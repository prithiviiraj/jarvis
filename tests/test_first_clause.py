import unittest
from jarvis.streaming import sentences
class FirstClause(unittest.TestCase):
 def test_meaningful_comma_not_word_fragments(self):
  chunks=['I can help you with this task right now, ','and the next step is to check the details.']
  parts=list(sentences(chunks));self.assertTrue(parts[0].endswith(','));self.assertGreaterEqual(len(parts[0].split()),6)
  self.assertEqual(list(sentences(['Hello, ','world.'])),['Hello, world.'])
