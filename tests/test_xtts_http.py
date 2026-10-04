import unittest,http.server,threading,io,wave
from jarvis.experimental.xtts_local import XTTSLocal
class RealLocalHTTP(unittest.TestCase):
 def test_real_loopback_pcm_and_redirect_refusal(self):
  buf=io.BytesIO()
  with wave.open(buf,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\x01\x00'*240)
  mode=['pcm'];requests=[]
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_GET(self):
    requests.append(self.path)
    if mode[0]=='redirect':self.send_response(302);self.send_header('Location','https://example.com/');self.end_headers()
    else:self.send_response(200);self.send_header('Content-Type','audio/wav');self.end_headers();self.wfile.write(buf.getvalue())
  server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   client=XTTSLocal(port=server.server_port,noncommercial=True);a,sr=client.synthesize('Hello');self.assertEqual(len(a),240);self.assertEqual(sr,24000);self.assertIn('speaker-id=Craig+Gutsy',requests[0])
   mode[0]='redirect'
   with self.assertRaises(ValueError):client.synthesize('Hello')
  finally:server.shutdown();server.server_close();thread.join(2)
