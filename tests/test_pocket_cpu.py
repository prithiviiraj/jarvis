import tempfile,pathlib,unittest
from unittest.mock import patch,Mock
from jarvis import pocket_assets
from jarvis.experimental.pocket_cpu import PocketProfile,PRESETS
class Pocket(unittest.TestCase):
 def test_download_review_and_hashes(self):
  with tempfile.TemporaryDirectory()as d:
   self.assertFalse(pocket_assets.ready(d))
   with self.assertRaises(Exception):pocket_assets.download(d)
   self.assertEqual(len(pocket_assets.FILES),7)
   for url,sha,cap in pocket_assets.FILES.values():self.assertIn('/resolve/',url);self.assertEqual(len(sha),64);self.assertGreater(cap,1)
 def test_preset_map_and_short_text(self):
  self.assertEqual(PRESETS['LYRA'],'alba');self.assertEqual(PRESETS['NOVA'],'anna');e=Mock();s=PocketProfile(e,'LYRA')
  for text in ('',None,'x'*501):
   with self.assertRaises(ValueError):s.synthesize(text)
  e.model.generate_audio.assert_not_called()
 def test_preference_and_review(self):
  from jarvis.voice_preferences import VoicePreferences
  with tempfile.TemporaryDirectory()as d:
   v=VoicePreferences(pathlib.Path(d)/'p.json')
   with self.assertRaises(ValueError):v.save('pocket')
   self.assertEqual(v.load(),'kokoro')
 def test_setup_requires_review(self):
  from jarvis.voice_setup import VoiceSetup
  s=VoiceSetup()
  with self.assertRaises(ValueError):s.select('pocket')
  with self.assertRaises(Exception):s.start(engine='pocket')
 def test_team_cleanup_has_no_kokoro_specific_g2p(self):
  from jarvis.workspace_voice import WorkspaceVoice
  import inspect
  for method in (WorkspaceVoice.dialogue,WorkspaceVoice.parallel_round):self.assertNotIn('speaker.synth.g2p.close',inspect.getsource(method))
