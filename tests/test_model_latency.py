import unittest,io,json,threading
from unittest.mock import Mock
from jarvis.model_latency import ModelLatency
class Tests(unittest.TestCase):
 def setUp(self):
  self.runtime=Mock();self.runtime.route.return_value={'url':'http://127.0.0.1:43210/v1','key':'fixture-token','model':'fixture'};self.http=Mock()
  body=b'data: '+json.dumps({'choices':[{'delta':{'content':'Synthetic answer'}}]}).encode()+b'\n\ndata: [DONE]\n'
  self.http.open.side_effect=lambda *a,**k:io.BytesIO(body);self.test=ModelLatency(self.runtime,self.http)
 def test_exact_six_requests_local_synthetic_no_private_capture(self):
  out=self.test.run(True);self.assertEqual(len(out['rows']),6);self.assertEqual(self.http.open.call_count,6)
  payload=json.loads(self.http.open.call_args.args[0].data);self.assertTrue(payload['stream']);self.assertEqual(payload['max_tokens'],96);self.assertIn('data:image/png;base64,',payload['messages'][0]['content'][1]['image_url']['url'])
 def test_requires_review(self):
  with self.assertRaises(ValueError):self.test.run()
  self.http.open.assert_not_called()
 def test_cancel_before_send(self):
  cancel=threading.Event();cancel.set()
  with self.assertRaises(InterruptedError):self.test.run(True,cancel)
  self.http.open.assert_not_called()
 def test_route_revoked_before_send(self):
  self.runtime.route.side_effect=[self.runtime.route.return_value,ValueError('Stopped')]
  with self.assertRaises(ValueError):self.test.run(True)
  self.http.open.assert_not_called()
 def test_route_changed_before_reply_rejected(self):
  route=self.runtime.route.return_value;self.runtime.route.side_effect=[route,route,{**route,'key':'changed'}]
  with self.assertRaises(ValueError):self.test.run(True)
 def test_empty_stream_is_not_latency_success(self):
  self.http.open.side_effect=lambda *a,**k:io.BytesIO(b'data: [DONE]\n')
  with self.assertRaises(ValueError):self.test.run(True)
 def test_completed_rows_retained_on_later_image_timeout(self):
  body=b'data: '+json.dumps({'choices':[{'delta':{'content':'answer'}}]}).encode()+b'\n\ndata: [DONE]\n'
  count=[0]
  def open_request(*args,**kwargs):
   count[0]+=1
   if count[0]==4:raise TimeoutError('fixture image timeout')
   return io.BytesIO(body)
  self.http.open.side_effect=open_request
  with self.assertRaises(TimeoutError):self.test.run(True)
  self.assertEqual(len(self.test.rows),3);self.assertEqual(self.test.current['kind'],'image');self.assertEqual(self.test.current['diagnostic_timeout_s'],120)
