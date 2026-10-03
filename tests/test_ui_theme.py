import unittest
from unittest.mock import Mock
from jarvis.ui_theme import mix,glass
class ThemeTests(unittest.TestCase):
 def test_mix_limits(self):self.assertEqual(mix('#000000','#ffffff',0),'#000000');self.assertEqual(mix('#000000','#ffffff',1),'#ffffff');self.assertEqual(mix('#000000','#ffffff',.5),'#808080')
 def test_alpha(self):
  w=Mock();self.assertTrue(glass(w));w.attributes.assert_called_once_with('-alpha',.97)
 def test_opaque_fallback(self):
  w=Mock();w.attributes.side_effect=RuntimeError();self.assertFalse(glass(w))
