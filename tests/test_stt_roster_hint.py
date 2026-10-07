import unittest,sys,types
from unittest.mock import Mock,patch
from jarvis.speech import WhisperSTT
class HintTests(unittest.TestCase):
 def test_initial_prompt_passed_local(self):
  model=Mock();model.transcribe.return_value=([types.SimpleNamespace(text='NOVA',no_speech_prob=.1,avg_logprob=-.1)],None)
  with patch.dict(sys.modules,{'faster_whisper':types.SimpleNamespace(WhisperModel=Mock(return_value=model))}):stt=WhisperSTT('local',vocabulary='JARVIS NOVA SILA LYRA DEX',language='en')
  self.assertEqual(stt.transcribe([0]),'NOVA');self.assertEqual(model.transcribe.call_args.kwargs['initial_prompt'],'JARVIS NOVA SILA LYRA DEX');self.assertFalse(model.transcribe.call_args.kwargs['vad_filter'])
import unittest,threading
from types import SimpleNamespace
from unittest.mock import Mock
from jarvis.speech import WhisperSTT,SpeechCancelled
class SttCancel(unittest.TestCase):
 def stt(self,segments):
  s=WhisperSTT.__new__(WhisperSTT);s.lock=threading.RLock();s.model=Mock();s.model.transcribe.return_value=(segments,None);s.language=None;s.vocabulary='';return s
 def test_pre_cancel_no_inference(self):
  cancel=threading.Event();cancel.set();s=self.stt([])
  with self.assertRaises(SpeechCancelled):s.transcribe_cancellable([],cancel)
  s.model.transcribe.assert_not_called()
 def test_cancel_after_segment_closes_without_more_consumption(self):
  cancel=threading.Event();events=[]
  def segments():
   try:
    events.append('first');cancel.set();yield SimpleNamespace(text='private',no_speech_prob=0,avg_logprob=0)
    events.append('second');yield SimpleNamespace(text='not consumed',no_speech_prob=0,avg_logprob=0)
   finally:events.append('closed')
  s=self.stt(segments())
  with self.assertRaises(SpeechCancelled):s.transcribe_cancellable([],cancel)
  self.assertEqual(events,['first','closed'])
 def test_normal_segments_and_close(self):
  events=[]
  def segments():
   try:yield SimpleNamespace(text='hello',no_speech_prob=0,avg_logprob=0)
   finally:events.append('closed')
  self.assertEqual(self.stt(segments()).transcribe([]),'hello');self.assertEqual(events,['closed'])
 def test_runtime_uses_cancel_token_and_never_routes_cancelled_text(self):
  from jarvis.runtime import VoiceRuntime
  class Adapter:
   def transcribe_cancellable(self,audio,cancel):cancel.set();raise SpeechCancelled()
  r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=False;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Adapter();r.speaker=Mock();r.speaker.generation=0;r.notify=Mock();r.router=Mock();r.mic=Mock();r.action_handler=Mock()
  r.turn([],1,False,[]);r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.action_handler.assert_not_called();self.assertFalse(r.busy)
