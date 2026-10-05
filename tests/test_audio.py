import unittest
from jarvis.audio import Endpointer,ContinuousMic,AudioError
from unittest.mock import Mock
class AudioTests(unittest.TestCase):
 def test_silence_no_trigger(self):
  e=Endpointer();self.assertTrue(all(e.feed([0],.1) is None for i in range(100)))
 def test_speech_end(self):
  e=Endpointer(silence_frames=2,min_frames=2);self.assertEqual(e.feed([1],.9)[0],'start');e.feed([2],.9);e.feed([3],0);self.assertEqual(e.feed([4],0),('utterance',[[1],[2],[3],[4]]));self.assertFalse(e.active)
 def test_noise_spike_discarded(self):
  e=Endpointer(silence_frames=2,min_frames=2);e.feed([1],.9);e.feed([0],0);self.assertEqual(e.feed([0],0),('utterance',None))
 def test_hard_cap(self):
  e=Endpointer(min_frames=2,max_frames=3);e.feed([1],1);e.feed([1],1);self.assertEqual(e.feed([1],1)[0],'utterance')
 def test_consent_no_device(self):
  mic=ContinuousMic(Mock(),Mock())
  with self.assertRaises(AudioError):mic.start()
 def test_pause_discards(self):
  v=Mock();mic=ContinuousMic(v,Mock());mic.accepting=True;mic.frames.put((1,[1]));mic.close();self.assertFalse(mic.accepting);self.assertTrue(mic.frames.empty());v.reset.assert_called_once()
 def test_endpoint_presets_exact_silence_and_resume(self):
  from jarvis.audio import ENDPOINT_FRAMES
  self.assertEqual({k:v*32 for k,v in ENDPOINT_FRAMES.items()},{'balanced':800,'fast':480,'deliberate':1216})
  for n in ENDPOINT_FRAMES.values():
   e=Endpointer(silence_frames=n)
   for i in range(6):e.feed([1],1)
   for i in range(n-1):self.assertIsNone(e.feed([0],0))
   self.assertIsNone(e.feed([1],1))
   for i in range(n-1):self.assertIsNone(e.feed([0],0))
   self.assertEqual(e.feed([0],0)[0],'utterance')

class OnsetCallbackTests(unittest.TestCase):
 def test_onset_fires_on_speech_start_only_when_set(self):
  import threading,time
  from jarvis.audio import ContinuousMic
  vad=Mock();vad.score.return_value=.9
  onset=Mock();mic=ContinuousMic(vad,Mock());mic.on_onset=onset;mic.accepting=True
  thread=threading.Thread(target=mic.run,daemon=True);thread.start()
  mic.frames.put((mic.generation,[0.0]*512));time.sleep(.4)
  mic.stop_event.set();thread.join(timeout=2)
  onset.assert_called()
 def test_no_onset_without_hook(self):
  import threading,time
  from jarvis.audio import ContinuousMic
  vad=Mock();vad.score.return_value=.9
  mic=ContinuousMic(vad,Mock());mic.accepting=True
  thread=threading.Thread(target=mic.run,daemon=True);thread.start()
  mic.frames.put((mic.generation,[0.0]*512));time.sleep(.4)
  mic.stop_event.set();thread.join(timeout=2)

class SemanticEndpointTests(unittest.TestCase):
 def test_incomplete_waits_then_complete(self):
  from jarvis.audio import Endpointer
  calls=[]
  def complete(frames):calls.append(len(frames));return len(calls)>1
  e=Endpointer(silence_frames=2,min_frames=1,max_frames=100,turn_complete=complete);self.assertEqual(e.feed([0],1)[0],'start')
  self.assertIsNone(e.feed([0],0));self.assertIsNone(e.feed([0],0))
  for _ in range(14):self.assertIsNone(e.feed([0],0))
  self.assertEqual(e.feed([0],0)[0],'utterance');self.assertEqual(len(calls),2)
 def test_incomplete_bounded_hard_cap(self):
  from jarvis.audio import Endpointer
  e=Endpointer(silence_frames=2,min_frames=1,max_frames=20,turn_complete=lambda frames:False);e.feed([0],1)
  seen=[e.feed([0],0)for _ in range(19)];self.assertEqual(seen[-1][0],'utterance')
 def test_invalid_detector_fails_closed(self):
  from jarvis.audio import Endpointer
  def fail(f):raise ValueError('Invalid model')
  e=Endpointer(silence_frames=1,min_frames=1,turn_complete=fail);e.feed([0],1)
  with self.assertRaises(ValueError):e.feed([0],0)
 def test_smart_turn_features_no_heavy_dependency(self):
  import numpy as np
  from jarvis.experimental.turn_features import features
  out=features(np.zeros(16000,np.float32));self.assertEqual(out.shape,(1,80,800));self.assertTrue(np.isfinite(out).all());self.assertTrue(np.all(out==-1.5))
 def test_voiced_restart_resets_semantic_check(self):
  from jarvis.audio import Endpointer
  calls=[];e=Endpointer(silence_frames=2,min_frames=1,turn_complete=lambda f:calls.append(1)or False);e.feed([0],1);e.feed([0],0);e.feed([0],0);self.assertEqual(len(calls),1);e.feed([0],1);e.feed([0],0);e.feed([0],0);self.assertEqual(len(calls),2)
 def test_moonshine_no_tamil_or_implicit_download(self):
  from jarvis.experimental.moonshine_stt import MoonshineSTT,download
  with self.assertRaises(ValueError):MoonshineSTT('/nonexistent',language='ta')
  with self.assertRaises(ValueError):MoonshineSTT('/nonexistent')
  with self.assertRaises(ValueError):download('/nonexistent')

class SmartTurnBound(unittest.TestCase):
 def test_exact_extra_wait_ceiling(self):
  from jarvis.audio import Endpointer
  calls=[];e=Endpointer(turn_complete=lambda frames:(calls.append(len(frames))or False))
  for _ in range(7):e.feed([0],1)
  ended=None
  for i in range(1,100):
   ended=e.feed([0],0)
   if ended:break
  self.assertEqual(i,75);self.assertEqual(len(calls),4)
