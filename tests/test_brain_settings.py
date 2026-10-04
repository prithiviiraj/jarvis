import unittest,tempfile,json,time,threading
from pathlib import Path
from unittest.mock import Mock,patch
from jarvis.brain_settings import BrainSettings
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.router import RouterError
class BrainTests(unittest.TestCase):
 def setUp(self):
  self.keys=Mock();self.keys.status.return_value={'present':True};self.b=BrainSettings(self.keys)
  self.rows=[{'id':'slot1','provider':'groq','model':'llama-3.1-8b-instant','enabled':True,'consent':True,'free':True},{'id':'slot2','provider':'gemini','model':'gemini-test','enabled':True,'consent':True,'free':True}]
 def test_no_creation_network(self):self.keys.get.assert_not_called()
 def test_secure_key_status_never_secret(self):
  self.b.configure(self.rows,{'DEX':'slot2'});self.b.set_key('slot1','groq','test-value');self.assertNotIn('test-value',json.dumps(self.b.snapshot()));self.keys.set.assert_called_once_with('groq/slot1','test-value')
 def test_persist_without_secrets_or_consent(self):
  with tempfile.TemporaryDirectory()as d:
   path=Path(d)/'routes.json';b=BrainSettings(self.keys,path);b.configure(self.rows,{'DEX':'slot2'});saved=path.read_text();self.assertNotIn('consent',saved);self.assertNotIn('free',saved);loaded=BrainSettings(self.keys,path);self.assertEqual(loaded.assignments['DEX'],'slot2');self.assertEqual(loaded.consent,set());self.assertEqual(loaded.free,set())
 def test_primary_cloud_first_local_last(self):
  self.b.configure(self.rows,{'DEX':'slot2'});self.assertEqual([s.provider for s in self.b.candidates('DEX')],['gemini','groq','local'])
 def test_unconfirmed_cloud_excluded(self):
  self.rows[0]['free']=False;self.rows[1]['consent']=False;self.b.configure(self.rows,{});self.assertEqual([s.provider for s in self.b.candidates('DEX')],['local'])
 def test_shared_rate_limit_cooldown(self):
  self.b.configure(self.rows,{'DEX':'slot1'});routers=[]
  class Fake:
   def __init__(me,ps,**kw):me.p=ps[0];me.last_diagnostics=[];me.last_warnings=[];routers.append(me.p.name)
   def stream(me,*a,**kw):
    if me.p.name=='slot1':raise RouterError('http-429')
    yield {'text':'yes','provider':me.p.name,'model':me.p.model}
  with patch('jarvis.brain_settings.BrainRouter',Fake):
   self.assertEqual(self.b.router('DEX').ask([{'role':'user','content':'hi'}])['text'],'yes');self.assertEqual(self.b.router('NOVA').ask([{'role':'user','content':'hi'}])['text'],'yes')
  self.assertEqual(routers,['slot1','slot2','slot2']);self.assertGreater(self.b.cooldowns['slot1'],time.monotonic())
 def test_partial_no_fallback(self):
  self.b.configure(self.rows,{})
  class Fake:
   def __init__(me,*a,**kw):me.last_diagnostics=[];me.last_warnings=[]
   def stream(me,*a,**kw):yield {'text':'part','provider':'slot1'};raise RouterError('mid stream')
  with patch('jarvis.brain_settings.BrainRouter',Fake):
   with self.assertRaises(RouterError):self.b.router('DEX').ask([{'role':'user','content':'hi'}])
 def test_parallel_round_real_concurrency_order_and_conclusion(self):
  v=WorkspaceVoice();barrier=threading.Barrier(5);seen=[];lock=threading.Lock()
  class Settings:
   def router(me,name):
    class R:
     def ask(me,messages,**kw):
      if 'conclusion' in messages[-1]['content']:
       self.assertEqual(len([m for m in messages if m['role']=='assistant']),5);return {'text':'Conclusion.'}
      barrier.wait(timeout=2)
      with lock:seen.append(name)
      return {'text':name+' perspective.'}
    return R()
  t=v.parallel_round('test topic',Settings());t.join(4);self.assertFalse(t.is_alive());self.assertEqual(len(seen),5);events=[]
  while not v.events.empty():events.append(v.events.get())
  answers=[value for kind,value in events if kind=='answer'];self.assertEqual([a['profile']for a in answers],['NOVA','KAI','LYRA','DEX','JARVIS','JARVIS']);self.assertEqual(answers[-1]['text'],'Conclusion.');v.close()
 def test_local_connection_check_async_current_failure(self):
  with patch('jarvis.brain_settings.local_models',return_value=['current-model']):
   t=self.b.check();t.join(1)
  self.assertEqual(self.b.snapshot()['checks']['local']['model'],'current-model')
  with patch('jarvis.brain_settings.local_models',side_effect=RouterError('server stopped')):
   t=self.b.check();t.join(1)
  self.assertEqual(self.b.snapshot()['checks']['local']['state'],'failed')
 def test_live_api_models_greeting_and_secret_not_in_status(self):
  import io
  from jarvis.router import HttpTransport
  self.b.configure(self.rows,{});self.keys.get.return_value='not-a-real-key'
  models=io.BytesIO(json.dumps({'data':[{'id':'llama-3.1-8b-instant'}]}).encode());http=Mock();http.open.return_value=models
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch.object(HttpTransport,'complete',return_value='Hello.'):
   t=self.b.check('slot1');t.join(1)
  self.assertEqual(self.b.checks['slot1']['state'],'ready');self.assertNotIn('not-a-real-key',json.dumps(self.b.snapshot()))
 def test_local_fallback_is_serialized_across_personas(self):
  active=0;maximum=0;lock=threading.Lock()
  class Fake:
   def __init__(me,*a,**kw):me.last_diagnostics=[];me.last_warnings=[]
   def stream(me,*a,**kw):
    nonlocal active,maximum
    with lock:active+=1;maximum=max(maximum,active)
    time.sleep(.04)
    yield {'text':'local answer','provider':'local'}
    with lock:active-=1
  with patch('jarvis.brain_settings.local_models',return_value=['qwen']),patch('jarvis.brain_settings.BrainRouter',Fake):
   threads=[threading.Thread(target=lambda n=n:self.b.router(n).ask([{'role':'user','content':'hi'}]))for n in ('DEX','NOVA','JARVIS')]
   for t in threads:t.start()
   for t in threads:t.join(1)
  self.assertEqual(maximum,1)
 def test_actual_bridge_new_commands_are_allowed(self):
  from jarvis.ui_bridge import Bridge
  v=WorkspaceVoice();b=Bridge(v,self.b)
  with patch.object(self.b,'check')as check:
   b.execute({'command':'brain-check','slot':'local'});check.assert_called_once()
  b.execute({'command':'key-save','slot':'slot1','kind':'groq','secret':'fixture-only'})
  self.keys.set.assert_called_once_with('groq/slot1','fixture-only')
  b.execute({'command':'brain-save','slots':self.rows,'assignments':{'DEX':'slot2'}})
  self.assertEqual(b.execute({'command':'status'})['brains']['assignments']['DEX'],'slot2')
  with patch.object(v,'parallel_round')as round_call:b.execute({'command':'team-round','text':'topic','audio':False});round_call.assert_called_once()
  b.execute({'command':'key-delete','slot':'slot1','kind':'groq'});self.keys.delete.assert_called_once_with('groq/slot1');b.close()
