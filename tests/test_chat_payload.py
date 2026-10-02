import unittest,io,json
from jarvis.chat_payload import payload,reply_metadata
from jarvis.streaming import text_deltas
from jarvis.router import ProviderFailure
class PayloadTests(unittest.TestCase):
 def test_oss_reasoning_bounded_hidden(self):
  p=payload('openai/gpt-oss-20b',[{'role':'user','content':'hi'}]);self.assertEqual(p['max_completion_tokens'],1024);self.assertEqual(p['reasoning_effort'],'low');self.assertFalse(p['include_reasoning']);self.assertNotIn('reasoning_format',p);self.assertNotIn('max_tokens',p)
 def test_other_model_unchanged(self):self.assertEqual(payload('local',[{}])['max_tokens'],300)
 def test_metadata_redacted(self):
  data={'choices':[{'message':{'reasoning':'SECRET'},'finish_reason':'length'}],'usage':{'completion_tokens':32,'completion_tokens_details':{'reasoning_tokens':32}}};r=reply_metadata(data);self.assertEqual(r['finish_category'],'length');self.assertNotIn('SECRET',str(r))
 def test_stream_reasoning_never_answer(self):
  data=[{'choices':[{'delta':{'reasoning':'SECRET'}}]},{'choices':[{'delta':{'content':'Hello.'}}]}];b=''.join('data: '+json.dumps(x)+'\n\n' for x in data).encode();self.assertEqual(list(text_deltas(io.BytesIO(b))),['Hello.'])
 def test_stream_token_limit_explicit(self):
  with self.assertRaises(ProviderFailure):list(text_deltas(io.BytesIO(b'data: {"choices":[{"delta":{},"finish_reason":"length"}]}\n')))
