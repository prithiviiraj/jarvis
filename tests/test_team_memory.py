import unittest
from jarvis.team_memory import TeamMemory
from jarvis.orbs import radius
class TeamTests(unittest.TestCase):
 def test_shared_identity(self):
  m=TeamMemory();m.append('JARVIS','what happened','I made a mistake');m.append('NOVA','help','I heard JARVIS');self.assertEqual(m.messages()[1]['content'],'[JARVIS] I made a mistake');self.assertEqual(len(m.messages()),4)
 def test_bounds_clear(self):
  m=TeamMemory(max_turns=2,max_chars=20)
  for _ in range(10):m.append('NOVA','a'*10,'b'*10)
  self.assertEqual(len(m.turns),1);m.clear();self.assertEqual(m.messages(),[])
 def test_unknown(self):
  with self.assertRaises(ValueError):TeamMemory().append('unknown','a','b')
 def test_speaking_orb_only(self):
  self.assertGreater(radius('NOVA','NOVA','speaking',0),21);self.assertEqual(radius('JARVIS','NOVA','speaking',0),21);self.assertEqual(radius('NOVA','NOVA','thinking',0),21)
 def test_reduced_motion(self):self.assertEqual(radius('NOVA','NOVA','speaking',0,True),radius('NOVA','NOVA','speaking',1,True))
