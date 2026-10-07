import unittest,threading,time
from unittest.mock import Mock
from jarvis.live_screen import LiveScreen
T={'id':123,'title':'Fixture window'}
class LiveScreenTests(unittest.TestCase):
 def wait(self,f):
  deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   if f():return
   time.sleep(.005)
  self.fail('condition timeout')
 def test_start_requires_exact_target_and_no_export(self):
  c=LiveScreen(Mock());m=Mock()
  with self.assertRaises(ValueError):c.enable(T,T,m)
  with self.assertRaises(ValueError):c.enable(T,T,m,True,True,True)
  m.verify.assert_not_called()
 def test_capture_continues_while_inference_pending_and_stop_discards(self):
  entered=threading.Event();gate=threading.Event();count=[0];notes=[]
  def source(t):count[0]+=1;return str(count[0]).encode()
  def analyze(f):entered.set();gate.wait(2);return {'observed':'fixture','comment':'A change','confidence':'high'}
  m=Mock();m.analyze=analyze;c=LiveScreen(lambda *x:notes.append(x),source=source,interval=.01);c.enable(T,T,m,True,True)
  self.assertTrue(entered.wait(1));self.wait(lambda:count[0]>5);self.assertEqual(c.metrics['inflight_limit']if 'inflight_limit'in c.metrics else 1,1);c.stop();gate.set();self.wait(lambda:all(not t.is_alive()for t in c.workers));self.assertEqual(notes,[]);self.assertIsNone(c.preview);self.assertIsNone(c.latest)
 def test_unchanged_scene_no_repeat_and_audio_flag(self):
  notes=[];m=Mock();m.analyze.return_value={'observed':'fixture','comment':'Visible scene','confidence':'high'};c=LiveScreen(lambda *x:notes.append(x),source=lambda t:b'jpeg',interval=.01);c.enable(T,T,m,True,True);self.wait(lambda:len(notes)==1);time.sleep(.08);c.stop();self.assertEqual(m.analyze.call_count,1);self.assertTrue(notes[0][1]['audio'])
 def test_focus_loss_clears_frame(self):
  state=[b'jpeg'];m=Mock();m.analyze.return_value={'observed':'','comment':'','confidence':'low'};c=LiveScreen(Mock(),source=lambda t:state[0],interval=.01);c.enable(T,T,m,True);self.wait(lambda:c.preview is not None);state[0]=None;self.wait(lambda:c.preview is None);c.stop()
 def test_bad_frame_stops_before_model(self):
  m=Mock();c=LiveScreen(Mock(),source=lambda t:b'x'*200001,interval=.01);c.enable(T,T,m,True);self.wait(lambda:not c.enabled);m.analyze.assert_not_called()
 def test_restart_blocked_while_old_analysis_runs(self):
  gate=threading.Event();entered=threading.Event();m=Mock()
  def analyze(f):entered.set();gate.wait(2);return {'observed':'test','comment':'test','confidence':'high'}
  m.analyze=analyze;c=LiveScreen(Mock(),source=lambda t:b'jpeg',interval=.01);c.enable(T,T,m,True);self.assertTrue(entered.wait(1));c.stop()
  with self.assertRaises(ValueError):c.enable(T,T,m,True)
  gate.set();self.wait(lambda:all(not t.is_alive()for t in c.workers));c.enable(T,T,m,True);c.stop()
 def test_stale_result_not_emitted(self):
  notes=[];entered=threading.Event();gate=threading.Event();m=Mock()
  def analyze(f):entered.set();gate.wait(2);return {'observed':'old','comment':'old','confidence':'high'}
  m.analyze=analyze;c=LiveScreen(lambda *x:notes.append(x),source=lambda t:b'jpeg',interval=.01,max_age=.03);c.enable(T,T,m,True);self.assertTrue(entered.wait(1));time.sleep(.05);c.stop();gate.set();self.wait(lambda:all(not t.is_alive()for t in c.workers));self.assertEqual(notes,[])
 def test_invalid_scene_does_not_escape(self):
  notes=[];m=Mock();m.analyze.return_value={'observed':{},'comment':'test','confidence':'high'};c=LiveScreen(lambda *x:notes.append(x),source=lambda t:b'jpeg',interval=.01);c.enable(T,T,m,True);self.wait(lambda:not c.enabled);self.assertEqual(notes,[])
 def test_analysis_pauses_for_conversation_but_capture_continues(self):
  m=Mock();m.analyze.return_value={'observed':'','comment':'','confidence':'low'};c=LiveScreen(Mock(),source=lambda t:b'jpeg',interval=.01);c.poll(True);c.enable(T,T,m,True);c.poll(True);self.wait(lambda:c.sequence>5);calls=m.analyze.call_count;time.sleep(.04);self.assertEqual(m.analyze.call_count,calls);c.poll(False);c.stop()
 def test_focus_loss_regain_drops_previous_reply(self):
  notes=[];entered=threading.Event();gate=threading.Event();state=[b'jpeg'];m=Mock()
  def analyze(f):entered.set();gate.wait(2);return {'observed':'before focus loss','comment':'old scene','confidence':'high'}
  m.analyze=analyze;c=LiveScreen(lambda *x:notes.append(x),source=lambda t:state[0],interval=.01);c.enable(T,T,m,True);self.assertTrue(entered.wait(1));state[0]=None;self.wait(lambda:c.preview is None);state[0]=b'jpeg';self.wait(lambda:c.preview is not None);c.poll(True);gate.set();self.wait(lambda:not c.busy);c.stop();self.assertEqual(notes,[])
 def test_terminal_runtime_error_stops_not_retries(self):
  m=Mock();m.analyze.side_effect=RuntimeError('local model unavailable');c=LiveScreen(Mock(),source=lambda t:b'jpeg',interval=.01);c.enable(T,T,m,True);self.wait(lambda:not c.enabled);self.assertEqual(m.analyze.call_count,1)
