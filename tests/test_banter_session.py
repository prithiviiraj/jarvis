import unittest,threading
from unittest.mock import Mock,patch
from jarvis.workspace_voice import WorkspaceVoice
class BanterTests(unittest.TestCase):
 def make(self):
  r=Mock();r.ask.return_value={'text':'Actual supplied reply'};c=WorkspaceVoice(Mock(),Mock(return_value=r));return c,r
 def test_default_off(self):
  c,r=self.make();self.assertFalse(c.banter_active);r.ask.assert_not_called();self.assertIsNone(c.runtime)
 def test_consent_limits(self):
  for kwargs in [{'consent':False},{'consent':1},{'turn_limit':1},{'turn_limit':13},{'turn_limit':True},{'interval':1},{'interval':31},{'interval':True}]:
   c,r=self.make();opts={'consent':True,**kwargs}
   with self.assertRaises(ValueError):c.start_banter('topic',('NOVA','JARVIS'),**opts)
   r.ask.assert_not_called()
 def test_scope(self):
  for topic,names in [('',('NOVA','JARVIS')),('x'*1001,('NOVA','JARVIS')),('x',('NOVA','NOVA')),('x',('NOVA','unknown'))]:
   c,r=self.make()
   with self.assertRaises(ValueError):c.start_banter(topic,names,True)
 def test_context_sequence_and_bound(self):
  c,r=self.make();c.memory.append('DEX','question','prior context')
  with patch('jarvis.workspace_voice.banter_wait',return_value=False):c.start_banter('invited banter',('NOVA','JARVIS','KAI'),True,5,2).join(2)
  self.assertEqual(r.ask.call_count,5);self.assertEqual([x[0] for x in c.memory.snapshot()][-5:],['NOVA','JARVIS','KAI','NOVA','JARVIS'])
  self.assertTrue(any('[NOVA] Actual supplied reply'==m['content'] for m in r.ask.call_args_list[1].args[0]));self.assertTrue(all(x.kwargs['cloud_consent'] is False for x in r.ask.call_args_list));c.factory.assert_not_called();self.assertFalse(c.banter_active)
 def test_failure_atomic(self):
  c,r=self.make();c.memory.append('DEX','old','kept');r.ask.side_effect=[{'text':'one'},RuntimeError()]
  with patch('jarvis.workspace_voice.banter_wait',return_value=False):c.start_banter('x',('NOVA','JARVIS'),True,2,2).join(2)
  self.assertEqual(c.memory.snapshot(),[('DEX','old','kept')])
 def test_stop_switch_pause_close(self):
  for action in ['stop_banter','select','pause','close']:
   c,r=self.make();entered=threading.Event();release=threading.Event()
   def reply(*a,**kw):entered.set();release.wait(1);return {'text':'late'}
   r.ask.side_effect=reply;w=c.start_banter('x',('NOVA','JARVIS'),True,2,2);entered.wait(1)
   if action=='select':c.select('DEX')
   else:getattr(c,action)()
   release.set();w.join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertEqual(r.ask.call_count,1);self.assertFalse(c.banter_active)
 def test_stop_during_interval(self):
  c,r=self.make();w=c.start_banter('x',('NOVA','JARVIS'),True,3,30)
  for _ in range(100):
   if r.ask.called:break
   threading.Event().wait(.005)
  c.stop_banter();w.join(1);self.assertFalse(w.is_alive());self.assertEqual(r.ask.call_count,1);self.assertEqual(c.memory.snapshot(),[])
 def test_invalid_reply(self):
  for text in ['',None,'x'*1001]:
   c,r=self.make();r.ask.return_value={'text':text};c.start_banter('x',('NOVA','JARVIS'),True,2,2).join(1);self.assertEqual(c.memory.snapshot(),[])
 def test_busy_voice_closed(self):
  for attr,value in [('busy',True),('runtime',Mock()),('closed',True)]:
   c,r=self.make();setattr(c,attr,value)
   with self.assertRaises(RuntimeError):c.start_banter('x',('NOVA','JARVIS'),True)
 def test_time_limit(self):
  c,r=self.make()
  with patch('time.monotonic',side_effect=[0,121]):c.start_banter('x',('NOVA','JARVIS'),True).join(1)
  r.ask.assert_not_called();self.assertEqual(c.memory.snapshot(),[])
 def test_twelve_turns_context_bound(self):
  c,r=self.make();r.ask.return_value={'text':'a'*1000}
  with patch('jarvis.workspace_voice.banter_wait',return_value=False):c.start_banter('x'*1000,('JARVIS','NOVA','KAI','LYRA','DEX'),True,12,2).join(2)
  self.assertEqual(r.ask.call_count,12);self.assertEqual(len(c.memory.snapshot()),6)
  # Supplied prior context is bounded before each request, plus system/current instruction.
  for call in r.ask.call_args_list:self.assertLessEqual(sum(len(m['content']) for m in call.args[0][1:-1]),12000)
 def test_no_restart_while_request_inflight(self):
  c,r=self.make();entered=threading.Event();release=threading.Event()
  def answer(*args,**kw):entered.set();release.wait(1);return {'text':'late'}
  r.ask.side_effect=answer;w=c.start_banter('x',('NOVA','JARVIS'),True,2,2);self.assertTrue(entered.wait(1));c.stop_banter()
  with self.assertRaises(RuntimeError):c.start_banter('x',('NOVA','JARVIS'),True,2,2)
  release.set();w.join(2);self.assertFalse(c.busy);self.assertEqual(c.memory.snapshot(),[])
 def test_default_short_session(self):
  c,r=self.make()
  with patch('jarvis.workspace_voice.banter_wait',return_value=False):c.start_banter('short',('NOVA','JARVIS'),True).join(2)
  self.assertEqual(r.ask.call_count,2);self.assertIn('at most20words',r.ask.call_args.args[0][-1]['content'])
