import threading,unittest
from unittest.mock import Mock,patch
from jarvis.vision import LocalVision,GuardedVisionRouter
class Revocation(unittest.TestCase):
 def vision(self):
  v=LocalVision(lambda:b'camera');v.vision_model=Mock(return_value='fixture');return v
 def test_stop_during_screen_capture_discards(self):
  v=self.vision();entered=threading.Event();release=threading.Event();errors=[]
  def capture():entered.set();release.wait(2);return b'screen'
  v.enable_screen(capture,True)
  def run():
   try:v.attach([{'role':'user','content':'see screen'}])
   except RuntimeError as e:errors.append(str(e))
  t=threading.Thread(target=run);t.start();self.assertTrue(entered.wait(1));v.disable_screen();release.set();t.join(2);self.assertEqual(len(errors),1);self.assertIn('discarded',errors[0])
 def test_stop_during_camera_capture_discards(self):
  v=self.vision();v.enable(True)
  def source():v.disable();return b'camera'
  v.frame_source=source
  with self.assertRaisesRegex(RuntimeError,'discarded'):v.attach([{'role':'user','content':'see me'}])
 def test_stop_after_attach_before_route_no_model(self):
  v=self.vision();v.enable(True);m=v.attach([{'role':'user','content':'see me'}]);v.disable();v.vision_model.reset_mock()
  with self.assertRaises(RuntimeError):v.route(Mock(),m)
  v.vision_model.assert_not_called()
 def test_stop_during_model_check_no_router(self):
  v=self.vision();v.enable(True);m=v.attach([{'role':'user','content':'see me'}])
  def check():v.disable();return 'fixture'
  v.vision_model=check
  with patch('jarvis.router.BrainRouter')as router:
   with self.assertRaises(RuntimeError):v.route(Mock(),m)
   router.assert_not_called()
 def test_stop_after_route_before_send(self):
  v=self.vision();router=Mock();g=GuardedVisionRouter(v,router,v.generation);v.disable()
  with self.assertRaises(RuntimeError):g.ask([])
  with self.assertRaises(RuntimeError):list(g.stream([]))
  router.ask.assert_not_called();router.stream.assert_not_called()
 def test_old_reply_and_stream_not_exposed_after_stop(self):
  v=self.vision();router=Mock();g=GuardedVisionRouter(v,router,v.generation)
  def ask(*a,**kw):v.disable();return {'text':'old'}
  router.ask=ask
  with self.assertRaises(RuntimeError):g.ask([])
  g=GuardedVisionRouter(v,router,v.generation)
  def stream(*a,**kw):yield {'text':'before'};v.disable();yield {'text':'old'}
  class Streaming:
   def stream(self,*a,**kw):return stream(*a,**kw)
  g=GuardedVisionRouter(v,Streaming(),v.generation);it=g.stream([]);self.assertEqual(next(it),{'text':'before'})
  with self.assertRaises(RuntimeError):next(it)

 def test_stop_during_enable_not_reenabled(self):
  v=self.vision()
  def check():v.disable_screen();return 'fixture'
  v.vision_model=check
  with self.assertRaises(RuntimeError):v.enable_screen(lambda:b'old',True)
  self.assertFalse(v.screen_enabled)
