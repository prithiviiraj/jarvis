import unittest
from jarvis.google_tokens import GoogleTokens,GoogleCredentials
from jarvis.google_oauth import SCOPES
class Store:
 def __init__(self):self.rows={}
 def set(self,k,v):self.rows[k]=v
 def get(self,k):return self.rows.get(k)
 def delete(self,k):self.rows.pop(k,None)
 def status(self,k):return {'present':k in self.rows}
class Tests(unittest.TestCase):
 def test_isolated_key_scope_cache_and_delete(self):
  calls=[];s=Store();g=GoogleTokens(s,lambda p:(calls.append(p)or{'access_token':'fixture-access','expires_in':3600,'token_type':'Bearer'}));scope=SCOPES['mail-read'];g.save('owner@example.com','fixture.apps.googleusercontent.com','fixture-refresh',[scope],True)
  self.assertTrue(g.status('owner@example.com')['credential_present']);self.assertNotIn('refresh',str(g.status('owner@example.com')));self.assertTrue(GoogleCredentials.target(g.key('owner@example.com')).startswith('JARVIS/google/'))
  self.assertEqual(g.access('owner@example.com',scope),'fixture-access');g.access('owner@example.com',scope);self.assertEqual(len(calls),1)
  with self.assertRaises(ValueError):g.access('owner@example.com',SCOPES['mail-send'])
  g.disconnect('owner@example.com');self.assertFalse(g.status('owner@example.com')['credential_present'])
 def test_no_save_without_consent_or_expanded_scope(self):
  g=GoogleTokens(Store())
  with self.assertRaises(ValueError):g.save('owner@example.com','fixture.apps.googleusercontent.com','refresh',[SCOPES['mail-read']])
  with self.assertRaises(ValueError):g.save('owner@example.com','fixture.apps.googleusercontent.com','refresh',['https://mail.google.com/'],True)
 def test_bad_token_reply_never_cached(self):
  g=GoogleTokens(Store(),lambda p:{'error':'fixture-secret-error'});scope=SCOPES['mail-read'];g.save('owner@example.com','fixture.apps.googleusercontent.com','refresh',[scope],True)
  with self.assertRaises(ValueError):g.access('owner@example.com',scope)
  self.assertFalse(g.cache)
