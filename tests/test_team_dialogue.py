import unittest,threading
from unittest.mock import Mock
from jarvis.team_discussion import requested,order,clean_reply
from jarvis.workspace_voice import WorkspaceVoice
class Dialogue(unittest.TestCase):
 def test_explicit_pair(self):
  t='Lyra, can you and Dex talk to each other about how humans form and tell me an answer?'
  self.assertTrue(requested(t));self.assertEqual(order(t),('LYRA','DEX','LYRA','DEX','JARVIS'));self.assertFalse(requested('Lyra what is time now?'))
 def test_reject_narrated_multi_person(self):
  with self.assertRaises(ValueError):clean_reply('My reply. [DEX] Fake reply')
  with self.assertRaises(ValueError):clean_reply('Hi.\nDex: Fake reply')
  self.assertEqual(clean_reply('[LYRA] My reply.'),'My reply.')
 def test_real_routes_and_prior_actual_messages(self):
  v=WorkspaceVoice();calls=[]
  class Router:
   def __init__(self,name):self.name=name
   def ask(self,messages,**kw):calls.append((self.name,messages));return {'text':self.name+' actual reply.','backend':'fixture'}
  brains=Mock();brains.router.side_effect=lambda name:Router(name)
  v.dialogue('Lyra and Dex talk to each other about biology',brains).join(2)
  answers=[x[1]for x in list(v.events.queue)if x[0]=='answer'];self.assertEqual([x['profile']for x in answers],['LYRA','DEX','LYRA','DEX','JARVIS']);self.assertEqual([x[0]for x in calls],['LYRA','DEX','LYRA','DEX','JARVIS']);self.assertIn('[LYRA] LYRA actual reply.',str(calls[1][1]));self.assertIn('[DEX] DEX actual reply.',str(calls[2][1]));v.close()
 def test_cancel_no_later_reply(self):
  v=WorkspaceVoice();started=threading.Event();released=threading.Event();router=Mock()
  def ask(*a,**kw):started.set();released.wait(1);return {'text':'A reply.'}
  router.ask.side_effect=ask;brains=Mock();brains.router.return_value=router
  worker=v.dialogue('Lyra and Dex talk to each other',brains);started.wait(1);v.pause();released.set();worker.join(2);self.assertFalse(any(x[0]=='answer'for x in list(v.events.queue)));v.close()
 def test_natural_named_discussion_intents(self):
  for t in ('JARVIS, can you discuss with DEX about why humans have imagination?', 'Jarvis have a discussion with Dex about science', 'Lyra talk to Dex about coding'):
   self.assertTrue(requested(t),t)
  self.assertEqual(order('JARVIS, can you discuss with DEX about humans?'),('JARVIS','DEX','JARVIS','DEX','JARVIS'))
  for t in ("Jarvis don't discuss with Dex about this",'Stop the conversation with Dex','Do not talk to Dex about science','What does Dex do?','I talked with Dex yesterday','Talk to Dex','Lyra what is time now?'):
   self.assertFalse(requested(t),t)
 def test_live_laptop_speak_together_phrase(self):
  from jarvis.team_discussion import participants
  t='Can you speak with DEX together? Speak about why politics is important?'
  self.assertTrue(requested(t));self.assertEqual(order(t),('JARVIS','DEX','JARVIS','DEX','JARVIS'))
  self.assertEqual(participants(t,'LYRA'),('LYRA','DEX'))
  for no in ("Don't speak with DEX together",'Stop speaking with DEX together','Speak to Dex','Speak with Dex'):
   self.assertFalse(requested(no),no)
 def test_laptop_phrase_actual_rounds_and_context(self):
  v=WorkspaceVoice();calls=[]
  class Router:
   def __init__(self,name):self.name=name
   def ask(self,messages,**kw):calls.append((self.name,messages));return {'text':'Useful reply from '+self.name+'.','provider':'fixture','model':'controlled','cloud':True}
  brains=Mock();brains.router.side_effect=lambda name:Router(name)
  v.dialogue('Can you speak with DEX together? Speak about why politics is important?',brains).join(2)
  self.assertEqual([n for n,m in calls],['JARVIS','DEX','JARVIS','DEX','JARVIS'])
  self.assertIn('[JARVIS] Useful reply from JARVIS.',str(calls[1][1]));self.assertIn('[DEX] Useful reply from DEX.',str(calls[2][1]));v.close()
 def test_no_fabricated_user_turn_on_idle(self):
  v=WorkspaceVoice();brains=Mock();brains.router.return_value.ask.return_value={'text':'A short real reply.'}
  v.dialogue('Dex and Lyra talk to each other about hello',brains,rounds=1,origin='idle').join(2)
  self.assertFalse(any(k=='transcript'for k,x in list(v.events.queue)));self.assertEqual(sum(k=='answer'for k,x in list(v.events.queue)),3);v.close()

class StreamingDialogue(unittest.TestCase):
 def test_partial_arrives_before_generation_finishes(self):
  v=WorkspaceVoice();entered=threading.Event();release=threading.Event();calls=[]
  class Router:
   def stream(self,messages,**kw):
    calls.append(messages);yield {'text':'A useful ','provider':'fixture'};entered.set();release.wait(2);yield {'text':'reply.','provider':'fixture'}
  brains=Mock();brains.router.return_value=Router()
  w=v.dialogue('Dex and Lyra talk to each other about art',brains,rounds=1);self.assertTrue(entered.wait(1))
  a=[x[1]for x in list(v.events.queue)if x[0]=='answer'];self.assertEqual(a[0]['text'],'A useful ');self.assertTrue(w.is_alive())
  release.set();w.join(3);a=[x[1]for x in list(v.events.queue)if x[0]=='answer'];self.assertEqual(len(a),6);self.assertEqual(a[0]['stream_id'],a[1]['stream_id']);self.assertIn('[DEX] A useful reply.',str(calls[1]));v.close()
 def test_pause_stops_delta_and_next_profile(self):
  v=WorkspaceVoice();entered=threading.Event();release=threading.Event();calls=[]
  class Router:
   def stream(self,*a,**kw):
    calls.append(1);yield {'text':'First ','provider':'fixture'};entered.set();release.wait(2);yield {'text':'late.','provider':'fixture'}
  brains=Mock();brains.router.return_value=Router();w=v.dialogue('Dex and Lyra talk to each other',brains,rounds=1);entered.wait(1);v.pause();release.set();w.join(2)
  a=[x[1]for x in list(v.events.queue)if x[0]=='answer'];self.assertEqual(len(a),1);self.assertEqual(len(calls),1);self.assertEqual(v.memory.messages(),[]);v.close()
 def test_invented_teammate_stream_stops_without_replacement(self):
  v=WorkspaceVoice()
  class Router:
   def stream(self,*a,**kw):yield {'text':'[Lyra, secretly fixes things]','provider':'fixture'}
  brains=Mock();brains.router.return_value=Router();v.dialogue('Dex and Lyra talk to each other',brains,rounds=1).join(2)
  self.assertFalse(any(k=='answer'for k,x in list(v.events.queue)));self.assertTrue(any(k=='error'for k,x in list(v.events.queue)));v.close()
 def test_clause_audio_before_full_reply_and_stop(self):
  from unittest.mock import patch
  v=WorkspaceVoice();spoken=threading.Event();release=threading.Event();said=[]
  class Speaker:
   generation=0
   synth=Mock()
   def select_profile(self,name):self.profile=name
   def speak(self,text,generation=None):said.append((self.profile,text));spoken.set()
   def stop(self):self.generation+=1
  class Router:
   def stream(self,*a,**kw):
    yield {'text':'First useful sentence.','provider':'fixture'};release.wait(2);yield {'text':' Another sentence.','provider':'fixture'}
  brains=Mock();brains.router.return_value=Router()
  with patch('jarvis.workspace_voice.build_proactive_speaker',return_value=Speaker()):
   w=v.dialogue('Dex and Lyra talk to each other',brains,audio=True,rounds=1);self.assertTrue(spoken.wait(1));self.assertTrue(w.is_alive());v.pause();release.set();w.join(3)
  self.assertEqual(said,[('DEX','First useful sentence.')]);v.close()

class PrefetchedDialogue(unittest.TestCase):
 def test_next_real_request_during_previous_audio_no_overlap(self):
  from unittest.mock import patch
  v=WorkspaceVoice();audio_started=threading.Event();next_started=threading.Event();release=threading.Event();calls=[];said=[];active=0
  class Speaker:
   generation=0;synth=Mock()
   def select_profile(self,name):self.profile=name
   def speak(self,text,generation=None):
    nonlocal active
    active+=1
    if active!=1:raise RuntimeError('overlapping audio')
    said.append(self.profile)
    if len(said)==1:audio_started.set();release.wait(2)
    active-=1
   def stop(self):self.generation+=1
  class Router:
   def __init__(self,name):self.name=name
   def stream(self,messages,**kw):
    calls.append((self.name,messages))
    if len(calls)==2:next_started.set()
    yield {'text':'Useful reply.','provider':'fixture'}
  brains=Mock();brains.router.side_effect=lambda name:Router(name)
  with patch('jarvis.workspace_voice.build_proactive_speaker',return_value=Speaker()):
   w=v.dialogue('Dex and Lyra talk to each other about art',brains,audio=True,rounds=1)
   self.assertTrue(audio_started.wait(1));self.assertTrue(next_started.wait(1));self.assertEqual(said,['DEX']);self.assertIn('[DEX] Useful reply.',str(calls[1][1]));release.set();w.join(3)
  self.assertFalse(w.is_alive());self.assertEqual(said,['DEX','LYRA','JARVIS']);self.assertTrue(any(k=='dialogue-metrics'for k,x in list(v.events.queue)));v.close()
