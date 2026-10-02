import unittest
from unittest.mock import Mock
from jarvis.voice_loop import VoiceLoop,State
class LoopTests(unittest.TestCase):
 def setUp(self):
  self.rec=Mock();self.stt=Mock();self.brain=Mock();self.tts=Mock();self.stt.transcribe.return_value='Hello';self.brain.ask.return_value={'text':'Hi','provider':'local'}
  self.v=VoiceLoop(self.rec,self.stt,self.brain,self.tts)
 def test_off_default(self):self.assertEqual(self.v.state,State.OFF);self.assertFalse(self.v.speech_started())
 def test_consent_required(self):
  with self.assertRaises(ValueError):self.v.enable()
 def test_turn(self):
  self.v.enable(True);self.v.speech_started();self.assertTrue(self.v.speech_finished());self.assertEqual(self.v.state,State.SPEAKING);self.v.speech_playback_finished();self.assertEqual(self.v.state,State.LISTENING)
 def test_pause_releases(self):
  self.v.enable(True);self.v.speech_started();self.v.pause();self.rec.cancel.assert_called_once();self.tts.stop.assert_called_once();self.assertEqual(self.v.state,State.OFF)
 def test_stale_transcript_discarded(self):
  self.v.enable(True);self.v.speech_started();self.stt.transcribe.side_effect=lambda a:(self.v.pause() or 'private');self.assertFalse(self.v.speech_finished());self.brain.ask.assert_not_called()
 def test_error_recovers(self):
  self.v.enable(True);self.v.speech_started();self.stt.transcribe.side_effect=RuntimeError('private');self.assertFalse(self.v.speech_finished());self.assertEqual(self.v.state,State.LISTENING)
 def test_bargein_controller_only(self):
  self.v.enable(True);self.v.speech_started();self.v.speech_finished();self.assertTrue(self.v.speech_started());self.tts.stop.assert_called_once()
