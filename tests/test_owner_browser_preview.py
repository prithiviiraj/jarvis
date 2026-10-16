import base64,io,unittest,threading
from unittest.mock import Mock
from PIL import Image
from jarvis.browseros_transport import BrowserOSNavigation
from jarvis.browseros_controller import BrowserOSController
class BrowserPreview(unittest.TestCase):
 def image(self):
  out=io.BytesIO();Image.new('RGB',(320,200),'#e9e2da').save(out,format='JPEG');return base64.b64encode(out.getvalue()).decode()
 def test_only_real_jpeg_of_owned_page_with_fixed_read_only_capture(self):
  v=BrowserOSNavigation('http://127.0.0.1:9200/mcp');v._tool=Mock()
  v._capture_foreground=lambda:None  # Windows-only owned-process focus; this contract is the real JPEG capture shape
  with self.assertRaises(RuntimeError):v.screenshot()
  v.owned_page=7;v._tool.return_value={'content':[{'type':'image','data':self.image(),'mimeType':'image/jpeg'}]};self.assertTrue(v.screenshot()['data_url'].startswith('data:image/jpeg;base64,'));v._tool.assert_called_once_with('screenshot',{'page':7,'format':'jpeg','quality':65,'size':{'width':960,'height':600},'fullPage':False,'annotate':False})
  for image in [{'type':'image','data':'bm90IGFuIGltYWdl','mimeType':'image/jpeg'},{'type':'image','data':self.image(),'mimeType':'image/svg+xml'}]:
   v._tool.return_value={'content':[image]}
   with self.assertRaises(RuntimeError):v.screenshot()
 def test_capture_failure_does_not_invent_image_or_erase_verified_navigation(self):
  c=Mock();c.connect.return_value={'tools':[]};c.open_blank.return_value={'url':'about:blank'};c.screenshot.side_effect=RuntimeError('capture unavailable');v=BrowserOSController(lambda _:c);v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);v.start().join(2);self.assertEqual(v.state,'connected');self.assertEqual(v.url,'about:blank');self.assertIsNone(v.preview);self.assertIn('unavailable',v.preview_error);self.assertEqual(v.drain_events()[0]['kind'],'browser-tab-ready');v.stop().join(2)
 def test_stop_discards_delayed_preview_and_never_replays_old_page(self):
  entered=threading.Event();release=threading.Event();c=Mock();c.connect.return_value={'tools':[]};c.open_blank.return_value={'url':'about:blank'}
  def capture():entered.set();release.wait(2);return {'page':7,'data_url':'data:image/jpeg;base64,'+self.image()}
  c.screenshot.side_effect=capture;v=BrowserOSController(lambda _:c);v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);worker=v.start();self.assertTrue(entered.wait(1));v.stop().join(2);release.set();worker.join(2);self.assertIsNone(v.preview);self.assertEqual(v.url,'');self.assertEqual(v.drain_events(),[])
 def test_cancelled_navigation_never_captures_another_reconnected_client(self):
  entered=threading.Event();release=threading.Event();first=Mock();second=Mock();first.connect.return_value=second.connect.return_value={'tools':[]};clients=iter([first,second]);first.open_blank.side_effect=lambda *a:(entered.set(),release.wait(2),{'url':'about:blank'})[-1];v=BrowserOSController(lambda _:next(clients));v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);worker=v.start();self.assertTrue(entered.wait(1));v.stop().join(2);v.connect('http://127.0.0.1:9201/mcp',True,True).join(2);release.set();worker.join(2);first.screenshot.assert_not_called();second.screenshot.assert_not_called();self.assertIsNone(v.preview);self.assertEqual(v.url,'');v.stop().join(2)
