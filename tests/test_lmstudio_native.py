import unittest,json,io
from unittest.mock import Mock,patch
from jarvis.lmstudio_rest import NativeSparkTransport,request_payload
from jarvis.router import Provider,ProviderFailure
class Response(io.BytesIO):
 def __init__(self,body,ctype='application/json'):super().__init__(body);self.headers={'Content-Type':ctype}
def model(options):return Response(json.dumps({'models':[{'key':'spark-x2.5-4b','capabilities':{'reasoning':{'allowed_options':options}}}]}).encode())
def frame(e):return ('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n').encode()
def end(tokens=5):return frame({'type':'chat.end','result':{'output':[],'stats':{'input_tokens':7,'total_output_tokens':tokens,'reasoning_output_tokens':0}}})
class NativeTests(unittest.TestCase):
 def setUp(self):self.p=Provider('local','http://127.0.0.1:1234/v1','spark-x2.5-4b');self.t=NativeSparkTransport()
 def test_stateless_context_not_dropped(self):
  p=request_payload(self.p.model,[{'role':'system','content':'persona'},{'role':'user','content':'prior'},{'role':'assistant','content':'old'},{'role':'user','content':'current'}]);self.assertEqual(p['input'],'current');self.assertIn('"role": "assistant"',p['system_prompt']);self.assertIn('prior',p['system_prompt']);self.assertFalse(p['store']);self.assertEqual(p['integrations'],[]);self.assertEqual(p['reasoning'],'off')
 def test_final_stream_only_and_payload(self):
  response=Response(frame({'type':'message.delta','content':'<think>private</think>Hi'})+end(),'text/event-stream')
  with patch.object(self.t.http,'open',side_effect=[model(['off','on']),response])as call:
   self.assertEqual(list(self.t.stream(self.p,[{'role':'user','content':'hi'}])),['Hi']);body=json.loads(call.call_args.args[0].data);self.assertFalse(body['store']);self.assertEqual(body['reasoning'],'off');self.assertEqual(body['max_output_tokens'],1024)
  self.assertEqual(self.t.last_diagnostics[0]['usage']['reasoning_tokens'],0)
 def test_unsupported_never_falls_back(self):
  with patch.object(self.t.http,'open',return_value=model(['on']))as call:
   with self.assertRaisesRegex(ProviderFailure,'native-reasoning-off-unavailable'):list(self.t.stream(self.p,[{'role':'user','content':'hi'}]))
   self.assertEqual(call.call_count,1)
 def test_off_ignored_never_speaks_reasoning(self):
  response=Response(frame({'type':'reasoning.delta','content':'private secret'})+end(),'text/event-stream')
  with patch.object(self.t.http,'open',side_effect=[model(['off']),response]):
   with self.assertRaisesRegex(ProviderFailure,'native-reasoning-off-ignored'):list(self.t.stream(self.p,[{'role':'user','content':'hi'}]))
  self.assertNotIn('secret',str(self.t.last_diagnostics));self.assertEqual(self.t.last_diagnostics[0]['reasoning_chars'],14)
 def test_cap_marks_final(self):
  response=Response(frame({'type':'message.delta','content':'Final'})+end(1024),'text/event-stream')
  with patch.object(self.t.http,'open',side_effect=[model(['off']),response]):self.assertEqual(list(self.t.stream(self.p,[{'role':'user','content':'hi'}])),['Final'])
  self.assertEqual(self.t.last_diagnostics[0]['finish_reason'],'length')
 def test_dropped_stream(self):
  with patch.object(self.t.http,'open',side_effect=[model(['off']),Response(b'', 'text/event-stream')]):
   with self.assertRaisesRegex(ProviderFailure,'native-incomplete-stream'):list(self.t.stream(self.p,[{'role':'user','content':'hi'}]))
class StickyDiagnosticsTests(unittest.TestCase):
 def test_finish_usage_never_erase_reasoning(self):
  from jarvis.response_diagnostics import ResponseDiagnostics
  d=ResponseDiagnostics('spark-x2.5-4b',1,'stream');d.observe({'choices':[{'delta':{'reasoning_content':'secret'}}]});d.observe({'choices':[{'delta':{},'finish_reason':'length'}]});d.observe({'choices':[],'usage':{'completion_tokens':1024}});s=d.snapshot();self.assertEqual(s['response_category'],'reasoning_without_final_text');self.assertEqual(s['reasoning_fields'],['reasoning_content']);self.assertEqual(s['reasoning_chars'],6);self.assertNotIn('secret',str(s))
class NativeHTTPTests(unittest.TestCase):
 def test_actual_loopback_sse_reasoning_off(self):
  import http.server,threading
  rows=[]
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    self.send_response(200);self.end_headers();self.wfile.write(model(['off']).getvalue())
   def do_POST(self):
    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));rows.append(body);self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(frame({'type':'message.delta','content':'Short answer.'})+end())
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   p=Provider('local',f'http://127.0.0.1:{server.server_port}/v1','spark-x2.5-4b');t=NativeSparkTransport();self.assertEqual(list(t.stream(p,[{'role':'user','content':'hi'}])),['Short answer.']);self.assertEqual(rows[0]['reasoning'],'off');self.assertFalse(rows[0]['store'])
  finally:server.shutdown();server.server_close();thread.join()
