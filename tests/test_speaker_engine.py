import unittest
from unittest.mock import Mock,patch
from pathlib import Path
from jarvis.workspace_voice import build_proactive_speaker,VOICES
class SpeakerEngine(unittest.TestCase):
 def test_output_only_kitten_profiles_all_five(self):
  g=Mock();synths=[]
  def synth(root,g2p,voice):
   s=Mock();s.g2p=g2p;s.voice=voice;synths.append(s);return s
  with patch('jarvis.paths.ensure_layout',return_value=Path('/tmp/models-fixture')),patch('jarvis.kitten_assets.ready',return_value=True),patch('jarvis.native_frontend.verified_frontend',return_value=('fixture-exe','fixture-data')),patch('jarvis.experimental.kokoro.NativeG2P',return_value=g),patch('jarvis.experimental.kitten_onnx.KittenONNX',side_effect=synth):
   speaker=build_proactive_speaker('kitten');self.assertEqual(set(speaker.profiles),set(VOICES));self.assertEqual(speaker.profile,'JARVIS');self.assertEqual(speaker.synth.voice,'Jasper');speaker.select_profile('NOVA');self.assertEqual(speaker.synth.voice,'Rosie');speaker.select_profile('LYRA');self.assertEqual(speaker.synth.voice,'Luna');speaker.close();g.close.assert_called_once()
