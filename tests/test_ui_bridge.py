import unittest
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class UiBridgeTests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_default_off(self):
  s=self.b.execute({'command':'status'});self.assertEqual(s['awareness']['camera'],'off');self.assertFalse(s['judgment']['enabled'])
 def test_unknown_refused(self):
  for cmd in ['shell','read-file','cloud-chat','open-url']:
   with self.assertRaises(ValueError):self.b.execute({'command':cmd})
 def test_camera_consent(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'camera-on'})
 def test_judge_consent(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'judgment','enabled':True})
 def test_no_cloud_command(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'cloud':True})
 def test_pause_clears(self):
  self.b.context.set_apps(True);self.b.messages=[{'name':'You','text':'private'}];s=self.b.execute({'command':'pause'});self.assertFalse(s['messages']);self.assertFalse(s['awareness']['app_monitor'])
 def test_select(self):self.assertEqual(self.b.execute({'command':'select','name':'DEX'})['selected'],'DEX')
 def test_bad_apps(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'apps','enabled':'yes'})

 def test_judgment_opt_in_and_audio_revoke(self):
  state=self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':True});self.assertTrue(state['judgment']['enabled']);self.assertTrue(state['judgment']['audio'])
  state=self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':False});self.assertFalse(state['judgment']['audio'])
 def test_camera_explicit_opt_in(self):
  self.b.camera.start=Mock();self.b.execute({'command':'camera-on','consent':True});self.b.camera.start.assert_called_once_with(True)
 def test_apps_title_consent_and_clear(self):
  self.b.execute({'command':'apps','enabled':True,'titles':True});self.assertTrue(self.b.titles)
  self.b.context.app_event({'process':'app.exe','title':'private title'});self.b.execute({'command':'apps','enabled':True,'titles':False});self.assertFalse(self.b.titles);self.assertIsNone(self.b.context.app)
 def test_voice_consent_and_local(self):
  self.b.voice.start=Mock()
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-on'})
  self.b.execute({'command':'voice-on','consent':True});self.b.voice.start.assert_called_once_with(consent=True,cloud=False)
 def test_pause_disables_all(self):
  self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':True});self.b.execute({'command':'apps','enabled':True,'titles':True})
  state=self.b.execute({'command':'pause'});self.assertFalse(state['judgment']['enabled']);self.assertFalse(state['judgment']['audio']);self.assertFalse(state['awareness']['app_monitor']);self.assertFalse(self.b.titles)
 def test_no_destinations(self):
  for k in ['cloud','cloud_consent','provider','api_key','model','path','url']:
   with self.assertRaises(ValueError):self.b.execute({'command':'status',k:'x'})

 def test_error_survives_idle_poll(self):
  self.b.voice.notify('error','LM Studio timeout');self.b.voice.notify('state','off')
  self.assertEqual(self.b.execute({'command':'status'})['error'],'LM Studio timeout')
  self.assertEqual(self.b.execute({'command':'status'})['error'],'LM Studio timeout')
  self.assertEqual(self.b.execute({'command':'pause'})['error'],'')

 def test_setup_does_not_enable_audio(self):
  self.b.setup.start=Mock();state=self.b.execute({'command':'voice-setup','consent':True});self.b.setup.start.assert_called_once_with(consent=True);self.assertFalse(state['voice_active'])
 def test_voice_failure_visible(self):
  self.b.voice.notify('error','Speech assets missing');self.b.voice.notify('state','off');self.assertEqual(self.b.execute({'command':'status'})['error'],'Speech assets missing')
