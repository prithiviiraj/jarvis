import unittest,time
from unittest.mock import patch
from jarvis.voice_setup import VoiceSetup
class SetupTests(unittest.TestCase):
 def test_download_requires_consent(self):
  with self.assertRaises(ValueError):VoiceSetup().start()
 def test_check_never_downloads(self):
  setup=VoiceSetup()
  with patch('jarvis.voice_setup.models.ready',return_value=False),patch('jarvis.voice_setup.models.download') as d:
   setup.start(check=True)
   while setup.busy:time.sleep(.01)
   d.assert_not_called();self.assertFalse(setup.ready)
 def test_cancel_available(self):
  setup=VoiceSetup();setup.stop();self.assertTrue(setup.cancel.is_set())
