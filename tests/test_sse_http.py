import http.server,threading,unittest,json
from jarvis.streaming import StreamTransport
from jarvis.router import Provider
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  j=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  assert j['stream'] is True
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
  for text in ['Hello ','world.']:
   self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':text}}]})+'\n\n').encode());self.wfile.flush()
  self.wfile.write(b'data: [DONE]\n\n')
class SseHttpTests(unittest.TestCase):
 def test_real_stream(self):
  server=http.server.HTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
  try:
   p=Provider('local',f'http://127.0.0.1:{server.server_port}/v1','test');self.assertEqual(list(StreamTransport().stream(p,[{'role':'user','content':'Hi'}])),['Hello ','world.'])
  finally:server.shutdown();server.server_close();t.join()
