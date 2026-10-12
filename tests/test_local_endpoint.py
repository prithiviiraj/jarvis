import unittest
from unittest.mock import Mock
from jarvis.local_endpoint import bind,unbind,managed_route
from jarvis.providers import configured,local_models,local_live_models
class Endpoints(unittest.TestCase):
 def setUp(self):self.runtime=Mock();self.runtime.route.return_value={'url':'http://127.0.0.1:43210/v1','key':'ephemeral','model':'qwen3-vl-4b'};bind(self.runtime)
 def tearDown(self):unbind(self.runtime)
 def test_managed_provider_and_metadata(self):
  p=configured('local','automatic');self.assertEqual(p.url,'http://127.0.0.1:43210/v1');self.assertEqual(p.local_key,'ephemeral');self.assertEqual(local_models(),['qwen3-vl-4b']);self.assertTrue(local_live_models()[0]['vision'])
 def test_does_not_silently_select_wrong_model(self):
  with self.assertRaises(ValueError):configured('local','some-other-model')
 def test_off_runtime_never_falls_back(self):
  self.runtime.route.side_effect=ValueError('Off')
  with self.assertRaises(ValueError):local_models()
  with self.assertRaises(ValueError):configured('local','automatic')
 def test_other_owner_and_wrong_unbind(self):
  with self.assertRaises(ValueError):bind(Mock())
  unbind(Mock());self.assertIsNotNone(managed_route())
 def test_local_token_passed_to_actual_transport(self):
  from jarvis.router import BrainRouter
  transport=Mock();transport.complete.return_value='hello';router=BrainRouter([configured('local','automatic')],transport);router.ask([{'role':'user','content':'hi'}]);self.assertEqual(transport.complete.call_args.args[2],'ephemeral')

 def test_stream_token_passed_to_actual_transport(self):
  from jarvis.router import BrainRouter
  transport=Mock();transport.stream.return_value=iter(['hello']);router=BrainRouter([configured('local','automatic')]);list(router.stream([{'role':'user','content':'hi'}],stream_transport=transport));self.assertEqual(transport.stream.call_args.args[2],'ephemeral')

 def test_vision_uses_owned_discovery(self):
  from jarvis.vision import LocalVision
  v=LocalVision(lambda:None);self.assertEqual(v.vision_model(),'qwen3-vl-4b')
 def test_game_actual_callback_owned_route(self):
  import io,json
  from jarvis.game_companion import LocalGameModel
  body=json.dumps({'choices':[{'message':{'content':json.dumps({'observed':'window','comment':'visible window','confidence':'medium'})}}]}).encode();http=Mock();http.open.side_effect=lambda req,**kw:io.BytesIO(body)
  model=LocalGameModel('qwen3-vl-4b',opener=http);result=model.analyze(b'image');self.assertEqual(result['observed'],'window');req=http.open.call_args.args[0];self.assertEqual(req.full_url,'http://127.0.0.1:43210/v1/chat/completions');self.assertEqual(req.get_header('Authorization'),'Bearer ephemeral')

 def test_local_token_not_in_provider_display(self):
  self.assertNotIn('ephemeral',repr(configured('local','automatic')))

 def test_large_owned_model_not_labeled_tiny(self):
  from jarvis.tiny_specialists import Specialists
  http=Mock();s=Specialists(opener=http);self.assertEqual(s.metadata(),[]);http.open.assert_not_called()
 def test_catalog_in_both_frozen_packages(self):
  import pathlib
  root=pathlib.Path(__file__).resolve().parents[1]
  for name in ('package-windows.py','package-native-diagnostic.py'):self.assertIn('src/jarvis/chat-assets.json',(root/'modern-ui'/name).read_text())
 def test_actual_http_transport_carries_owned_token(self):
  import io,json
  from jarvis.router import HttpTransport
  class Response(io.BytesIO):headers={'Content-Type':'application/json'}
  transport=HttpTransport();transport.http=Mock();transport.http.open.side_effect=lambda req,**kw:Response(json.dumps({'choices':[{'message':{'content':'hello'}}]}).encode())
  from jarvis.router import BrainRouter
  answer=BrainRouter([configured('local','automatic')],transport).ask([{'role':'user','content':'hi'}]);self.assertEqual(answer['text'],'hello');req=transport.http.open.call_args.args[0];self.assertEqual(req.get_header('Authorization'),'Bearer ephemeral');self.assertEqual(req.full_url,'http://127.0.0.1:43210/v1/chat/completions')
