import unittest,io
from jarvis.scene_sampling import SceneSampler
class SceneSamplingTests(unittest.TestCase):
 def frame(self,color,comment=''):
  try:from PIL import Image
  except ImportError:self.skipTest('Pillow required for pixel comparison')
  stream=io.BytesIO();Image.new('RGB',(80,60),(color,color,color)).save(stream,format='JPEG',comment=comment.encode());return stream.getvalue()
 def test_rate_budget_and_change(self):
  s=SceneSampler();self.assertTrue(s.consider(self.frame(0),0)[0]);self.assertFalse(s.consider(self.frame(255),1)[0]);self.assertTrue(s.consider(self.frame(255),2)[0])
 def test_tiny_changes_skip_until_keyframe(self):
  s=SceneSampler();s.consider(self.frame(100),0);self.assertEqual(s.consider(self.frame(102),3),(False,'small visual change'));self.assertEqual(s.consider(self.frame(102),12),(True,'keyframe'))
 def test_unchanged_never_spends_again(self):
  s=SceneSampler();f=self.frame(120);s.consider(f,0);self.assertFalse(s.consider(f,100)[0]);s.reset();self.assertTrue(s.consider(f,101)[0])
 def test_no_image_dependency_fallback_still_bounded(self):
  s=SceneSampler();self.assertTrue(s.consider(b'fixture-a',0)[0]);self.assertFalse(s.consider(b'fixture-b',1)[0]);self.assertTrue(s.consider(b'fixture-b',3)[0])
