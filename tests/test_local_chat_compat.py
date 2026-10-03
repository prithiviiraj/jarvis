import io,json,threading,unittest
from unittest.mock import Mock,patch
from jarvis.streaming import StreamTransport,text_deltas
from jarvis.router import Provider,ProviderFailure
class Response(io.BytesIO):
 def __init__(self,body,ctype):super().__init__(body);self.headers={'Content-Type':ctype}
def event(value):return ('data: '+json.dumps(value)+'\n\n').encode()
class LocalCompatibility(unittest.TestCase):
 def setUp(self):self.local=Provider('local','http://127.0.0.1:1234/v1','qwen2.5-vl-3b-instruct');self.t=StreamTransport()
 def test_empty_sse_retries_once_without_stream(self):
  with patch.object(self.t,'opener')as opener,patch('jarvis.streaming.HttpTransport')as fallback:
   opener.return_value.open.return_value=Response(b'data: [DONE]\n\n','text/event-stream');fallback.return_value.complete.return_value='Hello'
   self.assertEqual(list(self.t.stream(self.local,[{'role':'user','content':'hi'}])),['Hello']);fallback.return_value.complete.assert_called_once_with(self.local,[{'role':'user','content':'hi'}],None)
 def test_json_instead_of_sse(self):
  with patch.object(self.t,'opener')as opener,patch('jarvis.streaming.HttpTransport')as fallback:
   opener.return_value.open.return_value=Response(json.dumps({'choices':[{'message':{'content':[{'type':'text','text':'Hello'}]}}]}).encode(),'application/json')
   self.assertEqual(list(self.t.stream(self.local,[{}])),['Hello']);fallback.assert_not_called()
 def test_no_retry_after_text(self):
  with patch.object(self.t,'opener')as opener,patch('jarvis.streaming.HttpTransport')as fallback:
   opener.return_value.open.return_value=Response(event({'choices':[{'delta':{'content':'Hello'}}]})+b'data: [DONE]\n','text/event-stream')
   self.assertEqual(list(self.t.stream(self.local,[{}])),['Hello']);fallback.assert_not_called()
 def test_no_reasoning_as_answer(self):
  self.assertEqual(list(text_deltas(Response(event({'choices':[{'delta':{'reasoning_content':'private'}}]})+b'data: [DONE]\n','text/event-stream'))),[])
 def test_message_shape(self):self.assertEqual(list(text_deltas(Response(event({'choices':[{'message':{'content':'Hello'}}]}),'text/event-stream'))),['Hello'])
 def test_empty_retry_diagnostic(self):
  with patch.object(self.t,'opener')as opener,patch('jarvis.streaming.HttpTransport')as fallback:
   opener.return_value.open.return_value=Response(b'data: [DONE]\n','text/event-stream');fallback.return_value.complete.side_effect=ProviderFailure('empty')
   with self.assertRaisesRegex(ProviderFailure,'local-empty-after-retry'):list(self.t.stream(self.local,[{}]))
 def test_cloud_no_local_retry(self):
  with patch.object(self.t,'opener')as opener,patch('jarvis.streaming.HttpTransport')as fallback:
   opener.return_value.open.return_value=Response(b'data: [DONE]\n','text/event-stream');self.assertEqual(list(self.t.stream(Provider('groq','https://example.test/v1','test',True),[{}])),[]);fallback.assert_not_called()
