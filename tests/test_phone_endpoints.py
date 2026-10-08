import base64,json,unittest
from jarvis.phone_controller import PhoneController
from jarvis.phone_endpoints import PhoneEndpoints
from test_phone_controller import Processor
from test_phone_session import audio
class Tests(unittest.TestCase):
 def setUp(self):self.c=PhoneController(Processor());self.e=PhoneEndpoints(self.c)
 def tearDown(self):self.e.stop_local();self.c.close()
 def call(self,path,data={},token=''):return self.e.handle(path,json.dumps(data).encode(),token,True,True)
 def pair(self):
  r=self.call('/phone/pair',{'code':self.c.enable(True),'label':'phone'});self.e.approve_local(self.e.pending,True);return self.call('/phone/pair-result',r)['token']
 def test_no_http_authority_and_no_untrusted_transport(self):
  for path in ('/bridge','/phone/approve','/phone/desktop-run'):
   with self.assertRaises(ValueError):self.call(path)
  with self.assertRaises(ValueError):self.e.handle('/phone/pair',b'{}',trusted_https=False,same_origin=True)
  with self.assertRaises(ValueError):self.e.handle('/phone/pair',b'{}',trusted_https=True,same_origin=False)
 def test_exact_local_approval_oneuse_delivery(self):
  r=self.call('/phone/pair',{'code':self.c.enable(True),'label':'claiming owner'});self.assertEqual(self.call('/phone/pair-result',r),{'waiting':True})
  with self.assertRaises(ValueError):self.e.approve_local(self.e.pending)
  self.e.approve_local(self.e.pending,True);t=self.call('/phone/pair-result',r)['token']
  with self.assertRaises(ValueError):self.call('/phone/pair-result',r)
  self.assertNotIn(t,str(self.e.snapshot()));self.call('/phone/stop',token=t)
  with self.assertRaises(ValueError):self.call('/phone/reply',token=t)
 def test_audio_roundtrip_no_network(self):
  t=self.pair();self.call('/phone/turn',{'wav':base64.b64encode(audio()).decode()},t);self.c.worker.join(2);reply=self.call('/phone/reply',token=t);self.assertEqual(reply['text'],'reply');self.assertEqual(base64.b64decode(reply['wav']),audio());self.assertEqual(self.call('/phone/reply',token=t),{'waiting':True})
 def test_bad_payloads(self):
  t=self.pair()
  for data in ({'wav':'!bad'},{'command':'desktop-run'},{'wav':123}):
   with self.assertRaises(ValueError):self.call('/phone/turn',data,t)
