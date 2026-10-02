import unittest,threading,time
from unittest.mock import Mock
from jarvis.audio import ContinuousMic,Endpointer
class MicWorkerTests(unittest.TestCase):
 def test_stale_frames_discarded_after_resume(self):
  vad=Mock();vad.score.return_value=1.0;mic=ContinuousMic(vad,Mock());mic.accepting=True;mic.generation=1
  mic.frames.put((0,[0]*512));mic.frames.put((1,[1]*512));t=threading.Thread(target=mic.run);t.start()
  deadline=time.monotonic()+1
  while vad.score.call_count<1 and time.monotonic()<deadline:time.sleep(.005)
  mic.close();t.join(2);self.assertEqual(vad.score.call_count,1)
 def test_endpoint_callback_suspends_processing(self):
  vad=Mock();vad.score.side_effect=[1.,1.,0.,0.];got=threading.Event();callback=Mock(side_effect=lambda audio:got.set());mic=ContinuousMic(vad,callback);mic.endpointer=Endpointer(silence_frames=2,min_frames=2);mic.accepting=True;mic.generation=1
  for i in range(4):mic.frames.put((1,[0.0]*512))
  t=threading.Thread(target=mic.run);t.start();self.assertTrue(got.wait(2));self.assertFalse(mic.accepting);mic.close();t.join(2);callback.assert_called_once()
 def test_vad_error_closes_state(self):
  vad=Mock();vad.score.side_effect=RuntimeError('private');notify=Mock();mic=ContinuousMic(vad,Mock(),notify);mic.accepting=True;mic.generation=1;mic.frames.put((1,[0]*512));t=threading.Thread(target=mic.run);t.start();t.join(2);self.assertTrue(mic.stop_event.is_set());self.assertFalse(mic.accepting);notify.assert_called_with('error','Voice detection failed. Listening stopped.')
