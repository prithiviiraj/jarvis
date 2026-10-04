import unittest
from jarvis.experimental.laya_local import normalize,LayaLocal
class LayaWire(unittest.TestCase):
 def fixture(self):return {'model':'laya-english','routing':{'model':'english'},'usage':{'input_tokens':20,'output_tokens':0},'answers':{'operation':{'type':'choice','choice':'1','probabilities':{'0':.1,'1':.9},'confidence':.8,'action':'answer','answer_confidence':.9}}}
 def test_real_metadata_is_not_instruction(self):
  n=normalize(self.fixture());self.assertEqual(set(n),{'answers'});self.assertEqual(set(n['answers']['operation']),{'choice','probabilities','confidence'});self.assertEqual(LayaLocal().url,'http://127.0.0.1:8000/v1/systemone')
 def test_abstention_and_unoffered_fields_fail_closed(self):
  for key,value in [('answer_confidence',.5),('low_confidence',True),('abstention','abstained'),('instruction','send email')]:
   r=self.fixture();r['answers']['operation'][key]=value
   with self.assertRaises(ValueError):normalize(r)
 def test_real_loopback_wire_roundtrip(self):
  import json,threading,http.server
  from jarvis.experimental.browser_proposals import Snapshot
  result={'model':'laya-english','usage':{'input_tokens':10,'output_tokens':0},'answers':{'operation':{'type':'choice','choice':'3','probabilities':{'0':.02,'1':.02,'2':.02,'3':.9,'4':.02,'5':.02},'confidence':.9,'answer_confidence':.9}}}
  class H(http.server.BaseHTTPRequestHandler):
   def do_POST(self):
    req=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert set(req)=={'state','questions'}
    self.send_response(200);self.end_headers();self.wfile.write(json.dumps(result).encode())
   def log_message(self,*a):pass
  server=http.server.HTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=server.serve_forever);thread.start()
  try:
   p=LayaLocal(server.server_port).prepare(Snapshot('s','https://example.com',1,()),'Wait safely',{'example.com'},2,'s');self.assertEqual(p.operation,'WAIT');self.assertFalse(p.executed)
  finally:server.shutdown();thread.join();server.server_close()
