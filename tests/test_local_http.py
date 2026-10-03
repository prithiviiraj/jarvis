import unittest,ssl,urllib.request
from unittest.mock import patch
from jarvis.router import HttpTransport,local_http,ProviderFailure,Provider
from jarvis.streaming import StreamTransport
class LocalHttpTests(unittest.TestCase):
 def test_loopback_does_not_initialize_windows_tls_store(self):
  with patch('ssl.create_default_context',side_effect=AssertionError('TLS initialization')):
   h=HttpTransport();s=StreamTransport();local=Provider('local','http://127.0.0.1:1234/v1','test')
   self.assertIs(h.opener(local),h.http);self.assertIs(s.opener(local),s.http)
 def test_local_https_refused(self):
  with self.assertRaises(ProviderFailure):local_http().open('https://example.invalid')
 def test_cloud_retains_verified_tls_handler(self):
  h=HttpTransport();p=Provider('cloud','https://example.invalid/v1','test',True)
  handler=next(x for x in h.opener(p).handlers if isinstance(x,urllib.request.HTTPSHandler))
  self.assertNotEqual(type(handler).__name__,'LocalOnlyHTTPS')
