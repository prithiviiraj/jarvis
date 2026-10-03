import unittest,types,sys
from unittest.mock import Mock,patch
from jarvis import speech
class EngineCacheTests(unittest.TestCase):
 def test_stt_shared_model_but_separate_persona_hints(self):
  constructor=Mock(return_value=Mock())
  with patch.dict(sys.modules,{'faster_whisper':types.SimpleNamespace(WhisperModel=constructor)}),patch.dict(speech._STT_MODELS,{},clear=True):
   a=speech.WhisperSTT('cache-fixture','JARVIS');b=speech.WhisperSTT('cache-fixture','NOVA')
   constructor.assert_called_once();self.assertIs(a.model,b.model);self.assertEqual(b.vocabulary,'NOVA')
