import unittest,io,json
from jarvis.final_text import FinalTextFilter,final_text
from jarvis.streaming import text_deltas,StreamTransport
from jarvis.router import BrainRouter,Provider,ProviderFailure,RouterError
from jarvis.team_memory import TeamMemory
from unittest.mock import Mock
class FinalTextTests(unittest.TestCase):
 def test_split_markers(self):
  f=FinalTextFilter();out=''.join(f.feed(x)for x in ['<th','ink>secret','</thi','nk>Answer']);self.assertEqual(out+f.finish(),'Answer')
 def test_unclosed_thinking(self):self.assertEqual(final_text('<think>secret'),'')
 def test_reasoning_length(self):
  raw=b'data: {"choices":[{"delta":{"content":"<think>secret"},"finish_reason":"length"}]}\n\n'
  with self.assertRaisesRegex(ProviderFailure,'reasoning-token-limit'):list(text_deltas(io.BytesIO(raw)))
 def test_same_packet_length_final_retained(self):
  raw=b'data: {"choices":[{"delta":{"content":"A final answer"},"finish_reason":"length"}]}\n\n';self.assertEqual(list(text_deltas(io.BytesIO(raw))),['A final answer'])
 def test_textparts_thinking_hidden(self):
  from jarvis.chat_payload import answer_text
  self.assertEqual(answer_text([{'type':'text','text':'<think>secret</think>Final'}]),'Final')
 def test_spark_bounded_budget(self):
  from jarvis.chat_payload import payload
  self.assertEqual(payload('spark-x2.5-4b',[{}])['max_tokens'],1024)
 def test_prefix_once(self):
  m=TeamMemory();m.append('JARVIS','hi','[JARVIS] [JARVIS] Hello');self.assertEqual(m.messages()[1]['content'],'[JARVIS] Hello')
 def test_local_budget_failure_next_turn(self):
  t=Mock();t.stream.side_effect=[ProviderFailure('completion-token-limit',False),iter(['Hello'])];r=BrainRouter([Provider('local','http://127.0.0.1:1234/v1','test')])
  with self.assertRaises(RouterError):list(r.stream([{}],stream_transport=t))
  self.assertEqual(list(r.stream([{}],stream_transport=t))[0]['text'],'Hello')
 def test_observed_untagged_scaffold_never_streams(self):
  leak="Here's a thinking process:\n1. **Analyze User Input**: DEX you are also here right.\n2. **Check Constraints**: private instructions"
  for size in (1,2,5,25,1000):
   f=FinalTextFilter();out=''.join(f.feed(leak[i:i+size])for i in range(0,len(leak),size))+f.finish();self.assertEqual(out,'');self.assertTrue(f.suppressed)
 def test_legitimate_numbered_answer_preserved(self):
  self.assertEqual(final_text('1. Open Settings. 2. Stop Mic.'),'1. Open Settings. 2. Stop Mic.')
  self.assertEqual(final_text("Here's a useful answer: yes."),"Here's a useful answer: yes.")
