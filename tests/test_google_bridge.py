import unittest
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.google_tokens import GoogleTokens
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice());self.b.google.tokens=GoogleTokens(Store());self.b.google.auth.tokens=self.b.google.tokens
 def tearDown(self):self.b.close()
 def test_inert_missing_client_and_secret_free_snapshot(self):
  self.assertFalse(self.b.execute({'command':'status'})['google']['busy'])
  with self.assertRaises(ValueError):self.b.execute({'command':'google-connect','account':'owner@example.com','grants':['mail-read'],'consent':True})
  with self.assertRaises(ValueError):self.b.execute({'command':'google-configure','client_id':'fixture.apps.googleusercontent.com','client_secret':'fixture-secret'})
  s=self.b.execute({'command':'google-configure','client_id':'fixture.apps.googleusercontent.com','client_secret':'fixture-secret','consent':True});self.assertNotIn('fixture-secret',str(s));self.b.execute({'command':'pause'});self.assertFalse(self.b.google.busy)
