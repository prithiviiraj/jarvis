import unittest,urllib.parse
from jarvis.google_authorization import GoogleAuthorization,IDENTITY
from jarvis.google_tokens import GoogleTokens
from jarvis.google_oauth import SCOPES
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def fixture(self,identity=None,scopes=None):
  s=Store();g=GoogleTokens(s,lambda p:{'access_token':'fixture','refresh_token':'fixture-refresh','token_type':'Bearer','scope':scopes or ' '.join({SCOPES['calendar-freebusy']}|IDENTITY)})
  a=GoogleAuthorization(g,lambda t:identity or {'email':'owner@example.com','email_verified':True,'sub':'fixture-id'});r=a.begin('fixture.apps.googleusercontent.com',12345,['calendar-freebusy'],'owner@example.com',True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(r['authorization_url']).query);url=r['redirect_uri']+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'});return a,s,url
 def test_verified_identity_save_oneuse(self):
  a,s,url=self.fixture();self.assertNotIn(a.oauth.verifier,str(a.snapshot()));self.assertTrue(a.complete(url)['connected']);self.assertEqual(len(s.rows),1)
  with self.assertRaises(ValueError):a.complete(url)
 def test_wrong_identity_or_unverified_or_scope_expansion_no_save(self):
  for identity,scopes in (({'email':'other@example.com','email_verified':True,'sub':'id'},None),({'email':'owner@example.com','email_verified':False,'sub':'id'},None),(None,' '.join({SCOPES['calendar-freebusy'],SCOPES['mail-send']}|IDENTITY)),(None,'openid')):
   a,s,url=self.fixture(identity,scopes)
   with self.assertRaises(ValueError):a.complete(url)
   self.assertFalse(s.rows)
 def test_cancel(self):
  a,s,url=self.fixture();a.cancel()
  with self.assertRaises(ValueError):a.complete(url)
  self.assertFalse(s.rows)
