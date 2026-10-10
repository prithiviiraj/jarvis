import unittest
from unittest.mock import Mock
from jarvis.router import BrainRouter,RouterError
from jarvis.providers import configured
from jarvis.vision import LocalVision
from test_vision import opener,VISION
class LocalImageGate(unittest.TestCase):
 def test_image_cannot_use_cloud_even_with_cloud_image_flags(self):
  transport=Mock();r=BrainRouter([configured('gemini','test')],transport=transport,key_store=Mock())
  message=[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,eA=='}}]}]
  with self.assertRaises(RouterError):r.ask(message,cloud_consent=True,cloud_image_consent=True)
  with self.assertRaises(RouterError):list(r.stream(message,cloud_consent=True))
  transport.complete.assert_not_called()
 def test_camera_and_screen_exact_current_frames_local_route(self):
  v=LocalVision(lambda:b'camera',opener=opener(VISION));v.enable(True);v.enable_screen(lambda:b'screen',True)
  messages=v.attach([{'role':'user','content':'what do you see'}]);images=[p for p in messages[-1]['content']if p['type']=='image_url'];self.assertEqual(len(images),2)
  route=v.route(Mock(),messages);self.assertEqual(route.providers[0].model,VISION[0]['loaded_instances'][0]['id']);self.assertFalse(route.providers[0].cloud)
  v.disable_screen();self.assertEqual(len([p for p in v.attach([{'role':'user','content':'hi'}])[-1]['content']if p['type']=='image_url']),1)
 def test_actual_mic_turn_cloud_router_bypassed_for_screen_pixels(self):
  import threading
  from unittest.mock import patch
  from jarvis.runtime import VoiceRuntime
  v=LocalVision(lambda:None,opener=opener(VISION));v.enable_screen(lambda:b'screen',True)
  original=Mock();local=Mock();local.ask.return_value={'text':'Current local frame fixture reply'}
  stt=Mock();stt.transcribe.return_value='what is on my screen';speaker=Mock();speaker.generation=0
  r=VoiceRuntime(Mock(),stt,original,speaker);r.mic=Mock();r.vision=v;r.enable(True,True)
  with patch('jarvis.router.BrainRouter',return_value=local)as factory:r.turn([],r.generation,True,[])
  original.ask.assert_not_called();original.stream.assert_not_called();self.assertFalse(factory.call_args.args[0][0].cloud)
  self.assertFalse(local.ask.call_args.kwargs['cloud_consent']);self.assertTrue(any(p['type']=='image_url'for p in local.ask.call_args.args[0][-1]['content']));speaker.speak.assert_called_once()

 def test_actual_team_turn_uses_local_images_not_configured_cloud(self):
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import patch
  v=WorkspaceVoice();vision=LocalVision(lambda:b'camera',opener=opener(VISION));vision.enable(True);v.vision=vision
  class Local:
   def ask(self,messages,**kw):
    self.seen=messages;return {'text':'Current local image fixture reply'}
  local=Local();brains=Mock()
  with patch('jarvis.router.BrainRouter',return_value=local):v.dialogue('Lyra talk to Dex about what you see',brains).join(2)
  self.assertTrue(any(p['type']=='image_url'for p in local.seen[-1]['content']));brains.router.return_value.ask.assert_not_called();v.close()
