import unittest
from unittest.mock import Mock
from jarvis.router import Provider,BrainRouter,ProviderFailure,RouterError
class RouterTests(unittest.TestCase):
 def setUp(self):
  self.local=Provider('local','http://127.0.0.1:1234/v1','test')
  self.cloud=Provider('gemini','https://example.invalid/v1','test',True)
  self.t=Mock();self.keys=Mock();self.keys.get.return_value='synthetic-test';self.now=0
  self.r=BrainRouter([self.local,self.cloud],self.t,self.keys,lambda:self.now)
 def test_local_default(self):
  self.t.complete.return_value='hello';self.assertFalse(self.r.ask([{}])['cloud']);self.keys.get.assert_not_called()
 def test_no_cloud_without_consent(self):
  self.t.complete.side_effect=ProviderFailure('connection')
  with self.assertRaises(RouterError):self.r.ask([{}])
  self.assertEqual(self.t.complete.call_count,1)
 def test_failover_with_consent(self):
  self.t.complete.side_effect=[ProviderFailure('http-429'),'ok'];j=self.r.ask([{}],True);self.assertEqual(j['provider'],'gemini');self.assertEqual(j['fallbacks'],[('local','http-429')])
 def test_circuit_breaker(self):
  self.t.complete.side_effect=[ProviderFailure('connection'),'ok','ok'];self.r.ask([{}],True);self.r.ask([{}],True);self.assertEqual(self.t.complete.call_count,3)
 def test_circuit_recovers(self):
  self.t.complete.side_effect=ProviderFailure('connection')
  with self.assertRaises(RouterError):self.r.ask([{}])
  self.now=61;self.t.complete.side_effect=None;self.t.complete.return_value='ok';self.assertEqual(self.r.ask([{}])['provider'],'local')
 def test_images_separate_permission(self):
  self.r=BrainRouter([self.cloud],self.t,self.keys)
  with self.assertRaises(RouterError):self.r.ask([{}],True,contains_image=True)
  self.t.complete.assert_not_called()
 def test_key_missing_skips(self):
  self.keys.get.return_value=None;self.r=BrainRouter([self.cloud],self.t,self.keys)
  with self.assertRaises(RouterError):self.r.ask([{}],True)
  self.t.complete.assert_not_called()
 def test_reorder(self):
  self.r.reorder(['gemini','local']);self.assertEqual(self.r.providers[0].name,'gemini')
  with self.assertRaises(ValueError):self.r.reorder(['local','local'])
 def test_url_validation(self):
  for u in ['http://example.com/v1','https://user:pass@example.com/v1','https://example.com/v1?key=oops']:
   with self.assertRaises(ValueError):Provider('x',u,'m',True)

class CancelTests(unittest.TestCase):
 def test_cancel_before_transport_and_after_reply(self):
  import threading
  cancel=threading.Event();transport=Mock();router=BrainRouter([Provider('local','http://127.0.0.1:1234/v1','fixture')],transport);cancel.set()
  with self.assertRaisesRegex(RouterError,'stopped'):router.ask([{}],cancel=cancel)
  transport.complete.assert_not_called();cancel.clear()
  def reply(*a):cancel.set();return 'late'
  transport.complete.side_effect=reply
  with self.assertRaisesRegex(RouterError,'stopped'):router.ask([{}],cancel=cancel)
 def test_failure_after_cancel_does_not_start_fallback(self):
  import threading
  cancel=threading.Event();transport=Mock();router=BrainRouter([Provider('local','http://127.0.0.1:1234/v1','first'),Provider('other','http://127.0.0.1:1235/v1','second')],transport)
  def fail(*a):cancel.set();raise ProviderFailure('connection')
  transport.complete.side_effect=fail
  with self.assertRaisesRegex(RouterError,'stopped'):router.ask([{}],cancel=cancel)
  self.assertEqual(transport.complete.call_count,1)
 def test_actual_default_source_and_switch_callbacks_accept_cancel(self):
  import threading
  from unittest.mock import patch
  from jarvis.source_answer import SourceAnswer
  from jarvis.brain_switch import BrainSwitch
  from jarvis.brain_settings import BrainSettings
  with patch('jarvis.router.HttpTransport.complete',return_value='Synthetic local reply')as call:
   cancel=threading.Event();source=SourceAnswer(threading.Lock());r=source._generate('synthetic-local','Question',{'name':'fixture.md','text':'Synthetic evidence','truncated':False},cancel);self.assertFalse(r['cloud']);self.assertEqual(r['model'],'synthetic-local');switch=BrainSwitch(BrainSettings());r=switch._probe('synthetic-local',cancel);self.assertFalse(r['cloud']);self.assertEqual(call.call_count,2)
