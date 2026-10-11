import unittest
from unittest.mock import Mock
from jarvis.cloud_vision import CloudVision,LocalFirstVision
from jarvis.provider_pool import Slot
class CloudVisionTests(unittest.TestCase):
 def setUp(self):
  self.brains=Mock();self.brains.rows={'slot1':Slot('slot1','groq','text','test')};self.brains.consent={'slot1'};self.brains.free={'slot1'};self.brains.keys.return_value.get.return_value='fixture-not-secret';self.transport=Mock();self.transport.complete.return_value='Visible evidence';self.c=CloudVision(self.brains,self.transport)
 def test_default_off(self):
  with self.assertRaises(ValueError):self.c.ask([])
  self.transport.complete.assert_not_called()
 def test_no_unreviewed_enable(self):
  with self.assertRaises(ValueError):self.c.enable('slot1','qwen/qwen3.8-27b')
 def test_unsupported_text_model(self):
  with self.assertRaisesRegex(ValueError,'text models'):self.c.enable('slot1','text',True)
 def test_only_current_question_and_images_leave(self):
  self.c.enabled=True;self.c.slot='slot1';self.c.model='qwen/qwen3.8-27b';current={'role':'user','content':[{'type':'text','text':'What is visible?'},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,fixture'}}]}
  result=self.c.ask([{'role':'system','content':'private context'},{'role':'user','content':'private history'},current]);self.assertTrue(result['cloud']);out=self.transport.complete.call_args.args[1];self.assertNotIn('private',str(out));self.assertEqual(out[-1],current)
 def test_local_success_never_cloud(self):
  self.c.enabled=True;local=Mock();local.ask.return_value={'text':'local'};vision=Mock();vision.generation=4;route=LocalFirstVision(local,self.c,vision,4);self.assertEqual(route.ask([]),{'text':'local'});self.transport.complete.assert_not_called()
 def test_revoke_blocks_fallback(self):
  vision=Mock();vision.generation=5;route=LocalFirstVision(None,self.c,vision,4)
  with self.assertRaisesRegex(RuntimeError,'changed'):route.ask([])
  self.transport.complete.assert_not_called()
 def test_bridge_specific_consent_command(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice());self.addCleanup(b.close);b.cloud_vision.enable=Mock()
  b.execute({'command':'cloud-vision','enabled':True,'consent':True,'slot':'slot1','vision_model':'qwen/qwen3.8-27b'});b.cloud_vision.enable.assert_called_once_with('slot1','qwen/qwen3.8-27b',True)
  b.cloud_vision.enabled=True;b.execute({'command':'pause'});self.assertFalse(b.cloud_vision.enabled)
 def test_missing_local_with_explicit_cloud_captures_both_current_frames(self):
  from jarvis.vision import LocalVision
  v=LocalVision(lambda:b'camera');v.vision_model=Mock(side_effect=RuntimeError('local absent'));v.cloud=self.c;self.c.enabled=True;self.c.slot='slot1';self.c.model='qwen/qwen3.8-27b'
  v.enable(True);v.enable_screen(lambda:b'screen',True);messages=v.attach([{'role':'user','content':'Explain these two views'}]);self.assertEqual(sum(p['type']=='image_url'for p in messages[-1]['content']),2);result=v.route(None,messages).ask(messages);self.assertEqual(result['provider'],'groq-vision');v.disable_screen()
  with self.assertRaises(RuntimeError):v.route(None,messages)

 def test_revoke_during_current_account_lookup_cannot_enable(self):
  from unittest.mock import patch
  def models(*args):self.c.disable();return ['qwen/qwen3.8-27b']
  with patch('jarvis.brain_settings.account_models',side_effect=models):
   with self.assertRaisesRegex(ValueError,'changed'):self.c.enable('slot1','qwen/qwen3.8-27b',True)
  self.assertFalse(self.c.enabled)
 def test_revoked_account_never_dispatches(self):
  self.c.enabled=True;self.c.slot='slot1';self.c.model='qwen/qwen3.8-27b';self.brains.free.clear()
  with self.assertRaises(ValueError):self.c.ask([{'role':'user','content':[]}])
  self.transport.complete.assert_not_called()

 def test_private_local_context_never_falls_back(self):
  self.c.enabled=True;self.c.slot='slot1';self.c.model='qwen/qwen3.8-27b';local=Mock();local.ask.side_effect=RuntimeError('local failure');vision=Mock();vision.generation=7;route=LocalFirstVision(local,self.c,vision,7)
  with self.assertRaisesRegex(RuntimeError,'Private local-context'):route.ask([{'role':'user','content':[]}],local_only=True)
  self.transport.complete.assert_not_called()

 def test_capture_only_never_calls_cloud(self):
  from jarvis.cloud_vision import CaptureOnly
  m=CaptureOnly();m.verify();row=m.analyze(b'frame');self.assertEqual(row['confidence'],'low');self.assertEqual(row['comment'],'');self.transport.complete.assert_not_called()
