import unittest
from jarvis.proactive import decision
class ProactiveSafety(unittest.TestCase):
 def test_model_decision_boundaries(self):
  self.assertEqual(decision('{"speak":false,"text":"never speak stale text"}'),{'speak':False,'text':''})
  with self.assertRaises(ValueError):decision('{"speak":true,"text":"'+('long '*36)+'"}')
  with self.assertRaises(ValueError):decision('{"speak":true,"text":"Hello","send":"private"}')
