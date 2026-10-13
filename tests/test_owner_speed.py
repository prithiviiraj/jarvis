import unittest
from unittest.mock import patch
from jarvis.owner_speed import installed,run
class OwnerSpeed(unittest.TestCase):
 def test_no_consent(self):
  with self.assertRaises(ValueError):run()
 def test_missing_no_download(self):
  with patch('jarvis.owner_speed.verified',return_value=False):self.assertEqual(installed('/tmp/none'),[])
 def test_only_verified(self):
  with patch('jarvis.owner_speed.verified',return_value=True):self.assertGreater(len(installed('/tmp/none')),1)
