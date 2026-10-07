import unittest
from jarvis.laya_routes import evidence
class Evidence(unittest.TestCase):
 def test_rules_no_fake_confidence_or_coverage(self):
  r=evidence('Jarvis open the browser.');self.assertEqual(r['lane'],'browser');self.assertIsNone(r['confidence']);self.assertEqual(r['vault_coverage'],'unknown until retrieval');self.assertEqual(r['speech_complete'],'not assessed')
 def test_unknown_not_completion_probability(self):
  self.assertEqual(evidence(None)['state'],'unknown');self.assertEqual(evidence('explain this','spoken')['speech_complete'],'upstream endpoint, not probability')
