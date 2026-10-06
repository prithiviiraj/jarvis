import unittest,ssl,io,json,urllib.error
from unittest.mock import Mock,patch
from jarvis.brain_settings import account_models
class SlotTLS(unittest.TestCase):
 def test_certificate_retry_and_inactive_model_filter(self):
  first=Mock();first.open.side_effect=urllib.error.URLError(ssl.SSLCertVerificationError('private-detail'))
  second=Mock();second.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'active','active':True},{'id':'disabled','active':False}]}).encode())
  with patch('jarvis.brain_settings.urllib.request.build_opener',side_effect=[first,second])as factory:
   self.assertEqual(account_models('groq','synthetic-secret'),['active']);self.assertEqual(factory.call_count,2)
  self.assertEqual(second.open.call_args.args[0].full_url,'https://api.groq.com/openai/v1/models')
 def test_safe_auth_error_no_retry(self):
  http=Mock();http.open.side_effect=urllib.error.HTTPError('private-url',401,'synthetic-secret',{},None)
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http)as factory:
   with self.assertRaisesRegex(ValueError,'HTTP_401_KEY_REJECTED')as result:account_models('groq','synthetic-secret')
   self.assertEqual(factory.call_count,1);self.assertNotIn('synthetic-secret',str(result.exception));self.assertNotIn('private-url',str(result.exception))

 def test_chat_and_stream_cloud_use_packaged_roots(self):
  from jarvis.router import HttpTransport
  from jarvis.streaming import StreamTransport
  from jarvis.providers import configured
  p=configured('groq','model')
  with patch('jarvis.router.cloud_http',return_value='safe-http')as factory:
   self.assertEqual(HttpTransport().opener(p),'safe-http');factory.assert_called_once()
  with patch('jarvis.streaming.cloud_http',return_value='safe-stream')as factory:
   self.assertEqual(StreamTransport().opener(p),'safe-stream');factory.assert_called_once()
