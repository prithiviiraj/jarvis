import unittest,threading
from unittest.mock import Mock
from jarvis.lmstudio_rest import SparkRecoveryTransport
from jarvis.router import Provider,ProviderFailure
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.p=Provider('local','http://127.0.0.1:1234/v1','spark-x2.5-4b');self.r=Mock();self.n=Mock();self.r.last_diagnostics=[{'response_category':'reasoning_without_final_text','reasoning_chars':3585}];self.n.last_diagnostics=[{'reasoning_requested':'off','recognized_text_chars':6}];self.notify=Mock();self.t=SparkRecoveryTransport(self.r,self.n,self.notify);self.messages=[{'role':'user','content':'hi'}]
 def fail(self,code='reasoning-token-limit',partial=False):
  def it(*a,**k):
   if partial:yield 'Partial'
   raise ProviderFailure(code,False)
  self.r.stream.side_effect=it
 def test_reasoning_only_recovered_once_same_local_input(self):
  self.fail();self.n.stream.return_value=iter(['Hello.']);self.assertEqual(list(self.t.stream(self.p,self.messages)),['Hello.']);self.n.stream.assert_called_once_with(self.p,self.messages,None,None);self.notify.assert_called_once();self.assertEqual(len(self.t.last_diagnostics),2)
 def test_unsupported_no_on_fallback(self):
  self.fail();self.n.stream.side_effect=ProviderFailure('native-reasoning-off-unavailable',False)
  with self.assertRaisesRegex(ProviderFailure,'native-reasoning-off-unavailable'):list(self.t.stream(self.p,self.messages))
  self.assertEqual(self.r.stream.call_count,1);self.assertEqual(self.n.stream.call_count,1)
 def test_partial_no_retry(self):
  self.fail(partial=True)
  with self.assertRaises(ProviderFailure):list(self.t.stream(self.p,self.messages))
  self.n.stream.assert_not_called()
 def test_other_error_no_retry(self):
  self.fail('http-503')
  with self.assertRaises(ProviderFailure):list(self.t.stream(self.p,self.messages))
  self.n.stream.assert_not_called()
 def test_other_model_no_retry(self):
  self.fail()
  with self.assertRaises(ProviderFailure):list(self.t.stream(Provider('local',self.p.url,'qwen'),self.messages))
  self.n.stream.assert_not_called()
 def test_cancel_no_retry(self):
  self.fail();c=threading.Event();c.set()
  with self.assertRaises(ProviderFailure):list(self.t.stream(self.p,self.messages,cancel=c))
  self.n.stream.assert_not_called()
 def test_regular_success_unchanged(self):
  self.r.stream.return_value=iter(['Answer.']);self.assertEqual(list(self.t.stream(self.p,self.messages)),['Answer.']);self.n.stream.assert_not_called()
