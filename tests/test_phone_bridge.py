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
  self.b.phone.enable(True)
  with self.assertRaisesRegex(ValueError,'History unavailable'):self.b.execute({'command':'history-new'})
  self.assertFalse(self.b.phone.snapshot()['enabled'])

class TransportUI(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_transport_defaults_and_pair_gate(self):
  self.assertEqual(self.b.execute({'command':'status'})['phone']['tls']['state'],'off')
  with self.assertRaises(ValueError):self.b.execute({'command':'phone-pair-open','consent':True})
 def test_review_routes_without_socket_and_stop(self):
  from unittest.mock import Mock
  self.b.phone_transport.prepare=Mock();self.b.phone_transport.start=Mock();self.b.execute({'command':'phone-transport-prepare','origin_host':'https://127.0.0.1:8443','certificate_file':'cert.pem','private_key_file':'key.pem','consent':True});self.b.phone_transport.prepare.assert_called_once_with('https://127.0.0.1:8443','cert.pem','key.pem',True);review={'exact':'fixture'};self.b.execute({'command':'phone-transport-start','reviewed':review,'confirm':True,'phone_trust_confirmed':True});self.b.phone_transport.start.assert_called_once_with(review,True,True);self.assertIsNone(self.b.phone_transport.server)
 def test_pair_code_local_temporary_and_pause_clears(self):
  self.b.phone_transport.state='listening';s=self.b.execute({'command':'phone-pair-open','consent':True});self.assertTrue(s['phone']['pair_code']);s=self.b.execute({'command':'pause'});self.assertIsNone(s['phone']['pair_code']);self.assertEqual(s['phone']['tls']['state'],'off')
