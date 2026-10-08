import unittest,time,urllib.parse,urllib.request
from jarvis.google_connection import GoogleConnection,CLIENT_KEY
import test_google_authorization as fixture
class Tests(unittest.TestCase):
 def setup_connection(self):
  auth,store,_=fixture.Tests().fixture();urls=[];c=GoogleConnection(auth.tokens,auth,lambda u:urls.append(u)or True);c.configure('fixture.apps.googleusercontent.com','fixture-secret',True);return c,store,urls
 def test_no_implicit_browser_or_connection_and_config_secret_private(self):
  c,s,urls=self.setup_connection()
  try:
   self.assertFalse(urls);self.assertNotIn('fixture-secret',str(c.snapshot()));self.assertIn(CLIENT_KEY,s.rows)
   with self.assertRaises(ValueError):c.begin('owner@example.com',['mail-read'])
   self.assertFalse(urls)
  finally:c.stop()
 def test_end_to_end_loopback_fixture_and_disconnect(self):
  c,s,urls=self.setup_connection()
  try:
   c.begin('owner@example.com',['calendar-freebusy'],True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query);url=q['redirect_uri'][0]+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'})
   with urllib.request.urlopen(url,timeout=2)as r:self.assertEqual(r.status,200)
   c.worker.join(3);self.assertFalse(c.busy);self.assertFalse(c.error);self.assertTrue(c.tokens.status('owner@example.com')['credential_present']);c.disconnect(True);self.assertFalse(c.tokens.status('owner@example.com')['credential_present'])
  finally:c.stop()
 def test_stop_during_token_exchange_no_late_save(self):
  import threading
  c,s,urls=self.setup_connection();entered=threading.Event();release=threading.Event();original=c.tokens.transport
  def blocked(payload):entered.set();release.wait(3);return original(payload)
  c.tokens.transport=blocked
  try:
   c.begin('owner@example.com',['calendar-freebusy'],True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query);url=q['redirect_uri'][0]+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'})
   with urllib.request.urlopen(url,timeout=2):pass
   self.assertTrue(entered.wait(2));c.stop();release.set();c.worker.join(3);self.assertFalse(c.tokens.status('owner@example.com')['credential_present']);self.assertFalse(c.busy)
  finally:release.set();c.stop()
