import unittest,threading
from unittest.mock import Mock
from jarvis.runtime import VoiceRuntime
class BrowserVoiceRuntime(unittest.TestCase):
 def test_explicit_browser_proposal_bypasses_language_model_and_speech(self):
  # Real VoiceRuntime turn path with hardware/model adapters as fixtures.
  r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value='Jarvis browser open example.com';r.speaker=Mock();r.speaker.generation=0;r.notify=Mock();r.action_handler=Mock(return_value=True);r.mic=Mock();r.router=Mock()
  r.turn([],1,False,[])
  r.action_handler.assert_called_once_with('Jarvis browser open example.com');r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.speaker.speak.assert_not_called();r.mic.resume.assert_called_once();self.assertFalse(r.busy)
