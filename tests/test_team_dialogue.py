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
