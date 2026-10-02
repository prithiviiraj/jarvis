import http.server,threading,json,unittest
from jarvis.router import Provider,HttpTransport,ProviderFailure
class Handler(http.server.BaseHTTPRequestHandler):
 code=200;seen=None
 def log_message(self,*a):pass
 def do_POST(self):
  Handler.seen=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  self.send_response(Handler.code)
  if Handler.code==302:self.send_header('Location','https://example.invalid/steal')
  self.end_headers();self.wfile.write(b'{"choices":[{"message":{"content":"Local answer"}}]}')
class RealHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=http.server.HTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.p=Provider('local',f'http://127.0.0.1:{cls.server.server_port}/v1','test')
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def test_real_http(self):
  Handler.code=200;self.assertEqual(HttpTransport().complete(self.p,[{'role':'user','content':'Hi'}]),'Local answer');self.assertFalse(Handler.seen['stream'])
 def test_redirect_refused(self):
  Handler.code=302
  with self.assertRaises(ProviderFailure) as e:HttpTransport().complete(self.p,[{'role':'user','content':'secret'}])
  self.assertEqual(e.exception.code,'http-302')
 def test_rate_limit(self):
  Handler.code=429
  with self.assertRaises(ProviderFailure) as e:HttpTransport().complete(self.p,[{'role':'user','content':'Hi'}])
  self.assertTrue(e.exception.retryable)
