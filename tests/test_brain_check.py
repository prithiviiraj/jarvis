import unittest
from unittest.mock import Mock
from jarvis.brain_check import check_groq
class ConnectionCheckTests(unittest.TestCase):
 def test_no_consent_no_key_access(self):
  keys=Mock()
  with self.assertRaises(ValueError):check_groq('model',key_store=keys)
  keys.get.assert_not_called()
 def test_no_free_plan_no_key_access(self):
  keys=Mock()
  with self.assertRaises(ValueError):check_groq('model',True,False,keys)
  keys.get.assert_not_called()
 def test_no_model(self):
  with self.assertRaises(ValueError):check_groq('',True,True,Mock())
 def test_no_key(self):
  keys=Mock();keys.get.return_value=None
  with self.assertRaises(ValueError):check_groq('model',True,True,keys)
 def test_synthetic_result_labeled(self):
  keys=Mock();keys.get.return_value='synthetic-key';router=Mock();router.stream.return_value=iter([{'text':'Hello.','provider':'groq'}]);factory=Mock(return_value=router)
  r=check_groq('test-model',True,True,keys,factory);self.assertEqual(r['reply'],'Hello.');self.assertIn('not voice',r['scope']);self.assertEqual(factory.call_args.args[0][0].url,'https://api.groq.com/openai/v1');self.assertEqual(router.stream.call_args.kwargs['verified_free_providers'],('groq',))
