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

 def test_selection_invalidates_previous_ready_without_io(self):
  setup=VoiceSetup();setup.ready=True;setup.checked=True;setup.status='Kokoro assets ready'
  with patch('jarvis.voice_setup.models.ready')as r,patch('jarvis.voice_setup.models.download')as d:
   setup.select('kokoro');state=setup.snapshot();self.assertFalse(state['ready']);self.assertFalse(state['checked']);self.assertEqual(state['engine'],'kokoro');self.assertIn('Kokoro assets not checked',state['status']);r.assert_not_called();d.assert_not_called()
 def test_selected_check_names_engine_and_reuses_no_download(self):
  setup=VoiceSetup()
  with patch('jarvis.voice_setup.models.ready',return_value=True),patch('jarvis.voice_setup.voice_assets.ready',return_value=True),patch('jarvis.voice_setup.models.download')as d:
   setup.start(check=True,engine='kokoro')
   while setup.busy:time.sleep(.01)
   state=setup.snapshot();self.assertTrue(state['ready']);self.assertTrue(state['checked']);self.assertEqual(state['engine'],'kokoro');self.assertIn('Kokoro assets ready',state['status']);d.assert_not_called()
 def test_selection_refused_during_setup(self):
  setup=VoiceSetup();setup.busy=True
  with self.assertRaises(ValueError):setup.select('kitten')
