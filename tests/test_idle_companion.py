import unittest,threading,json
from types import SimpleNamespace as N
from unittest.mock import Mock
from jarvis.idle_companion import IdleCompanion,decision
class Idle(unittest.TestCase):
 def make(self,text='{"speak":true,"profiles":["NOVA","LYRA"],"topic":"A friendly greeting"}'):
  self.now=0;v=N(busy=False,runtime=None,memory=N(messages=lambda:[{'role':'user','content':'Actual chat'}]),dialogue=Mock());r=N(ask=Mock(return_value={'text':text}));brains=N(router=lambda name:r);notes=[];i=IdleCompanion(v,brains,lambda *a:notes.append(a),clock=lambda:self.now,hour=lambda:9);return v,r,i,notes
 def test_off_review_and_rate(self):
  v,r,i,n=self.make();self.now=300;self.assertIsNone(i.poll());r.ask.assert_not_called()
  with self.assertRaises(ValueError):i.enable()
  i.enable(True);self.now=421;i.poll().join(2);v.dialogue.assert_called_once();self.assertEqual(v.dialogue.call_args.kwargs['origin'],'idle');self.assertIsNone(i.poll());self.now=1100;i.poll().join(2);self.assertEqual(v.dialogue.call_count,1)
 def test_quiet_busy_and_silence(self):
  v,r,i,n=self.make('{"speak":false,"profiles":[],"topic":""}');i.enable(True);self.now=300;i.hour=lambda:1;self.assertIsNone(i.poll());i.hour=lambda:9;v.runtime=object();self.assertIsNone(i.poll());v.runtime=None;v.busy=True;self.assertIsNone(i.poll());v.busy=False;i.poll().join(2);v.dialogue.assert_not_called()
 def test_activity_and_disable_cancel_late_decision(self):
  for action in ('activity','stop'):
   v,r,i,n=self.make();gate=threading.Event();entered=threading.Event()
   def ask(*a,**k):entered.set();gate.wait(2);return {'text':'{"speak":true,"profiles":["NOVA","LYRA"],"topic":"Hello"}'}
   r.ask=ask;i.enable(True,True);self.now=300;w=i.poll();entered.wait(1);getattr(i,action)();gate.set();w.join(2);v.dialogue.assert_not_called()
 def test_schema_no_actions(self):
  for text in ('{}','bad','{"speak":true,"profiles":["REO","NOVA"],"topic":"hey"}','{"speak":true,"profiles":["NOVA","LYRA"],"topic":"hey","tool":"open"}'):
   with self.assertRaises(ValueError):decision(text)
 def test_hourly_cap(self):
  v,r,i,n=self.make();i.enable(True);self.now=300;i.requests.extend([299]*6);self.assertIsNone(i.poll());r.ask.assert_not_called()

class GamingSuppression(unittest.TestCase):
 def test_gaming_stays_quiet(self):
  from unittest.mock import Mock
  from jarvis.idle_companion import IdleCompanion
  voice=Mock();voice.busy=False;voice.runtime=None;brains=Mock()
  c=IdleCompanion(voice,brains,Mock(),clock=lambda:1000,hour=lambda:12);c.enable(True);c.last_activity=0;c.gaming=True
  self.assertIsNone(c.poll());brains.router.assert_not_called();self.assertIn('gaming',c.waiting())

class StrongIdle(unittest.TestCase):
 def test_twenty_seconds_explicit_only_rotates_bounded_pair(self):
  from jarvis.idle_companion import IdleCompanion
  now=[0];voice=Mock();voice.busy=False;voice.runtime=None;voice.memory.messages.return_value=[];brains=Mock();brains.router.return_value.ask.side_effect=[{'text':'{"speak":true,"profiles":["NOVA","LYRA"],"topic":"A greeting"}'},{'text':'{"speak":true,"profiles":["NOVA","LYRA"],"topic":"A fresh idea"}'}]
  c=IdleCompanion(voice,brains,Mock(),clock=lambda:now[0],hour=lambda:12);c.enable(True,True,strong=True);now[0]=19;self.assertIsNone(c.poll());now[0]=21;c.poll().join(2)
  self.assertTrue(brains.router.return_value.ask.call_args.kwargs['local_only']);self.assertIn('NOVA and SILA',voice.dialogue.call_args.args[0]);self.assertEqual(voice.dialogue.call_args.kwargs['rounds'],2)
  now[0]=180;self.assertIsNone(c.poll());now[0]=202;c.poll().join(2);self.assertIn('LYRA and DEX',voice.dialogue.call_args.args[0]);c.stop();self.assertFalse(c.enabled)
 def test_typed_stop_never_goes_to_model(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  v=WorkspaceVoice();v.send_text=Mock();b=Bridge(voice=v)
  try:
   b.idle.enable(True,strong=True);b.execute({'command':'chat','text':'Jarvis, stop talking.'});self.assertFalse(b.idle.enabled);v.send_text.assert_not_called()
   self.assertFalse(b.stop_intent('How do I stop a loop?'))
  finally:b.close()
