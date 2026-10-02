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
 def test_busy_restart_refused(self):
  self.v.busy=True
  with self.assertRaises(RuntimeError):self.v.enable(True)
 def test_stream_clauses(self):
  self.v.enable(True);self.v.streaming=True;self.v.router.stream.return_value=iter([{'text':'Hello. ','provider':'local'},{'text':'Next sentence.','provider':'local'}]);self.v.turn([0],self.v.generation,False,[]);self.assertEqual(self.v.speaker.speak.call_count,2);self.assertEqual(self.v.history[-1]['content'],'Hello. Next sentence.')
 def test_stream_cancel_no_history(self):
  self.v.enable(True);self.v.streaming=True
  def chunks(*a,**k):
   self.v.pause();yield {'text':'stale','provider':'local'}
  self.v.router.stream.side_effect=chunks;self.v.turn([0],self.v.generation,False,[]);self.assertEqual(self.v.history,[]);self.v.speaker.speak.assert_not_called()

 def test_shared_context_and_completed_turn_record(self):
  self.v.shared_context=lambda:[{'role':'assistant','content':'[JARVIS] earlier'}];self.v.record_turn=Mock();self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertIn({'role':'assistant','content':'[JARVIS] earlier'},self.v.router.ask.call_args.args[0]);self.v.record_turn.assert_called_once_with('Hi','Hello')
