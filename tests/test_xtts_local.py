import unittest,io,wave
from unittest.mock import Mock
from jarvis.experimental.xtts_local import XTTSLocal
class LocalXTTS(unittest.TestCase):
 def test_scope_and_pcm(self):
  with self.assertRaises(ValueError):XTTSLocal()
  with self.assertRaises(ValueError):XTTSLocal(language='ta',noncommercial=True)
  s=XTTSLocal(noncommercial=True)
  buf=io.BytesIO()
  with wave.open(buf,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\x01\x00'*100)
  response=Mock();response.read.return_value=buf.getvalue();s.http=Mock();s.http.open.return_value.__enter__=Mock(return_value=response);s.http.open.return_value.__exit__=Mock(return_value=False)
  audio,sr=s.synthesize('Hello');self.assertEqual(sr,24000);self.assertEqual(len(audio),100);self.assertTrue(s.http.open.call_args.args[0].startswith('http://127.0.0.1:5002/api/tts?'))
  with self.assertRaises(ValueError):s.synthesize('வணக்கம்')
