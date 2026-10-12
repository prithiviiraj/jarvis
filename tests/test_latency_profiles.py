import unittest
from unittest.mock import Mock
from jarvis.latency_profiles import DiagnosticProfile
class Tests(unittest.TestCase):
 def test_only_context_changes_no_shipping_default(self):
  original=['llama-server.exe','--ctx-size','8192','--api-key','fixture','--host','127.0.0.1','--mmproj','fixture.gguf'];spawn=Mock();profile=DiagnosticProfile(4096,spawn);profile(original,cwd='fixture');new=spawn.call_args.args[0]
  self.assertEqual(original[2],'8192');self.assertEqual(new,original[:2]+['4096']+original[3:]);self.assertEqual(spawn.call_args.kwargs,{'cwd':'fixture'})
 def test_unknown_profile_rejected(self):
  with self.assertRaises(ValueError):DiagnosticProfile(2048)
 def test_missing_contract_does_not_spawn(self):
  spawn=Mock()
  with self.assertRaises(ValueError):DiagnosticProfile(4096,spawn)(['fixture'])
  spawn.assert_not_called()
