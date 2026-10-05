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

 def test_close_hook_once_and_callbacks_released(self):
  hook=Mock();self.v.close_hook=hook;self.v.shared_context=Mock();self.v.record_turn=Mock()
  self.v.close();self.v.close();hook.assert_called_once();self.assertIsNone(self.v.shared_context);self.assertIsNone(self.v.record_turn)

 def test_unclear_speech_repeat_and_no_stale_model_diagnostics(self):
  from jarvis.speech import UnclearSpeech
  events=[];self.v.notify=lambda *a:events.append(a);self.v.stt.transcribe.side_effect=UnclearSpeech('Speech was unclear. Please repeat.')
  self.v.router.last_diagnostics=[{'response_category':'final_text'}];self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertIn(('response-diagnostics',[]),events);self.assertFalse(any(e[0]=='response-diagnostics' and e[1] for e in events));self.assertTrue(any(e[0]=='error' and 'Nothing was sent to a model' in e[1] for e in events));self.v.router.ask.assert_not_called();self.v.mic.resume.assert_called_once()

 def test_output_metric_successful_adapter_write_not_audible(self):
  events=[];self.v.notify=lambda *a:events.append(a);self.v.enable(True)
  def speak(text,generation=None):self.v.speaker.output_event('first-write',generation,24000)
  self.v.speaker.speak.side_effect=speak;self.v.turn([0],self.v.generation,False,[])
  metric=[v for k,v in events if k=='metrics'and v][-1]
  self.assertLessEqual(metric['stt_s'],metric['first_text_s']);self.assertLessEqual(metric['first_text_s'],metric['first_output_write_s']);self.assertLessEqual(metric['first_output_write_s'],metric['turn_s']);self.assertIn('not sound heard',metric['scope'])
  self.assertIsNone(self.v.turn_metrics)
 def test_cancelled_output_does_not_report(self):
  events=[];self.v.notify=lambda *a:events.append(a);self.v.enable(True)
  def speak(text,generation=None):self.v.pause();self.v.speaker.output_event('first-write',generation,24000)
  self.v.speaker.speak.side_effect=speak;self.v.turn([0],self.v.generation,False,[])
  self.assertFalse(any(k=='metrics'and v for k,v in events));self.assertIsNone(self.v.turn_metrics)
 def test_no_output_adapter_does_not_invent_measurement(self):
  events=[];self.v.notify=lambda *a:events.append(a);self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  metric=[v for k,v in events if k=='metrics'and v][-1];self.assertNotIn('first_output_write_s',metric)
