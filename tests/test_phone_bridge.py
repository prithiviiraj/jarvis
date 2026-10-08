import unittest
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_off_no_transport_or_auto_pair(self):
  s=self.b.execute({'command':'status'})['phone'];self.assertFalse(s['enabled']);self.assertFalse(s['paired']);self.assertEqual(s['transport'],'Not configured; no network listener')
  with self.assertRaises(ValueError):self.b.execute({'command':'phone-enable','consent':True})
  with self.assertRaises(ValueError):self.b.execute({'command':'phone-pair-approve','reviewed':{},'confirm':True})
 def test_pair_approve_local_and_pause_revokes(self):
  code=self.b.phone.enable(True);r=self.b.phone_endpoints.handle('/phone/pair',__import__('json').dumps({'code':code,'label':'Unverified device'}).encode(),trusted_https=True,same_origin=True)
  state=self.b.execute({'command':'status'})['phone'];review=state['pending'];self.assertEqual(review['label'],'Unverified device')
  self.b.execute({'command':'phone-pair-approve','reviewed':review,'confirm':True});self.assertTrue(self.b.phone.snapshot()['paired']);self.b.execute({'command':'pause'});self.assertFalse(self.b.phone.snapshot()['paired'])
  with self.assertRaises(ValueError):self.b.phone_endpoints.handle('/phone/pair-result',__import__('json').dumps(r).encode(),trusted_https=True,same_origin=True)
 def test_stop_retains_chats(self):
  self.b.messages=[{'name':'You','text':'retained'}];s=self.b.execute({'command':'phone-stop'});self.assertEqual(s['messages'],self.b.messages);self.assertFalse(s['phone']['enabled'])

 def test_desktop_new_chat_revokes_phone(self):
  self.b.phone.enable(True);self.b.execute({'command':'history-new'});self.assertFalse(self.b.phone.snapshot()['enabled'])
