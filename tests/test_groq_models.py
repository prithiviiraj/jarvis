import unittest,json,urllib.error,ssl
from unittest.mock import Mock,MagicMock
from jarvis.groq_models import resolve_model,GroqCheckError
class ModelTests(unittest.TestCase):
 def run_model(self,data,override='',side_effect=None):
  keys=Mock();keys.get.return_value='SYNTHETIC-SECRET';http=MagicMock();response=Mock();response.read.return_value=json.dumps({'data':data}).encode();http.open.return_value.__enter__.return_value=response
  if side_effect:http.open.side_effect=side_effect
  factory=Mock(return_value=http);result=resolve_model(override,True,True,keys,factory);self.assertEqual(http.open.call_args.args[0].full_url,'https://api.groq.com/openai/v1/models');self.assertEqual(http.open.call_args.kwargs['timeout'],12);return result
 def test_gates(self):
  for consent,free in [(False,False),(False,True),(True,False)]:
   keys=Mock();opener=Mock()
   with self.assertRaises(GroqCheckError):resolve_model('',consent,free,keys,opener)
   keys.get.assert_not_called();opener.assert_not_called()
 def test_select_fast_active(self):
  self.assertEqual(self.run_model([{'id':'llama-3.3-70b-versatile','active':True},{'id':'llama-3.1-8b-instant','active':True}]),'llama-3.1-8b-instant')
 def test_no_arbitrary_fallback(self):
  with self.assertRaises(GroqCheckError):self.run_model([{'id':'unknown-preview','active':True}])
 def test_inactive_not_selected(self):
  self.assertEqual(self.run_model([{'id':'llama-3.1-8b-instant','active':False},{'id':'llama-3.3-70b-versatile','active':True}]),'llama-3.3-70b-versatile')
 def test_override_active(self):self.assertEqual(self.run_model([{'id':'test-owner-model','active':True}],'test-owner-model'),'test-owner-model')
 def test_override_missing(self):
  with self.assertRaises(GroqCheckError):self.run_model([{'id':'llama-3.1-8b-instant','active':True}],'not-active')
 def test_key_missing(self):
  keys=Mock();keys.get.return_value=None;factory=Mock()
  with self.assertRaises(GroqCheckError):resolve_model('',True,True,keys,factory)
  factory.assert_not_called()
 def test_http_sanitized(self):
  try:self.run_model([],side_effect=urllib.error.HTTPError('secret-url',401,'SYNTHETIC-SECRET',None,None))
  except GroqCheckError as e:self.assertIn('HTTP_401_KEY_REJECTED',str(e));self.assertNotIn('SYNTHETIC-SECRET',str(e));self.assertNotIn('secret-url',str(e))
  else:self.fail('Expected failure')
 def test_tls_sanitized(self):
  with self.assertRaises(GroqCheckError) as caught:self.run_model([],side_effect=ssl.SSLCertVerificationError('SYNTHETIC-SECRET'))
  self.assertNotIn('SYNTHETIC-SECRET',str(caught.exception))

 def test_model_schema_active_omitted(self):self.assertEqual(self.run_model([{'id':'openai/gpt-oss-20b','object':'model','owned_by':'OpenAI'}]),'openai/gpt-oss-20b')
 def test_prefers_production_oss_fast(self):self.assertEqual(self.run_model([{'id':'llama-3.1-8b-instant','active':True},{'id':'openai/gpt-oss-20b'}]),'openai/gpt-oss-20b')
 def test_explicit_inactive_not_selected(self):
  with self.assertRaises(GroqCheckError):self.run_model([{'id':'openai/gpt-oss-20b','active':False}])
