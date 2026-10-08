import unittest,urllib.request,urllib.error,urllib.parse
from jarvis.google_loopback import GoogleLoopback
import test_google_authorization as fixture_module
class Tests(unittest.TestCase):
 def setup_loop(self):
  a,s,_=fixture_module.Tests().fixture();l=GoogleLoopback(a);r=l.begin('fixture.apps.googleusercontent.com',['calendar-freebusy'],'owner@example.com',True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(r['authorization_url']).query);url=r['redirect_uri']+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'});return l,s,url
 def test_real_loopback_capture_no_secret_status(self):
  l,s,url=self.setup_loop()
  try:
   self.assertEqual(l.server.server_address[0],'127.0.0.1')
   with urllib.request.urlopen(url,timeout=2)as r:self.assertEqual(r.status,200);self.assertEqual(r.headers['Cache-Control'],'no-store')
   self.assertNotIn('fixture-code',str(l.snapshot()));self.assertTrue(l.snapshot()['callback_received']);self.assertFalse(s.rows);self.assertTrue(l.complete()['connected']);self.assertEqual(len(s.rows),1)
  finally:l.stop()
 def test_host_state_origin_and_stop(self):
  l,s,url=self.setup_loop()
  try:
   for req in (urllib.request.Request(url,headers={'Host':'evil.test'}),urllib.request.Request(url,headers={'Origin':'https://evil.test'}),urllib.request.Request(url.replace('state=','state=wrong'))):
    with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req,timeout=2)
   self.assertFalse(l.snapshot()['callback_received']);self.assertFalse(s.rows)
  finally:l.stop()
  self.assertFalse(l.snapshot()['pending'])
 def test_no_implicit_listener(self):
  a,s,_=fixture_module.Tests().fixture();l=GoogleLoopback(a)
  with self.assertRaises(ValueError):l.begin('fixture.apps.googleusercontent.com',['calendar-freebusy'],'owner@example.com')
  self.assertIsNone(l.server)
