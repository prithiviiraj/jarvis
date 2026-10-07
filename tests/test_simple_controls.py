import unittest
from unittest.mock import Mock
from pathlib import Path
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class SimpleControls(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_consent_and_strict_flags(self):
  for name in ('laya-session','proactive-session'):
   for row in ({'enabled':True},{'enabled':'yes','consent':True}):
    with self.assertRaises(ValueError):self.b.execute({'command':name,**row})
 def test_laya_one_action_still_bounded(self):
  self.b.execute({'command':'laya-session','enabled':True,'consent':True});self.assertTrue(self.b.laya_active);self.assertTrue(self.b.desktop_enabled);self.assertTrue(self.b.browser_enabled)
  self.b.execute({'command':'laya-session','enabled':False,'consent':True});self.assertFalse(self.b.laya_active)
 def test_proactive_api_only_no_immediate_dialogue_and_stop(self):
  self.b.setup.ready=True;self.b.voice.dialogue=Mock();self.b.execute({'command':'proactive-session','enabled':True,'consent':True});self.b.voice.dialogue.assert_not_called();self.assertTrue(self.b.idle.audio);self.assertTrue(self.b.idle.configured);self.assertTrue(self.b.voice.idle_configured);self.assertTrue(55<=self.b.idle.next_gap<=75);self.assertIsNone(self.b.idle.poll())
  self.b.execute({'command':'proactive-session','enabled':False,'consent':True});self.assertFalse(self.b.idle.enabled)
 def test_proactive_missing_voice_does_not_enable(self):
  self.b.setup.ready=False
  with self.assertRaises(ValueError):self.b.execute({'command':'proactive-session','enabled':True,'consent':True})
  self.assertFalse(self.b.idle.enabled)
 def test_transient_scene_excluded_from_history_and_chat_context(self):
  self.b.history=Mock();self.b.archive_dirty=True;self.b.messages=[{'name':'You','text':'hello'},{'name':'JARVIS','text':'screen only','transient_screen':True}];self.b.save_history(True);self.assertEqual(self.b.history.save.call_args[0][1],[self.b.messages[0]])
 def test_native_command_allowlist(self):
  source=(Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text();allow=source.split('.contains(&command)')[0]
  for cmd in ('laya-session','proactive-session'):self.assertIn('"'+cmd+'"',allow)
 def test_proactive_busy_does_not_latch(self):
  self.b.setup.ready=True;self.b.voice.busy=True
  with self.assertRaises(ValueError):self.b.execute({'command':'proactive-session','enabled':True,'consent':True})
  self.assertFalse(self.b.idle.enabled)
 def test_obsidian_manual_default_and_connect_no_auto_export(self):
  self.b.obsidian.enabled=True;self.b.obsidian.start=Mock();self.b.brains.refresh_live=Mock();self.b.poll();self.b.obsidian.start.assert_not_called();self.assertFalse(self.b.obsidian.snapshot()['auto_sync'])
  self.b.execute({'command':'obsidian-create','reviewed_name':'Brain of Brain','confirm':True});self.b.obsidian.start.assert_called_once();self.assertFalse(self.b.obsidian.auto_sync)
 def test_camera_single_session_does_not_enable_unrelated_features(self):
  self.b.camera.start=Mock();self.b.execute({'command':'camera-on','consent':True});self.assertFalse(self.b.context.apps);self.assertFalse(self.b.judge.enabled);self.assertFalse(self.b.idle.enabled);self.assertFalse(self.b.browser_enabled)
