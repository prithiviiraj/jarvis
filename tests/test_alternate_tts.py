import unittest,tempfile,pathlib
from unittest.mock import Mock
from jarvis.experimental.alternate_tts import KittenSynth,XTTSSynth
class AlternateTTS(unittest.TestCase):
 def test_kitten_guard(self):
  m=Mock();m.generate.return_value=[0.,.1];s=KittenSynth(m);self.assertEqual(s.synthesize('Hello')[1],24000)
  with self.assertRaises(ValueError):s.synthesize('வணக்கம்')
  m.generate.assert_called_once_with('Hello',voice='Jasper',speed=1.)
 def test_xtts_license_and_tamil(self):
  m=Mock()
  with self.assertRaises(ValueError):XTTSSynth(m,'missing.wav')
  with self.assertRaises(ValueError):XTTSSynth(m,'missing.wav',noncommercial=True)
  with self.assertRaises(ValueError):XTTSSynth(m,'missing.wav',language='ta',noncommercial=True,voice_rights=True)
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'voice.wav';p.write_bytes(b'fixture')
   s=XTTSSynth(m,p,noncommercial=True,voice_rights=True);s.synthesize('Hello')
   with self.assertRaises(ValueError):s.synthesize('வணக்கம்')
   m.tts.assert_called_once()
