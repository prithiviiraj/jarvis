import unittest,tempfile,pathlib,json
from jarvis.voice_preferences import VoicePreferences
class Prefs(unittest.TestCase):
 def test_engine_only_persists(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t)/'voice.json';v=VoicePreferences(p);self.assertEqual(v.load(),'kokoro');v.save('kokoro');self.assertEqual(VoicePreferences(p).load(),'kokoro');self.assertEqual(json.loads(p.read_text()),{'engine':'kokoro'})
   p.write_text('{"engine":"kitten","consent":true}');self.assertEqual(v.load(),'kokoro')
   with self.assertRaises(ValueError):v.save('xtts')
