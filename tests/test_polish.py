import unittest,tempfile,json,pathlib,time,threading
from unittest.mock import Mock,patch
from jarvis.obsidian_registry import register,uri
from jarvis.obsidian_vault import Vault,NAME
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.team_memory import TeamMemory
class Registry(unittest.TestCase):
 def fixture(self,d):
  root=pathlib.Path(d)/NAME;root.mkdir();(root/'.jarvis-vault.json').write_text('{}');p=pathlib.Path(d)/'obsidian.json';p.write_text(json.dumps({'update':True,'vaults':{'old':{'path':str(pathlib.Path(d)/'Other'),'open':True,'extra':'keep'}}}));return root,p
 def test_merge_backup_uri_reuse(self):
  with tempfile.TemporaryDirectory()as d:
   root,p=self.fixture(d);old=p.read_bytes();ident,new=register(root,p,lambda:False);self.assertTrue(new);j=json.loads(p.read_text());self.assertEqual(j['vaults']['old']['extra'],'keep');self.assertTrue(j['update']);self.assertEqual(next(p.parent.glob('*backup*')).read_bytes(),old);self.assertIn('vault='+ident,uri(root,'Brain of Brain.canvas',p));self.assertIn('file=Brain%20of%20Brain.canvas',uri(root,'Brain of Brain.canvas',p));self.assertEqual(register(root,p,lambda:True),(ident,False))
 def test_running_malformed_duplicate_no_write(self):
  with tempfile.TemporaryDirectory()as d:
   root,p=self.fixture(d);old=p.read_bytes()
   with self.assertRaisesRegex(RuntimeError,'Close Obsidian'):register(root,p,lambda:True)
   self.assertEqual(p.read_bytes(),old);p.write_text('bad')
   with self.assertRaises(ValueError):register(root,p,lambda:False)
   self.assertEqual(p.read_text(),'bad');p.write_text(json.dumps({'vaults':{'a':{'path':str(root)},'b':{'path':str(root)}}}))
   with self.assertRaisesRegex(ValueError,'Multiple'):register(root,p,lambda:False)
 def test_starting_mid_registration_no_write(self):
  with tempfile.TemporaryDirectory()as d:
   root,p=self.fixture(d);old=p.read_bytes();calls=iter([False,True])
   with self.assertRaisesRegex(RuntimeError,'started'):register(root,p,lambda:next(calls))
   self.assertEqual(p.read_bytes(),old)
class Context(unittest.TestCase):
 def test_unmatched_middle_and_last_keep_context(self):
  m=TeamMemory();m.restore([{'name':'You','text':'open data centre'},{'name':'You','text':'hear me?'}]);self.assertIn('open data centre',str(m.messages()));self.assertEqual(m.messages()[-1]['content'],'hear me?');self.assertEqual(m.messages()[0],{'role':'user','content':'open data centre'});self.assertEqual(m.snapshot(),[])
 def test_failed_action_followup_all_agents(self):
  for name in ('JARVIS','NOVA','KAI','LYRA','DEX'):
   seen=[]
   class Router:
    def stream(self,m,**kw):seen.extend(m);yield {'text':'I can hear you. Your earlier data centre request is not completed.','provider':'fixture','cloud':False}
   v=WorkspaceVoice(text_factory=Router);b=Bridge(v);b.evolution.generate=Mock()
   try:
    b.execute({'command':'chat','text':'JARVIS open the data center.'});self.assertTrue(any(m['name']=='KAI'and'not connected'in m['text']for m in b.messages));b.execute({'command':'select','name':name});b.execute({'command':'chat','text':name+', can you hear me?'})
    for _ in range(100):
     b.execute({'command':'status'})
     if not v.busy:break
     time.sleep(.001)
    self.assertIn('open the data center',str(seen),name);self.assertIn('not connected',str(seen),name)
   finally:b.close()
 def test_empty_error_timeout_and_cancel(self):
  b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
  try:
   b.voice.notify('answer',{'text':''});b.execute({'command':'status'});self.assertTrue(any(m['name']=='KAI'and'empty'in m['text']for m in b.messages));b.reply_wait={'started':time.monotonic()-95,'chat':b.chat_id};b.execute({'command':'status'});self.assertTrue(any('90 seconds'in m['text']for m in b.messages));n=len(b.messages);b.execute({'command':'status'});self.assertEqual(len(b.messages),n);b.reply_wait={'started':0,'chat':b.chat_id};b.execute({'command':'pause'});self.assertIsNone(b.reply_wait)
  finally:b.close()
 def test_data_open_success_not_invent_visibility(self):
  b=Bridge(WorkspaceVoice());b.obsidian.enabled=True;b.obsidian.open=Mock(side_effect=lambda *a:setattr(b.obsidian,'status','Open requested; visibility not verified'))
  try:b.execute({'command':'chat','text':'JARVIS open the data centre.'});b.obsidian.open.assert_called_once_with('Brain of Brain.canvas');self.assertTrue(any('visibility not verified'in m['text']for m in b.messages))
  finally:b.close()
class Async(unittest.TestCase):
 def test_async_connect_progress_default_sync_and_no_forced_close(self):
  with tempfile.TemporaryDirectory()as d:
   v=Vault(pathlib.Path(d)/'cfg.json',lambda:pathlib.Path(d));entered=threading.Event();release=threading.Event()
   def reg(*a):entered.set();release.wait(2);raise RuntimeError('Close Obsidian then retry')
   with patch('jarvis.obsidian_registry.register',reg):
    worker=v.start('connect',reviewed=NAME,confirm=True);entered.wait(1);self.assertTrue(v.snapshot()['busy']);self.assertEqual(v.phase,'Checking Obsidian vault registration');self.assertTrue(v.enabled);release.set();worker.join(2);self.assertFalse(v.busy);self.assertIn('Close Obsidian',v.error)
 def test_titles_preserve_path_and_owner_edit_and_redact(self):
  with tempfile.TemporaryDirectory()as d:
   v=Vault(pathlib.Path(d)/'cfg.json',lambda:pathlib.Path(d));v.create(NAME,True);v.sync([{'name':'You','text':'sk-'+'a'*30}],{'agents':[]},{},'abc123',True);p=pathlib.Path(d)/NAME/'Conversations/abc123.md';self.assertIn('title:',p.read_text());self.assertNotIn('sk-'+'a'*30,p.read_text());p.write_text('owner note');v.sync([],{'agents':[]},{},'abc123',True);self.assertEqual(p.read_text(),'owner note')
class MoreGates(unittest.TestCase):
 def test_snapshot_does_not_wait_for_writer_lock(self):
  with tempfile.TemporaryDirectory()as d:
   v=Vault(pathlib.Path(d)/'c',lambda:pathlib.Path(d));entered=threading.Event();release=threading.Event()
   def hold():
    with v.lock:entered.set();release.wait(2)
   worker=threading.Thread(target=hold);worker.start();entered.wait(1);t=time.monotonic();v.snapshot();self.assertLess(time.monotonic()-t,.1);release.set();worker.join()
 def test_legacy_canvas_only_exact_upgrade(self):
  from jarvis.vault_canvas_legacy import canvas as old
  from jarvis.vault_canvas import canvas as new
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'c',lambda:base);v.create(NAME,True);p=base/NAME/'Brain of Brain.canvas';p.write_text(old());v.create(NAME,True);self.assertEqual(p.read_text(),new());p.write_text('owner custom canvas');v.create(NAME,True);self.assertEqual(p.read_text(),'owner custom canvas')
 def test_registry_change_race_no_write(self):
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d)/NAME;root.mkdir();(root/'.jarvis-vault.json').write_text('{}');p=pathlib.Path(d)/'obsidian.json';p.write_text('{}');n=0
   def proc():
    nonlocal n
    n+=1
    if n==2:p.write_text('{"owner":"changed"}')
    return False
   with self.assertRaisesRegex(RuntimeError,'changed'):register(root,p,proc)
   self.assertEqual(p.read_text(),'{"owner":"changed"}')
class Regression(unittest.TestCase):
 def test_empty_error_clear_is_not_a_failure(self):
  b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
  try:b.voice.notify('error','');b.execute({'command':'status'});self.assertFalse(any(m['name']=='KAI'for m in b.messages))
  finally:b.close()
 def test_voice_action_handled_does_not_timeout(self):
  b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
  try:b.voice.notify('transcript','open data centre');b.voice.notify('action-handled','open data centre');b.execute({'command':'status'});self.assertIsNone(b.reply_wait)
  finally:b.close()
 def test_export_worker_progress_and_owner_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   b=Bridge(WorkspaceVoice());b.obsidian=Vault(pathlib.Path(d)/'c',lambda:pathlib.Path(d));b.obsidian.create(NAME,True)
   row=b.evolution.prepare(json.dumps({'summary':'Fixture','module':'extension_fixture.py','source':'x=1','tests':'assert True','risks':'not run'}),'Fixture');p=pathlib.Path(d)/NAME/'Proposals'/str(row['sha256']+'.md');p.parent.mkdir();p.write_text('Owner edit')
   try:
    b.execute({'command':'evolution-export','reviewed':row,'confirm':True})
    for _ in range(100):
     if not b.export_busy:break
     time.sleep(.001)
    self.assertEqual(p.read_text(),'Owner edit');self.assertTrue(any(m['name']=='KAI'and'no overwrite'in m['text']for m in b.messages))
   finally:b.close()
class PresenceLayer(unittest.TestCase):
 def test_time_real_ist_12hour_no_model(self):
  import re
  b=Bridge(WorkspaceVoice());b.voice.send_text=Mock()
  try:
   for text in ["Jarvis what's the time?",'NOVA tell me the time','time now']:
    s=b.execute({'command':'chat','text':text});answer=s['messages'][-1];self.assertEqual(answer['provider'],'system-clock');self.assertRegex(answer['text'],r'Master, it is (?:[1-9]|1[0-2]):[0-5][0-9] (?:AM|PM) IST.');b.voice.send_text.assert_not_called()
  finally:b.close()
 def test_camera_review_and_off_no_false_identity(self):
  b=Bridge(WorkspaceVoice());b.camera.start=Mock();b.setup.ready=True
  try:
   with self.assertRaises(ValueError):b.execute({'command':'awareness-mode','enabled':True})
   b.camera.start.assert_not_called();b.execute({'command':'awareness-mode','enabled':True,'consent':True,'audio':True});b.camera.start.assert_called_once_with(True);self.assertTrue(b.judge.night_session);self.assertTrue(b.context.apps);self.assertIn('not identity/sleep',b.status);b.execute({'command':'awareness-mode','enabled':False});self.assertFalse(b.context.apps);self.assertFalse(b.judge.enabled)
  finally:b.close()
 def test_explicit_night_configured_presence(self):
  b=Bridge(WorkspaceVoice());b.setup.ready=True
  try:
   b.execute({'command':'presence-mode','enabled':True,'consent':True,'audio':True});self.assertTrue(b.idle.configured);self.assertTrue(b.idle.night_session);self.assertTrue(b.idle.audio);b.execute({'command':'presence-mode','enabled':False});self.assertFalse(b.idle.enabled)
  finally:b.close()
 def test_image_route_local_even_configured_cloud(self):
  from jarvis.brain_settings import BrainSettings
  keys=Mock();keys.status.return_value={'present':True};b=BrainSettings(keys);b.configure([{'id':'slot1','provider':'groq','model':'cloud','enabled':True,'consent':True,'free':True}],{});seen=[]
  class Fake:
   def __init__(me,providers,**kw):seen.append(providers[0]);me.last_diagnostics=[];me.last_warnings=[]
   def stream(me,*a,**kw):yield {'text':'fixture','cloud':False}
  with patch('jarvis.brain_settings.local_models',return_value=['local-vision']),patch('jarvis.brain_settings.BrainRouter',Fake):
   b.router('LYRA').ask([{'role':'user','content':[{'type':'text','text':'see this'},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,AA'}}]}],configured_chat=True)
  self.assertEqual(len(seen),1);self.assertFalse(seen[0].cloud);keys.get.assert_not_called()
class PresenceCadence(unittest.TestCase):
 def test_configured_night_short_turn_capped(self):
  from types import SimpleNamespace as N
  from jarvis.idle_companion import IdleCompanion
  now=[0];voice=N(busy=False,runtime=None,memory=N(messages=lambda:[{'role':'user','content':'actual chat'}]),dialogue=Mock());router=Mock();router.ask.return_value={'text':'{"speak":true,"profiles":["NOVA","LYRA"],"topic":"A friendly hello"}'};brains=N(router=lambda name:router);i=IdleCompanion(voice,brains,Mock(),clock=lambda:now[0],hour=lambda:2);i.enable(True,True,True,True,True);now[0]=21;i.poll().join(1);self.assertFalse(router.ask.call_args.kwargs['local_only']);self.assertTrue(router.ask.call_args.kwargs['configured_chat']);self.assertEqual(voice.dialogue.call_args.kwargs['rounds'],1);self.assertNotIn('camera',str(router.ask.call_args.args));now[0]=60;self.assertIsNone(i.poll());i.requests.extend([60]*12);now[0]=90;self.assertIsNone(i.poll());i.stop()
class WakeRobustness(unittest.TestCase):
 def test_ambiguous_prefix_not_legitimate_reference(self):
  from jarvis.wake_address import ambiguous
  names=['JARVIS','NOVA','KAI','LYRA','DEX']
  self.assertTrue(ambiguous('Kai jarvis can you hear me',names));self.assertTrue(ambiguous('Hey Kai Jarvis open browser',names))
  for text in ['Hey Jarvis can you hear me','Kai and Jarvis talk together','Jarvis tell Kai hello','Jarvis Jarvis hello']:self.assertFalse(ambiguous(text,names),text)
 def test_runtime_ambiguous_keeps_raw_no_route_no_action(self):
  from jarvis.runtime import VoiceRuntime
  stt=Mock();stt.transcribe.return_value='Kai jarvis';router=Mock();speaker=Mock();speaker.generation=1;events=[];v=VoiceRuntime(Mock(),stt,router,speaker,lambda *a:events.append(a));v.mic=Mock();v.action_handler=Mock();v.enable(True)
  try:v.turn([0],v.generation,False,[]);router.ask.assert_not_called();router.stream.assert_not_called();v.action_handler.assert_not_called();self.assertIn(('transcript','Kai jarvis'),events);self.assertTrue(any(k=='error'and'two adjacent'in s for k,s in events))
  finally:v.close()
class MultiAddress(unittest.TestCase):
 def test_explicit_order_not_mishear_or_mention(self):
  from jarvis.multi_address import addressed
  self.assertEqual(addressed('Jarvis, Lyra.'),('JARVIS','LYRA'));self.assertEqual(addressed('Lyra and Jarvis please answer'),('LYRA','JARVIS'))
  for t in ['Kai Jarvis','Jarvis tell Lyra hello','What did Jarvis and Lyra say?']:self.assertEqual(addressed(t),())
 def test_text_both_actual_replies_no_extra_summary(self):
  seen=[]
  class Settings:
   def stop_warmup(me):pass
   local_gate=threading.Lock()
   def snapshot(me):return {'slots':[],'assignments':{},'busy':[],'checks':{}}
   def router(me,name):
    class R:
     def ask(me,m,**kw):seen.append((name,m));return {'text':'Yes, master.'if name=='JARVIS'else'Master, I am here.','cloud':False}
    return R()
  v=WorkspaceVoice();b=Bridge(v,brains=Settings());v.send_text=Mock()
  try:
   b.execute({'command':'chat','text':'Jarvis, Lyra.'})
   for _ in range(200):
    if not v.busy:break
    time.sleep(.001)
   state=b.execute({'command':'status'});self.assertEqual([n for n,m in seen],['JARVIS','LYRA']);self.assertIn('[JARVIS] Yes, master.',str(seen[1][1]));self.assertEqual([m['name']for m in state['messages']if m['name']!='You'],['JARVIS','LYRA']);v.send_text.assert_not_called()
  finally:b.close()
 def test_streaming_speech_before_rest_of_tokens(self):
  from jarvis.speech_queue import SpeechQueue
  spoke=threading.Event();events=[]
  class Speaker:
   def speak(me,text,generation=None):events.append(text);spoke.set()
   def stop(me):pass
  def stream():
   yield 'First sentence. '
   self.assertTrue(spoke.wait(1),'First clause was held until stream completed');yield 'Second sentence.'
  SpeechQueue(Speaker(),threading.Event()).play_stream(stream(),1);self.assertEqual(events,['First sentence.','Second sentence.'])
class MultiVoice(unittest.TestCase):
 def test_voice_two_list_order_and_prior_actual_reply(self):
  from jarvis.runtime import VoiceRuntime
  stt=Mock();stt.transcribe.return_value='Jarvis, Lyra';router=Mock();router.ask.side_effect=[{'text':'Yes, master.'},{'text':'Master, I am here.'}];speaker=Mock();speaker.generation=1;events=[];v=VoiceRuntime(Mock(),stt,router,speaker,lambda *a:events.append(a));v.mic=Mock();v.enable(True)
  try:v.turn([0],v.generation,False,[]);self.assertEqual([x['profile']for k,x in events if k=='answer'],['JARVIS','LYRA']);self.assertEqual(router.ask.call_count,2);self.assertIn('[JARVIS] Yes, master.',str(router.ask.call_args.args[0]));self.assertEqual(speaker.speak.call_count,2)
  finally:v.close()

class ContextProvenance(unittest.TestCase):
 def test_unanswered_middle_and_final_preserve_chronology(self):
  from jarvis.team_memory import TeamMemory
  m=TeamMemory();m.restore([{'name':'You','text':'unanswered one'},{'name':'You','text':'answered two'},{'name':'LYRA','text':'real reply'},{'name':'You','text':'unanswered three'}])
  self.assertEqual(m.messages(),[{'role':'user','content':'unanswered one'},{'role':'user','content':'answered two'},{'role':'assistant','content':'[LYRA] real reply'},{'role':'user','content':'unanswered three'}]);self.assertEqual(len(m.snapshot()),1)
 def test_trim_keeps_unmatched_order_and_no_fabricated_answer(self):
  from jarvis.team_memory import TeamMemory
  m=TeamMemory(max_turns=2);m.restore([{'name':'You','text':'old'},{'name':'KAI','text':'old answer'},{'name':'You','text':'miss'},{'name':'You','text':'recent'},{'name':'LYRA','text':'recent answer'},{'name':'You','text':'latest'},{'name':'DEX','text':'latest answer'}])
  self.assertEqual([x['content']for x in m.messages()],['recent','[LYRA] recent answer','latest','[DEX] latest answer']);self.assertFalse(any('No completed answer' in x['content']for x in m.messages()))
 def test_only_unanswered_bounded(self):
  from jarvis.team_memory import TeamMemory
  m=TeamMemory(max_turns=2,max_chars=100);m.restore([{'name':'You','text':str(i)*90}for i in range(8)]);self.assertLessEqual(sum(len(x['content'])for x in m.messages()),100);self.assertTrue(all(x['role']=='user'for x in m.messages()));self.assertIn('7',m.messages()[-1]['content'])

class RegistryFinalWindow(unittest.TestCase):
 def test_owner_change_after_temp_write_is_preserved(self):
  from jarvis.obsidian_registry import register
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d)/NAME;root.mkdir();(root/'.jarvis-vault.json').write_text('{}');p=pathlib.Path(d)/'obsidian.json';p.write_text('{}');calls=[0]
   def process():
    calls[0]+=1
    if calls[0]==3:p.write_text('{"owner":"final change"}')
    return False
   with self.assertRaisesRegex(RuntimeError,'changed'):register(root,p,process)
   self.assertEqual(p.read_text(),'{"owner":"final change"}');self.assertEqual(list(p.parent.glob('*.tmp')),[])

class ShutdownAudit(unittest.TestCase):
 def test_disable_during_registration_prevents_open(self):
  with tempfile.TemporaryDirectory()as d:
   v=Vault(pathlib.Path(d)/'c',lambda:pathlib.Path(d));entered=threading.Event();release=threading.Event();v.open=Mock()
   def registration(*a):entered.set();release.wait(2)
   with patch('jarvis.obsidian_registry.register',registration):
    worker=v.start('connect',reviewed=NAME,confirm=True);self.assertTrue(entered.wait(1));v.disable();release.set();worker.join(2);v.open.assert_not_called();self.assertFalse(v.enabled);self.assertFalse(v.busy);v.close()
 def test_close_marks_proposal_export_cancelled(self):
  b=Bridge(WorkspaceVoice());b.close();self.assertTrue(b.export_cancel.is_set())
