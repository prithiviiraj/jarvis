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
  with self.assertRaises(ValueError):self.b.execute({'command':'judgment','enabled':True,'context_consent':True})
 def test_pause_clears(self):
  self.b.context.set_apps(True);self.b.messages=[{'name':'You','text':'private'}];s=self.b.execute({'command':'pause'});self.assertFalse(s['messages']);self.assertFalse(s['awareness']['app_monitor'])
 def test_select(self):self.assertEqual(self.b.execute({'command':'select','name':'DEX'})['selected'],'DEX')
 def test_bad_apps(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'apps','enabled':'yes'})
