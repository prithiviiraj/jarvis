import unittest
from jarvis.team_memory import TeamMemory
from jarvis.orbs import radius,face_pose
class TeamTests(unittest.TestCase):
 def test_shared_identity(self):
  m=TeamMemory();m.append('JARVIS','what happened','I made a mistake');m.append('DEX','help','I heard JARVIS');self.assertEqual(m.messages()[1]['content'],'[JARVIS] I made a mistake');self.assertEqual(len(m.messages()),4)
 def test_bounds_clear(self):
  m=TeamMemory(max_turns=2,max_chars=20)
  for _ in range(10):m.append('DEX','a'*10,'b'*10)
  self.assertEqual(len(m.turns),1);m.clear();self.assertEqual(m.messages(),[])
 def test_unknown(self):
  with self.assertRaises(ValueError):TeamMemory().append('unknown','a','b')
 def test_speaking_orb_only(self):
  self.assertGreater(radius('DEX','DEX','speaking',0),21);self.assertEqual(radius('JARVIS','DEX','speaking',0),21);self.assertEqual(radius('DEX','DEX','thinking',0),21)
 def test_reduced_motion(self):self.assertEqual(radius('DEX','DEX','speaking',0,True),radius('DEX','DEX','speaking',1,True))

 def test_faces_blink_and_speaking(self):
  self.assertLess(face_pose('DEX','DEX','off',3.86)['eye'],.11)
  self.assertGreater(face_pose('DEX','DEX','speaking',1)['mouth'],face_pose('JARVIS','DEX','speaking',1)['mouth'])
 def test_faces_reduced(self):
  self.assertEqual(face_pose('DEX','DEX','speaking',0,True),face_pose('DEX','DEX','speaking',1,True))
