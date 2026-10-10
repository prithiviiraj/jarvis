import io,unittest
from unittest.mock import patch,Mock
from PIL import Image
from jarvis.game_companion import encode_frame,capture
class QuestionFrame(unittest.TestCase):
 def test_question_larger_background_unchanged(self):
  source=Image.new('RGB',(1920,1080),'white')
  q=encode_frame(source,True);b=encode_frame(source,False)
  self.assertEqual(Image.open(io.BytesIO(q)).size,(1280,720));self.assertEqual(Image.open(io.BytesIO(b)).size,(640,360));self.assertLessEqual(len(q),300000);self.assertLessEqual(len(b),200000)
 def test_no_upscale_and_portrait_bounds(self):
  self.assertEqual(Image.open(io.BytesIO(encode_frame(Image.new('RGB',(300,200)),True))).size,(300,200))
  im=Image.open(io.BytesIO(encode_frame(Image.new('RGB',(1080,1920)),True)));self.assertLessEqual(im.width,1280);self.assertEqual(im.height,720)
 def test_full_primary_read_path_uses_question_bounds(self):
  with patch('jarvis.game_companion.os.name','nt'),patch('ctypes.windll',Mock(),create=True),patch('PIL.ImageGrab.grab',return_value=Image.new('RGB',(1920,1080)))as grab:
   out=capture({'id':1,'title':'Full primary laptop screen'},question=True)
  grab.assert_called_once_with(all_screens=False);self.assertEqual(Image.open(io.BytesIO(out)).size,(1280,720))
 def test_bounded_noise_uses_lower_quality_or_fails_closed(self):
  import random
  im=Image.frombytes('RGB',(1280,720),random.Random(0).randbytes(1280*720*3));out=encode_frame(im,True)
  self.assertTrue(out is None or len(out)<=300000)
