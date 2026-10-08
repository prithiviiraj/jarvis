import unittest,tempfile,pathlib
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.google_tokens import GoogleTokens
from jarvis.google_mail import GoogleMail
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.b=Bridge(WorkspaceVoice());self.b.google.tokens=GoogleTokens(Store());self.b.google.account='owner@example.com';self.b.google_mail=GoogleMail(self.b.google,pathlib.Path(self.temp.name)/'ledger.json',lambda *a:{})
 def tearDown(self):self.b.close();self.temp.cleanup()
 def test_prepare_exact_and_pause_cancel_no_send(self):
  r=self.b.execute({'command':'gmail-prepare','to':['friend@example.com'],'cc':['copy@example.com'],'subject':'Subject','body':'Exact words'})['google']['mail'];self.assertEqual(r['state'],'review');self.assertEqual(r['plan']['payload']['account'],'owner@example.com');self.assertFalse(r['busy'])
  with self.assertRaises(ValueError):self.b.execute({'command':'gmail-submit','reviewed':r['plan']})
  changed=dict(r['plan'],sha256='changed')
  with self.assertRaises(ValueError):self.b.execute({'command':'gmail-submit','reviewed':changed,'confirm':True})
  self.b.execute({'command':'pause'});self.assertEqual(self.b.google_mail.snapshot()['state'],'cancelled')
