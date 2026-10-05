import io,json,threading,unittest
from jarvis.streaming import text_deltas,sentences
from jarvis.router import ProviderFailure

def frame(value):return ('data: '+json.dumps(value)+'\n\n').encode()
def delta(text):return frame({'choices':[{'delta':{'content':text}}]})
class StreamingTests(unittest.TestCase):
 def test_text_only(self):
  raw=b': keepalive\n\n'+delta('Hi ')+frame({'choices':[{'delta':{'tool_calls':[{'name':'delete'}]}}]})+delta('there')+b'data: [DONE]\n\n'+delta('ignored')
  self.assertEqual(list(text_deltas(io.BytesIO(raw))),['Hi ','there'])
 def test_cancel(self):
  e=threading.Event();e.set();self.assertEqual(list(text_deltas(io.BytesIO(delta('secret')),e)),[])
 def test_bad_json(self):
  with self.assertRaises(ProviderFailure):list(text_deltas(io.BytesIO(b'data: no\n')))
 def test_line_cap(self):
  with self.assertRaises(ProviderFailure):list(text_deltas(io.BytesIO(b'data: '+b'x'*18000+b'\n')))
 def test_stream_cap(self):
  with self.assertRaises(ProviderFailure):list(text_deltas(io.BytesIO(delta('hello')),max_bytes=3))
 def test_error_event(self):
  with self.assertRaises(ProviderFailure):list(text_deltas(io.BytesIO(frame({'error':{'message':'private'}}))))
 def test_sentence_chunks(self):self.assertEqual(list(sentences(['Hello',' world. Next',' line?'])),['Hello world.','Next line?'])
 def test_bounded(self):self.assertEqual(list(sentences(['a'*100],max_chars=20)),['a'*20]*5)
 def test_tail(self):self.assertEqual(list(sentences(['unfinished clause'])),['unfinished clause'])

from jarvis.router import BrainRouter,Provider,RouterError
from unittest.mock import Mock
class RouterStreamTests(unittest.TestCase):
 def setUp(self):
  self.p=Provider('local','http://127.0.0.1:1234/v1','test');self.c=Provider('gemini','https://example.invalid/v1','test',True);self.t=Mock();self.k=Mock();self.k.get.return_value='synthetic';self.r=BrainRouter([self.p,self.c],key_store=self.k)
 def test_no_cloud_without_consent(self):
  self.t.stream.side_effect=ProviderFailure('bad')
  with self.assertRaises(RouterError):list(self.r.stream([{}],stream_transport=self.t))
  self.assertEqual(self.t.stream.call_count,1)
 def test_pretext_failover(self):
  self.t.stream.side_effect=[ProviderFailure('429'),iter(['Hi','!'])]
  out=list(self.r.stream([{}],cloud_consent=True,stream_transport=self.t));self.assertEqual([x['text'] for x in out],['Hi','!']);self.assertEqual(out[0]['provider'],'gemini')
 def test_partial_no_mix(self):
  def broken(*a):
   yield 'partial';raise ProviderFailure('connection')
  self.t.stream.side_effect=broken
  it=self.r.stream([{}],True,stream_transport=self.t);self.assertEqual(next(it)['text'],'partial')
  with self.assertRaises(RouterError):next(it)
  self.assertEqual(self.t.stream.call_count,1)
 def test_cancel(self):
  e=threading.Event();e.set();self.assertEqual(list(self.r.stream([{}],cancel=e,stream_transport=self.t)),[]);self.t.stream.assert_not_called()

class GroqModelFallbackTests(unittest.TestCase):
 def test_pretext_rate_limit_smaller_model(self):
  p=Provider('groq','https://api.groq.com/openai/v1','openai/gpt-oss-120b',True,allow_20b_fallback=True);keys=Mock();keys.get.return_value='synthetic';t=Mock();t.stream.side_effect=[ProviderFailure('http-429'),iter(['Hello'])]
  out=list(BrainRouter([p],key_store=keys).stream([{}],True,stream_transport=t));self.assertEqual(out[0]['model'],'openai/gpt-oss-20b');self.assertEqual(t.stream.call_count,2)
 def test_no_fallback_after_partial(self):
  p=Provider('groq','https://api.groq.com/openai/v1','openai/gpt-oss-120b',True,allow_20b_fallback=True);keys=Mock();keys.get.return_value='synthetic';t=Mock()
  def broken(*args):yield 'partial';raise ProviderFailure('http-429')
  t.stream.side_effect=broken
  with self.assertRaises(RouterError):list(BrainRouter([p],key_store=keys).stream([{}],True,stream_transport=t))
  self.assertEqual(t.stream.call_count,1)

class StreamErrorDetailTests(unittest.TestCase):
 def test_http_failure_code_survives(self):
  t=Mock();t.stream.side_effect=ProviderFailure('http-503')
  with self.assertRaisesRegex(RouterError,'http-503'):list(BrainRouter([Provider('local','http://127.0.0.1:1234/v1','test')]).stream([{}],stream_transport=t))

class ScaffoldRetryTests(unittest.TestCase):
 def test_one_direct_retry_no_scaffold_emitted_cloud_or_local(self):
  from unittest.mock import patch
  from jarvis.streaming import StreamTransport
  for cloud in (False,True):
   provider=Provider('test','https://example.invalid/v1'if cloud else'http://127.0.0.1:1234/v1','test',cloud)
   response=io.BytesIO(delta("Here's a thinking process: internal calculation 1907")+b'data: [DONE]\n\n');response.headers={'Content-Type':'text/event-stream'}
   transport=StreamTransport();opener=Mock();opener.open.return_value=response
   with patch.object(transport,'opener',return_value=opener),patch('jarvis.streaming.HttpTransport')as cls:
    cls.return_value.complete.return_value='The answer is 1907.'
    cls.return_value.last_diagnostics=[]
    self.assertEqual(list(transport.stream(provider,[{'role':'user','content':'25 plus1882?'}],'synthetic'if cloud else None)),['The answer is 1907.'])
    cls.return_value.complete.assert_called_once();self.assertIn('Answer the original question directly',cls.return_value.complete.call_args.args[1][-1]['content'])
 def test_repeated_scaffold_failure_has_no_second_retry(self):
  from unittest.mock import patch
  from jarvis.streaming import StreamTransport
  response=io.BytesIO(delta('Thinking process: secret')+b'data: [DONE]\n\n');response.headers={'Content-Type':'text/event-stream'}
  transport=StreamTransport();opener=Mock();opener.open.return_value=response
  with patch.object(transport,'opener',return_value=opener),patch('jarvis.streaming.HttpTransport')as cls:
   cls.return_value.complete.side_effect=ProviderFailure('empty');cls.return_value.last_diagnostics=[]
   with self.assertRaises(ProviderFailure):list(transport.stream(Provider('local','http://127.0.0.1:1234/v1','test'),[{'role':'user','content':'answer'}]))
   self.assertEqual(cls.return_value.complete.call_count,1)
