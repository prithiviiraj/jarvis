import unittest
from jarvis.changed_image_latency import grade,frame,ImageProfile,CASES
class ChangedImage(unittest.TestCase):
 def test_exact_sides(self):
  self.assertTrue(grade('{"left":{"label":"A17","color":"red"},"right":{"label":"B29","color":"blue"}}',CASES[0]))
  self.assertFalse(grade('{"left":{"label":"B29","color":"blue"},"right":{"label":"A17","color":"red"}}',CASES[0]))
  self.assertFalse(grade('A17 B29 red blue',CASES[0]))
 def test_fixture(self):
  from PIL import Image
  import io
  for width in (1024,960):self.assertEqual(Image.open(io.BytesIO(frame(CASES[0],width))).size,(width,width*640//1024))
  self.assertNotEqual(frame(CASES[0]),frame(CASES[1]))
 def test_bounds(self):
  with self.assertRaises(ValueError):ImageProfile(640)
