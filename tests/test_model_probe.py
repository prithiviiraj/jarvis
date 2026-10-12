import unittest,io,json
from unittest.mock import Mock
from jarvis.model_probe import ModelProbe
class Probe(unittest.TestCase):
 def runtime(self):
  r=Mock();r.route.return_value={'url':'http://127.0.0.1:45678/v1','key':'fixture','model':'fixture'};return r
 def test_actual_callback_requests_private_free_synthetic_image(self):
  http=Mock();calls=[]
  def open(req,**kw):
   data=json.loads(req.data);calls.append(data);return io.BytesIO(json.dumps({'choices':[{'message':{'content':'READY'if len(calls)==1 else'red'}}]}).encode())
  http.open.side_effect=open;p=ModelProbe(self.runtime(),http)
  with self.assertRaises(ValueError):p.start()
  p.start(True);p.worker.join(2);self.assertEqual(p.snapshot()['text'],'passed');self.assertEqual(p.snapshot()['image'],'passed');self.assertEqual(len(calls),2);self.assertTrue(calls[1]['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'));self.assertEqual(http.open.call_args.args[0].get_header('Authorization'),'Bearer fixture')
 def test_incorrect_text_never_claims_image_ready(self):
  http=Mock();http.open.return_value=io.BytesIO(json.dumps({'choices':[{'message':{'content':'hello'}}]}).encode());p=ModelProbe(self.runtime(),http);p.start(True);p.worker.join(2);self.assertEqual(p.snapshot()['text'],'failed');self.assertEqual(p.snapshot()['image'],'not tested');self.assertIn('incorrectly',p.snapshot()['error'])

 def test_stop_drops_late_probe_result(self):
  import threading
  entered=threading.Event();release=threading.Event();http=Mock()
  def opening(*a,**k):entered.set();release.wait(1);return io.BytesIO(json.dumps({'choices':[{'message':{'content':'READY'}}]}).encode())
  http.open.side_effect=opening;p=ModelProbe(self.runtime(),http);p.start(True);self.assertTrue(entered.wait(1));p.stop();release.set();p.worker.join(1);self.assertEqual(p.snapshot()['text'],'not tested');self.assertEqual(http.open.call_count,1)
 def test_image_failure_does_not_convert_text_pass_to_vision_pass(self):
  http=Mock();answers=iter(['READY','blue'])
  http.open.side_effect=lambda *a,**k:io.BytesIO(json.dumps({'choices':[{'message':{'content':next(answers)}}]}).encode());p=ModelProbe(self.runtime(),http);p.start(True);p.worker.join(1);self.assertEqual(p.snapshot()['text'],'passed');self.assertEqual(p.snapshot()['image'],'failed');p.stop();self.assertNotIn('text_request_s',p.snapshot())
 def test_owned_route_change_blocks_test(self):
  runtime=self.runtime();http=Mock();n=[0]
  def opening(*a,**k):n[0]+=1;runtime.route.return_value={'url':'http://127.0.0.1:45679/v1','key':'changed','model':'other'};return io.BytesIO(json.dumps({'choices':[{'message':{'content':'READY'}}]}).encode())
  http.open.side_effect=opening;p=ModelProbe(runtime,http);p.start(True);p.worker.join(1);self.assertEqual(p.snapshot()['image'],'failed');self.assertIn('changed',p.snapshot()['error']);self.assertEqual(n[0],1)

 def test_diagnostic_removes_owned_runtime_token_before_artifact(self):
  import pathlib
  source=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/managed-model-proof.py').read_text();self.assertIn("raw.replace(runtime_token,'[owned runtime token removed]')",source)
