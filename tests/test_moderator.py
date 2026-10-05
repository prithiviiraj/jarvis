import unittest
from jarvis.moderator import pick
class ModeratorTests(unittest.TestCase):
 def test_roles(self):
  for text,name in [('debug this Python function','DEX'),('draft a poem','LYRA'),('my meeting agenda','NOVA'),('compare these sources','KAI'),('how are you','JARVIS')]:self.assertEqual(pick(text)[0],name)
 def test_direct_address(self):
  self.assertEqual(pick('Hey NOVA, debug this code')[0],'NOVA');self.assertEqual(pick('DEX explain scheduling')[0],'DEX')
 def test_names_in_content_not_address(self):self.assertEqual(pick('What did NOVA say?')[0],'JARVIS')
 def test_ambiguity_one_leader(self):self.assertEqual(pick('write code for my calendar')[0],'JARVIS')
 def test_words_not_substrings(self):self.assertEqual(pick('the decode artifact')[0],'JARVIS')
 def test_reo_action_specialist(self):
  self.assertEqual(pick('Reo, open the browser')[0],'REO');self.assertEqual(pick('I want to talk with reo')[0],'REO');self.assertEqual(pick('open this website and click the download link')[0],'REO')
 def test_reo_keyword_conflicts_fall_to_leader(self):self.assertEqual(pick('debug this browser automation code')[0],'JARVIS')
 def test_scope(self):
  for text in ['',None]:
   with self.assertRaises(ValueError):pick(text)
  with self.assertRaises(ValueError):pick('x','UNKNOWN')
