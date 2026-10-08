import tempfile,unittest
from jarvis.phone_http import PhoneHTTP
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.h=PhoneHTTP(None,'https://192.168.1.5:8443',self.tmp.name);self.headers={'Host':'192.168.1.5:8443','Origin':'https://192.168.1.5:8443','Content-Type':'application/json','Content-Length':'2'}
 def tearDown(self):self.tmp.cleanup()
 def test_static_and_post_origin_tls_boundary(self):
  self.assertEqual(self.h.validate('GET','/',{'Host':'192.168.1.5:8443'},'127.0.0.1',True),0);self.assertEqual(self.h.validate('POST','/phone/pair',self.headers,'192.168.1.4',True),2)
  for headers,peer,tls in ((dict(self.headers,Host='evil.test'),'192.168.1.4',True),(dict(self.headers,Origin='https://evil.test'),'192.168.1.4',True),(self.headers,'8.8.8.8',True),(self.headers,'192.168.1.4',False)):
   with self.assertRaises(ValueError):self.h.validate('POST','/phone/pair',headers,peer,tls)
 def test_paths_sizes_and_transfer(self):
  for path in ('/phone/approve','/bridge','/phone/turn?x=1','/../phone.js'):
   with self.assertRaises(ValueError):self.h.validate('POST',path,self.headers,'127.0.0.1',True)
  for headers in (dict(self.headers,**{'Content-Length':'1280201'}),dict(self.headers,**{'Content-Length':'-1'}),dict(self.headers,**{'Transfer-Encoding':'chunked'})):
   with self.assertRaises(ValueError):self.h.validate('POST','/phone/turn',headers,'127.0.0.1',True)
 def test_rate_and_handler_without_socket(self):
  for _ in range(150):self.h.validate('POST','/phone/reply',self.headers,'127.0.0.1',True)
  with self.assertRaises(ValueError):self.h.validate('POST','/phone/reply',self.headers,'127.0.0.1',True)
  self.assertTrue(callable(self.h.handler()));self.assertEqual(self.h.token({'Authorization':'Bearer x'}),'x')
  with self.assertRaises(ValueError):self.h.token({'Authorization':'Basic x'})

 def test_stop_not_rate_limited_and_old_peers_expire(self):
  for _ in range(150):self.h.validate('POST','/phone/reply',self.headers,'127.0.0.1',True)
  self.assertEqual(self.h.validate('POST','/phone/stop',self.headers,'127.0.0.1',True),2)
  self.h.clock=lambda:1000000000000
  self.h.validate('POST','/phone/pair',self.headers,'192.168.1.8',True);self.assertNotIn('127.0.0.1',self.h.windows)
