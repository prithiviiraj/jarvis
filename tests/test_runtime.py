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
 def test_spoken_address_punctuation_selects_lyra_not_previous_dex(self):
  self.v.persona='DEX';self.v.stt.transcribe.return_value='Hey, Lyra. Can you hear me?';self.v.enable(True);self.v.turn([0],self.v.generation,False,[]);self.assertEqual(self.v.persona,'LYRA');self.v.speaker.select_profile.assert_called_once_with('LYRA');self.v.router.select_persona.assert_called_once_with('LYRA')
 def test_discuss_among_yourselves_six_actual_replies_and_leader_report(self):
  self.v.stt.transcribe.return_value='Discuss among yourselves how to help me study';self.v.router.ask.side_effect=[{'text':'reply'+str(i)}for i in range(4)];self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertEqual(self.v.router.ask.call_count,4);self.assertEqual([c.args[0]for c in self.v.speaker.select_profile.call_args_list],['JARVIS','LYRA','DEX','JARVIS']);self.assertEqual(self.v.speaker.speak.call_count,4);self.assertEqual(self.v.persona,'JARVIS');self.assertIn('[LYRA] reply1',str(self.v.router.ask.call_args_list[-1]))
 def test_discussion_stop_drops_late_reply(self):
  self.v.stt.transcribe.return_value='Talk among yourselves';self.v.router.ask.side_effect=lambda *a,**kw:(self.v.pause()or{'text':'late'});self.v.enable(True);self.v.turn([0],self.v.generation,False,[]);self.v.speaker.speak.assert_not_called();self.assertEqual(self.v.router.ask.call_count,1)

 def test_banter_is_bounded_and_leader_settles_before_apologies(self):
  self.v.stt.transcribe.return_value='Talk among yourselves and bicker playfully';self.v.router.ask.side_effect=[{'text':'reply'+str(i)}for i in range(7)];self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertEqual(self.v.router.ask.call_count,7);self.assertEqual([c.args[0]for c in self.v.speaker.select_profile.call_args_list],['JARVIS','LYRA','DEX','JARVIS','LYRA','DEX','JARVIS']);self.assertIn('Stop all!',str(self.v.router.ask.call_args_list[3]));self.assertIn('short apology',str(self.v.router.ask.call_args_list[4]));self.assertIn('final one-line',str(self.v.router.ask.call_args_list[-1]))

class ArgumentDynamicsTests(unittest.TestCase):
 def test_current_argument_roles(self):
  from jarvis.team_discussion import messages
  from jarvis.personas import prompt,ROLES
  self.assertEqual(tuple(ROLES),('JARVIS','LYRA','DEX'))
  self.assertIn('ends the debate',messages('DEX','argument about plans',[],2)[-1]['content'])
  self.assertIn('fear debating you',prompt('DEX'))
  self.assertIn('Master is watching',prompt('JARVIS'))
  self.assertIn('affectionate',prompt('LYRA'))
 def test_profanity_bound_never_at_master(self):
  from jarvis.personas import prompt
  for name in ('JARVIS','LYRA','DEX'):
   self.assertIn('never direct insults or profanity at master',prompt(name))

class BargeInTests(unittest.TestCase):
 def setUp(self):
  self.v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());self.v.mic=Mock();self.v.stt.transcribe.return_value='Hi';self.v.router.ask.return_value={'text':'Hello'}
 def test_default_no_onset_hook(self):
  self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertIsNone(self.v.mic.on_onset);self.v.mic.resume.assert_called_once()
 def test_barge_in_resumes_mic_during_reply_and_clears_hook(self):
  self.v.barge_in=True;self.v.enable(True);self.v.turn([0],self.v.generation,False,[])
  self.assertEqual(self.v.mic.resume.call_count,2);self.assertIsNone(self.v.mic.on_onset)
 def test_interrupt_cancels_output_swaps_event_and_next_turn_works(self):
  self.v.barge_in=True;self.v.enable(True)
  old_cancel=self.v.cancel
  def speaking(text,generation=None):self.v.interrupt(self.v.generation)
  self.v.speaker.speak.side_effect=speaking
  self.v.turn([0],self.v.generation,False,[])
  self.assertTrue(old_cancel.is_set());self.assertFalse(self.v.cancel.is_set());self.assertIsNot(self.v.cancel,old_cancel)
  self.v.speaker.speak.side_effect=None;self.v.speaker.speak.reset_mock()
  self.v.turn([0],self.v.generation,False,[]);self.v.speaker.speak.assert_called_once()
 def test_stale_interrupt_ignored(self):
  self.v.enable(True);self.v.interrupt(self.v.generation+5);self.v.speaker.stop.assert_not_called()
 def test_interrupted_turn_records_nothing(self):
  self.v.barge_in=True;self.v.record_turn=Mock();self.v.enable(True)
  def speaking(text,generation=None):self.v.interrupt(self.v.generation)
  self.v.speaker.speak.side_effect=speaking
  self.v.turn([0],self.v.generation,False,[])
  self.v.record_turn.assert_not_called();self.assertEqual(self.v.history,[])

class VoiceTeamStreaming(unittest.TestCase):
 def test_exact_voice_phrase_streams_clause_before_turn_complete(self):
  import threading
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='talk to each other about this';v.streaming=True
  entered=threading.Event();release=threading.Event();calls=[];events=[];v.notify=lambda *a:events.append(a)
  def stream(messages,**kw):
   calls.append(messages);yield {'text':'First useful sentence.','provider':'fixture','model':'controlled'}
   if len(calls)==1:entered.set();release.wait(2)
   yield {'text':' Second thought.','provider':'fixture','model':'controlled'}
  v.router.stream.side_effect=stream;v.speaker.speak.side_effect=lambda *a,**kw:release.set()
  v.enable(True);thread=threading.Thread(target=v.turn,args=([0],v.generation,False,[]));thread.start();self.assertTrue(entered.wait(1));thread.join(3)
  self.assertFalse(thread.is_alive());self.assertEqual(len(calls),7);v.router.ask.assert_not_called()
  self.assertIn('[JARVIS] First useful sentence. Second thought.',str(calls[1]));self.assertTrue(any(k=='answer' and x.get('stream_id')for k,x in events));self.assertEqual(v.speaker.speak.call_args_list[0].args[0],'First useful sentence.');v.close()
 def test_exact_voice_phrase_pause_drops_late_stream_and_next_actor(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='talk to each other about this';v.streaming=True
  def stream(*a,**kw):v.pause();yield {'text':'late'}
  v.router.stream.side_effect=stream;v.enable(True);v.turn([0],v.generation,False,[])
  self.assertEqual(v.router.stream.call_count,1);v.speaker.speak.assert_not_called();self.assertEqual(v.history,[]);v.close()
