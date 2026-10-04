import threading,unittest
from unittest.mock import Mock
from jarvis.speech_queue import SpeechQueue
class ReliabilityTests(unittest.TestCase):
 def test_audio_failure_not_swallowed_by_cancel(self):
  speaker=Mock();speaker.speak.side_effect=RuntimeError('output device unavailable');cancel=threading.Event()
  with self.assertRaisesRegex(RuntimeError,'Local voice failed'):SpeechQueue(speaker,cancel).play_stream(iter(['Hello. ','Again. ','Third. ']),0)
  self.assertTrue(cancel.is_set())
 def test_user_cancel_not_error(self):
  cancel=threading.Event();cancel.set();speaker=Mock();SpeechQueue(speaker,cancel).play_stream(iter(['Hello.']),0);speaker.speak.assert_not_called()

 def test_local_transient_allows_immediate_next_turn(self):
  from jarvis.router import BrainRouter,Provider,ProviderFailure,RouterError
  router=BrainRouter([Provider('local','http://127.0.0.1:1234/v1','test')]);t=Mock();t.stream.side_effect=[ProviderFailure('connection'),iter(['hello'])]
  with self.assertRaises(RouterError):list(router.stream([{}],stream_transport=t))
  self.assertEqual(list(router.stream([{}],stream_transport=t))[0]['text'],'hello')
 def test_model_failure_then_success_repeated_turn(self):
  from jarvis.runtime import VoiceRuntime
  from jarvis.router import RouterError
  events=[];v=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),lambda k,x:events.append((k,x)));v.mic=Mock();v.stt.transcribe.return_value='hello';v.streaming=True;v.enable(True)
  v.router.stream.side_effect=[RouterError('local:connection'),iter([{'text':'Hello.','provider':'local'}])]
  v.turn([0],v.generation,False,[]);self.assertTrue(any(k=='error'and'local model response'in x for k,x in events));self.assertTrue(v.enabled)
  v.turn([0],v.generation,False,[]);self.assertEqual(v.history[-1]['content'],'Hello.');self.assertEqual(v.mic.resume.call_count,2)
 def test_speech_failure_stops_safely_and_keeps_visible_text(self):
  from jarvis.runtime import VoiceRuntime
  events=[];v=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),lambda k,x:events.append((k,x)));v.mic=Mock();v.stt.transcribe.return_value='hello';v.streaming=True;v.enable(True)
  v.router.stream.return_value=iter([{'text':'Hello.','provider':'local'}]);v.speaker.speak.side_effect=RuntimeError('device failed');v.turn([0],v.generation,False,[])
  self.assertTrue(any(k=='answer'and x['text']=='Hello.'for k,x in events));self.assertTrue(any(k=='error'and'speech synthesis/playback'in x for k,x in events));self.assertFalse(v.enabled);self.assertEqual(v.history,[])
 def test_cloud_transient_keeps_circuit_breaker(self):
  from jarvis.router import BrainRouter,Provider,ProviderFailure,RouterError
  keys=Mock();keys.get.return_value='test';r=BrainRouter([Provider('cloud','https://example.test/v1','test',True)],key_store=keys);t=Mock();t.stream.side_effect=ProviderFailure('connection')
  for _ in range(2):
   with self.assertRaises(RouterError):list(r.stream([{}],cloud_consent=True,stream_transport=t))
  self.assertEqual(t.stream.call_count,1)
 def test_local_permanent_error_keeps_circuit_breaker(self):
  from jarvis.router import BrainRouter,Provider,ProviderFailure,RouterError
  r=BrainRouter([Provider('local','http://127.0.0.1:1234/v1','test')]);t=Mock();t.stream.side_effect=ProviderFailure('malformed',False)
  for _ in range(2):
   with self.assertRaises(RouterError):list(r.stream([{}],stream_transport=t))
  self.assertEqual(t.stream.call_count,1)
