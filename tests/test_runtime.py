import unittest
from unittest.mock import Mock
from jarvis.runtime import VoiceRuntime
class RuntimeTests(unittest.TestCase):
 def setUp(self):
  self.v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());self.v.mic=Mock();self.v.stt.transcribe.return_value='Hi';self.v.router.ask.return_value={'text':'Hello'}
 def test_consent(self):
  with self.assertRaises(ValueError):self.v.enable()
  self.v.mic.start.assert_not_called()
 def test_turn(self):
  self.v.enable(True);self.v.turn([0],self.v.generation,False,[]);self.v.speaker.speak.assert_called_once_with('Hello',generation=self.v.speaker.generation);self.v.mic.resume.assert_called_once()
 def test_stale_reply_not_spoken(self):
  self.v.enable(True);g=self.v.generation;self.v.router.ask.side_effect=lambda *a,**k:(self.v.pause() or {'text':'stale'});self.v.turn([0],g,False,[]);self.v.speaker.speak.assert_not_called();self.v.mic.resume.assert_not_called()
 def test_start_failure_disabled(self):
  self.v.mic.start.side_effect=RuntimeError('mic')
  with self.assertRaises(RuntimeError):self.v.enable(True)
  self.assertFalse(self.v.enabled)
 def test_provider_failure_resume(self):
  self.v.enable(True);self.v.router.ask.side_effect=RuntimeError('api');self.v.turn([0],self.v.generation,False,[]);self.v.mic.resume.assert_called_once();self.v.speaker.speak.assert_not_called()
