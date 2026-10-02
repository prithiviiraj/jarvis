import unittest,sys,types
from unittest.mock import Mock,patch
from jarvis.speech import WhisperSTT
class HintTests(unittest.TestCase):
 def test_initial_prompt_passed_local(self):
  model=Mock();model.transcribe.return_value=([types.SimpleNamespace(text='NOVA',no_speech_prob=.1,avg_logprob=-.1)],None)
  with patch.dict(sys.modules,{'faster_whisper':types.SimpleNamespace(WhisperModel=Mock(return_value=model))}):stt=WhisperSTT('local',vocabulary='JARVIS NOVA KAI LYRA DEX',language='en')
  self.assertEqual(stt.transcribe([0]),'NOVA');self.assertEqual(model.transcribe.call_args.kwargs['initial_prompt'],'JARVIS NOVA KAI LYRA DEX');self.assertFalse(model.transcribe.call_args.kwargs['vad_filter'])
