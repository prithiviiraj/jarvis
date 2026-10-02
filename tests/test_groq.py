import unittest
from unittest.mock import Mock
from jarvis.providers import configured
from jarvis.router import BrainRouter,RouterError
from jarvis.security import WindowsCredentials
class GroqTests(unittest.TestCase):
 def test_exact_endpoint(self):
  p=configured('groq','user-selected-model');self.assertEqual(p.url,'https://api.groq.com/openai/v1');self.assertTrue(p.requires_free_plan)
 def test_separate_key_namespace(self):
  self.assertNotEqual(WindowsCredentials.target('groq'),WindowsCredentials.target('grok'))
 def test_not_called_without_plan_verification(self):
  t=Mock();keys=Mock();r=BrainRouter([configured('groq','test')],t,keys)
  with self.assertRaises(RouterError):r.ask([{}],cloud_consent=True)
  t.complete.assert_not_called();keys.get.assert_not_called()
 def test_free_plan_allows_scoped_call(self):
  t=Mock();t.complete.return_value='synthetic';keys=Mock();keys.get.return_value='synthetic-test';r=BrainRouter([configured('groq','test')],t,keys)
  self.assertEqual(r.ask([{}],cloud_consent=True,verified_free_providers={'groq'})['provider'],'groq')
 def test_stream_same_gate(self):
  t=Mock();r=BrainRouter([configured('groq','test')],key_store=Mock())
  with self.assertRaises(RouterError):list(r.stream([{}],cloud_consent=True,stream_transport=t))
  t.stream.assert_not_called()
