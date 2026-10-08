import unittest,threading,json
from types import SimpleNamespace as N
from unittest.mock import Mock
from jarvis.idle_companion import IdleCompanion,decision
class Idle(unittest.TestCase):
 def make(self,text='{"speak":true,"profiles":["DEX","LYRA"],"topic":"A friendly greeting"}'):
  self.now=0;v=N(busy=False,runtime=None,memory=N(messages=lambda:[{'role':'user','content':'Actual chat'}]),dialogue=Mock());r=N(ask=Mock(return_value={'text':text}));brains=N(router=lambda name:r);notes=[];i=IdleCompanion(v,brains,lambda *a:notes.append(a),clock=lambda:self.now,hour=lambda:9);return v,r,i,notes
 def test_off_review_and_rate(self):
  v,r,i,n=self.make();self.now=300;self.assertIsNone(i.poll());r.ask.assert_not_called()
  with self.assertRaises(ValueError):i.enable()
  i.enable(True,configured=True);self.now=601;i.poll().join(2);v.dialogue.assert_called_once();self.assertEqual(v.dialogue.call_args.kwargs['origin'],'idle');self.assertIsNone(i.poll());self.now=1100;i.poll().join(2);self.assertEqual(v.dialogue.call_count,1)
 def test_quiet_busy_and_silence(self):
  v,r,i,n=self.make('{"speak":false,"profiles":[],"topic":""}');i.enable(True,configured=True);self.now=300;i.hour=lambda:1;self.assertIsNone(i.poll());i.hour=lambda:9;v.runtime=object();self.assertIsNone(i.poll());v.runtime=None;v.busy=True;self.assertIsNone(i.poll());v.busy=False;i.poll().join(2);v.dialogue.assert_not_called()
 def test_activity_and_disable_cancel_late_decision(self):
  for action in ('activity','stop'):
   v,r,i,n=self.make();gate=threading.Event();entered=threading.Event()
   def ask(*a,**k):entered.set();gate.wait(2);return {'text':'{"speak":true,"profiles":["DEX","LYRA"],"topic":"Hello"}'}
   r.ask=ask;i.enable(True,True,configured=True);self.now=300;w=i.poll();entered.wait(1);getattr(i,action)();gate.set();w.join(2);v.dialogue.assert_not_called()
 def test_schema_no_actions(self):
  for text in ('{}','bad','{"speak":true,"profiles":["REO","DEX"],"topic":"hey"}','{"speak":true,"profiles":["DEX","LYRA"],"topic":"hey","tool":"open"}'):
   with self.assertRaises(ValueError):decision(text)
 def test_hourly_cap(self):
  v,r,i,n=self.make();i.enable(True,configured=True);self.now=300;i.requests.extend([299]*6);self.assertIsNone(i.poll());r.ask.assert_not_called()

class GamingSuppression(unittest.TestCase):
 def test_gaming_stays_quiet(self):
  from unittest.mock import Mock
  from jarvis.idle_companion import IdleCompanion
  voice=Mock();voice.busy=False;voice.runtime=None;brains=Mock()
  c=IdleCompanion(voice,brains,Mock(),clock=lambda:1000,hour=lambda:12);c.enable(True,configured=True);c.last_activity=0;c.gaming=True
  self.assertIsNone(c.poll());brains.router.assert_not_called();self.assertIn('gaming',c.waiting())

class StrongIdle(unittest.TestCase):
 def test_twenty_seconds_explicit_only_rotates_bounded_pair(self):
  from jarvis.idle_companion import IdleCompanion
  now=[0];voice=Mock();voice.busy=False;voice.runtime=None;voice.memory.messages.return_value=[];brains=Mock();brains.router.return_value.ask.side_effect=[{'text':'{"speak":true,"profiles":["DEX","LYRA"],"topic":"A greeting"}'},{'text':'{"speak":true,"profiles":["DEX","LYRA"],"topic":"A fresh idea"}'}]
  c=IdleCompanion(voice,brains,Mock(),clock=lambda:now[0],hour=lambda:12);c.enable(True,True,strong=True,configured=True);now[0]=19;self.assertIsNone(c.poll());now[0]=301;c.poll().join(2)
  self.assertFalse(brains.router.return_value.ask.call_args.kwargs['local_only']);self.assertTrue(brains.router.return_value.ask.call_args.kwargs['api_only']);self.assertIn('LYRA and DEX',voice.dialogue.call_args.args[0]);self.assertEqual(voice.dialogue.call_args.kwargs['rounds'],1)
  now[0]=302;self.assertIsNone(c.poll());now[0]=602;c.poll().join(2);self.assertIn('LYRA and DEX',voice.dialogue.call_args.args[0]);c.stop();self.assertFalse(c.enabled)
 def test_typed_stop_never_goes_to_model(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  v=WorkspaceVoice();v.send_text=Mock();b=Bridge(voice=v)
  try:
   b.idle.enable(True,strong=True);b.execute({'command':'chat','text':'Jarvis, stop talking.'});self.assertFalse(b.idle.enabled);v.send_text.assert_not_called()
   self.assertFalse(b.stop_intent('How do I stop a loop?'))
  finally:b.close()

class ApiOnlyIdle(unittest.TestCase):
 def test_unconfigured_never_calls_any_model(self):
  voice=Mock();voice.busy=False;voice.runtime=None;brains=Mock();now=[0]
  c=IdleCompanion(voice,brains,Mock(),clock=lambda:now[0],hour=lambda:12);c.enable(True);now[0]=1000
  self.assertIsNone(c.poll());brains.router.assert_not_called();self.assertIn('enable a proactive session',c.waiting())
 def test_random_gap_drawn_on_enable_and_decision(self):
  from unittest.mock import patch
  voice=Mock();voice.busy=False;voice.runtime=None;voice.memory.messages.return_value=[];brains=Mock();brains.router.return_value.ask.return_value={'text':'{"speak":false,"profiles":[],"topic":""}'};now=[0]
  with patch('jarvis.idle_companion.random.uniform',side_effect=[60,65,70]):
   c=IdleCompanion(voice,brains,Mock(),clock=lambda:now[0],hour=lambda:12);c.enable(True,strong=True,configured=True);self.assertEqual(c.next_gap,65);now[0]=64;self.assertIsNone(c.poll());now[0]=66;c.poll().join(2);self.assertEqual(c.next_gap,70)
  self.assertTrue(brains.router.return_value.ask.call_args.kwargs['api_only'])
class AdaptiveCadence(unittest.TestCase):
 def make(self):
  now=[0];v=N(busy=False,runtime=None,memory=N(messages=lambda:[]),dialogue=Mock());r=N(ask=Mock(return_value={'text':'{"speak":false,"profiles":[],"topic":""}'}));brains=N(router=lambda name:r,live_snapshot=Mock(return_value={'state':'loaded','models':[{'id':'fixture'}],'age_s':1}));c=IdleCompanion(v,brains,Mock(),clock=lambda:now[0],hour=lambda:12);c.enable(True,strong=True,night_session=True,configured=True);c.auto_route=True;c.sync_route();return now,v,r,brains,c
 def test_local_ten_seconds_no_cloud(self):
  now,v,r,b,c=self.make();self.assertEqual(c.route,'local');now[0]=9;self.assertIsNone(c.poll());now[0]=10;c.poll().join(1);self.assertTrue(r.ask.call_args.kwargs['local_only']);self.assertFalse(r.ask.call_args.kwargs['api_only']);now[0]=19;self.assertIsNone(c.poll());now[0]=20;c.poll().join(1);self.assertEqual(r.ask.call_count,2)
 def test_stale_or_off_local_uses_api_without_local_fallback(self):
  now,v,r,b,c=self.make();b.live_snapshot.return_value={'state':'loaded','models':[{'id':'fixture'}],'age_s':16};c.sync_route();self.assertEqual(c.route,'api');self.assertTrue(55<=c.next_gap<=75);now[0]=76;c.poll().join(1);self.assertFalse(r.ask.call_args.kwargs['local_only']);self.assertTrue(r.ask.call_args.kwargs['api_only'])
 def test_busy_suppresses_even_after_due(self):
  now,v,r,b,c=self.make();v.busy=True;now[0]=100;self.assertIsNone(c.poll());r.ask.assert_not_called()
