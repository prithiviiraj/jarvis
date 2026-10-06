import unittest
from jarvis.workspace_voice import build_proactive_speaker
class SpeakerEngine(unittest.TestCase):
 def test_removed_optional_engines_rejected(self):
  for engine in ('kitten','pocket'):
   with self.assertRaises(ValueError):build_proactive_speaker(engine)
