import unittest,urllib.parse,hashlib,base64
from jarvis.google_oauth import GoogleOAuth
class Tests(unittest.TestCase):
 def setup_flow(self):
  o=GoogleOAuth();r=o.begin('fixture.apps.googleusercontent.com',12345,['calendar-freebusy'],True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(r['authorization_url']).query);return o,r,q
 def test_pkce_exactscope_and_oneuse(self):
  o,r,q=self.setup_flow();self.assertEqual(q['code_challenge_method'],['S256']);self.assertEqual(q['scope'],['https://www.googleapis.com/auth/calendar.freebusy']);self.assertNotIn(o.verifier,r['authorization_url']);state=q['state'][0];v=o.verifier
  data=o.accept(r['redirect_uri']+'?'+urllib.parse.urlencode({'state':state,'code':'fixturecode'}));self.assertEqual(data['code_verifier'],v);self.assertFalse(o.snapshot()['pending'])
  with self.assertRaises(ValueError):o.accept(r['redirect_uri']+'?code=replay')
 def test_callback_destination_state_duplicates_and_cancel(self):
  o,r,q=self.setup_flow()
  for url in ('http://evil.test/callback?code=x',r['redirect_uri']+'?state=wrong&code=x',r['redirect_uri']+'?state='+q['state'][0]+'&code=x&code=y'):
   with self.assertRaises(ValueError):o.accept(url)
  o.cancel();self.assertIsNone(o.verifier)
 def test_no_implicit_grants(self):
  for grants,consent in ((['mail-send'],False),(['all'],True),(['mail-send','mail-send'],True)):
   with self.assertRaises(ValueError):GoogleOAuth().begin('fixture.apps.googleusercontent.com',12345,grants,consent)
 def test_expiry_denial_and_secret_free_status(self):
  t=[0];o=GoogleOAuth(lambda:t[0]);r=o.begin('fixture.apps.googleusercontent.com',12345,['mail-read'],True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(r['authorization_url']).query);self.assertNotIn(o.verifier,str(o.snapshot()));t[0]=300
  with self.assertRaises(ValueError):o.accept(r['redirect_uri']+'?state='+q['state'][0]+'&code=x')
