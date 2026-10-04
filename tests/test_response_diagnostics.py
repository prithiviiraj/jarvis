import unittest,json,io
from jarvis.response_diagnostics import ResponseDiagnostics
from jarvis.streaming import text_deltas
class DiagnosticTests(unittest.TestCase):
 def test_secret_values_and_arbitrary_labels_never_copied(self):
  d=ResponseDiagnostics('qwen2.5-vl-3b-instruct',1,'stream');d.header('text/event-stream; SECRET')
  d.observe({'choices':[{'finish_reason':'SECRET','delta':{'content':[{'type':'SECRET','text':'SECRET'},{'type':'text','text':'SECRET'}],'reasoning':'SECRET','tool_calls':[{'name':'SECRET','arguments':'SECRET'}]}}],'usage':{'prompt_tokens':2,'completion_tokens':3,'other':'SECRET'}})
  s=d.snapshot();self.assertNotIn('SECRET',json.dumps(s));self.assertEqual(s['recognized_text_chars'],6);self.assertEqual(s['part_types'],['unknown','text']);self.assertEqual(s['usage'],{'prompt_tokens':2,'completion_tokens':3})
 def test_zero_vs_unsupported(self):
  d=ResponseDiagnostics('model',1,'nonstream');d.observe({'choices':[{'message':{'content':''},'finish_reason':'stop'}],'usage':{'completion_tokens':0}});self.assertEqual(d.snapshot()['response_category'],'no_final_text');self.assertEqual(d.snapshot()['usage']['completion_tokens'],0)
  d=ResponseDiagnostics('model',1,'nonstream');d.observe({'choices':[{'message':{'content':[{'type':'output_text','text':'secret'}]}}]});self.assertEqual(d.snapshot()['response_category'],'unrecognized_content_parts')
 def test_reasoning_presence_only(self):
  d=ResponseDiagnostics('model',1,'stream');d.observe({'choices':[{'delta':{'reasoning_content':'secret'}}]});self.assertEqual(d.snapshot()['response_category'],'reasoning_without_final_text');self.assertNotIn('secret',str(d.snapshot()))
 def test_snapshot_immutable_and_bad_model_redacted(self):
  d=ResponseDiagnostics('secret phrase',1,'stream');s=d.snapshot();s['usage']['anything']=1;self.assertEqual(d.snapshot()['usage'],{});self.assertEqual(s['model'],'redacted')
 def test_sse_usage_event_and_text(self):
  d=ResponseDiagnostics('model',1,'stream');raw=b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\ndata: {"choices":[],"usage":{"completion_tokens":1}}\n\ndata: [DONE]\n\n';self.assertEqual(list(text_deltas(io.BytesIO(raw),diagnostic=d)),['hello']);self.assertEqual(d.snapshot()['recognized_text_chars'],5);self.assertEqual(d.snapshot()['usage']['completion_tokens'],1)

from jarvis.router import Provider,BrainRouter,RouterError
from jarvis.streaming import StreamTransport
from unittest.mock import patch
import threading,http.server
class DiagnosticHTTPTests(unittest.TestCase):
 def test_two_requests_private_metadata_reaches_router(self):
  class Handler(http.server.BaseHTTPRequestHandler):
   count=0
   def log_message(self,*args):pass
   def do_POST(self):
    type(self).count+=1;body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
    self.send_response(200)
    if body['stream']:
     self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(b'data: {"choices":[{"delta":{"reasoning_content":"SECRET REASONING"},"finish_reason":"stop"}],"usage":{"completion_tokens":2}}\n\ndata: [DONE]\n\n')
    else:
     self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"choices":[{"message":{"content":"","reasoning_content":"SECRET REASONING"},"finish_reason":"stop"}],"usage":{"prompt_tokens":5,"completion_tokens":2}}')
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  try:
   p=Provider('local','http://127.0.0.1:'+str(server.server_port)+'/v1','test-model');r=BrainRouter([p]);t=StreamTransport()
   with self.assertRaisesRegex(RouterError,'local-empty-after-retry'):list(r.stream([{'role':'user','content':'SECRET PROMPT'}],stream_transport=t))
   self.assertEqual(Handler.count,2);self.assertEqual([d['attempt']for d in r.last_diagnostics],[1,2]);self.assertEqual(r.last_diagnostics[1]['usage']['completion_tokens'],2);self.assertNotIn('SECRET',json.dumps(r.last_diagnostics));self.assertEqual(r.last_diagnostics[0]['response_category'],'reasoning_without_final_text')
  finally:server.shutdown();server.server_close();worker.join(2)
 def test_length_metadata_survives_failure(self):
  from test_local_chat_compat import Response
  t=StreamTransport();p=Provider('local','http://127.0.0.1:1234/v1','spark-x2.5-4b')
  with patch.object(t,'opener')as op:
   op.return_value.open.return_value=Response(b'data: {"choices":[{"delta":{"reasoning":"SECRET"},"finish_reason":"length"}],"usage":{"completion_tokens":300}}\n','text/event-stream')
   with self.assertRaises(RouterError):list(t.stream(p,[{}]))
  self.assertEqual(t.last_diagnostics[0]['finish_reason'],'length');self.assertEqual(t.last_diagnostics[0]['usage']['completion_tokens'],300);self.assertNotIn('SECRET',str(t.last_diagnostics))
