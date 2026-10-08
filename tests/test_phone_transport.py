import shutil,pathlib,socket,ssl,subprocess,tempfile,unittest,urllib.request,json
from jarvis.phone_transport import PhoneTransport
from jarvis.phone_controller import PhoneController
from jarvis.phone_endpoints import PhoneEndpoints
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.cert=self.root/'cert.pem';self.key=self.root/'key.pem';self.controller=PhoneController(processor=lambda *a:None);self.endpoints=PhoneEndpoints(self.controller);self.t=PhoneTransport(self.endpoints,self.root)
  if not shutil.which('openssl'):self.skipTest('Fixture openssl missing')
  subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(self.key),'-out',str(self.cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,capture_output=True)
  (self.root/'index.html').write_text('Private controlled transport fixture')
  for name in ('phone.css','phone.js','capture.js'):(self.root/name).write_text('fixture')
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1]
  self.origin='https://127.0.0.1:'+str(self.port)
 def tearDown(self):self.t.stop();self.tmp.cleanup()
 def prepare(self):return self.t.prepare(self.origin,str(self.cert),str(self.key),True)
 def test_inert_review_and_trust_required(self):
  review=self.prepare();self.assertEqual(self.t.state,'review');self.assertIsNone(self.t.server)
  for approval,trust in [(False,True),(True,False)]:
   with self.assertRaises(ValueError):self.t.start(review,approval,trust)
  with self.assertRaises(ValueError):self.t.start(dict(review,port=9999),True,True)
 def test_real_loopback_tls_host_origin_and_stop(self):
  review=self.prepare();self.t.start(review,True,True);ctx=ssl.create_default_context(cafile=str(self.cert))
  with urllib.request.urlopen(self.origin,context=ctx,timeout=3)as r:self.assertEqual(r.status,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertIn(b'controlled',r.read())
  code=self.controller.enable(True);body=json.dumps({'code':code,'label':'Unverified fixture phone'}).encode();req=urllib.request.Request(self.origin+'/phone/pair',data=body,headers={'Origin':self.origin,'Content-Type':'application/json'})
  with urllib.request.urlopen(req,context=ctx,timeout=3)as r:claim=json.load(r)['claim']
  self.assertTrue(self.endpoints.pending);self.endpoints.approve_local(self.endpoints.pending,True)
  req=urllib.request.Request(self.origin+'/phone/pair-result',data=json.dumps({'claim':claim}).encode(),headers={'Origin':self.origin,'Content-Type':'application/json'})
  with urllib.request.urlopen(req,context=ctx,timeout=3)as r:token=json.load(r)['token']
  self.controller.session.authorize(token);self.t.stop();self.assertEqual(self.t.state,'off')
  with self.assertRaises(ValueError):self.controller.session.authorize(token)
 def test_public_bind_and_certificate_change_refused(self):
  for origin in ['https://8.8.8.8:8443','http://127.0.0.1:8443','https://127.0.0.1:8443/path','https://0.0.0.0:8443','https://192.0.2.1:8443','https://240.0.0.1:8443','https://169.254.1.1:8443']:
   with self.assertRaises(ValueError):self.t.prepare(origin,str(self.cert),str(self.key),True)
  review=self.prepare();self.cert.write_text(self.cert.read_text()+'\n')
  with self.assertRaises(ValueError):self.t.start(review,True,True)

 def test_san_mismatch_and_expired_review(self):
  with self.assertRaises(ValueError):self.t.prepare('https://192.168.1.10:'+str(self.port),str(self.cert),str(self.key),True)
  review=self.prepare();self.t.review_deadline=0
  with self.assertRaises(ValueError):self.t.start(review,True,True)
  self.assertIsNone(self.t.server)

 def test_certificate_validity_horizon(self):
  from unittest.mock import patch
  with patch('jarvis.phone_transport.time.time',return_value=0):
   with self.assertRaisesRegex(ValueError,'currently valid'):self.prepare()
  review=self.prepare();self.t.pending['not_after']=0
  with self.assertRaisesRegex(ValueError,'full session'):self.t.start(review,True,True)
  self.assertIsNone(self.t.server)
