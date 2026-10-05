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
