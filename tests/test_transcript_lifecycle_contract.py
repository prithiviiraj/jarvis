import pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class TranscriptLifecycleContract(unittest.TestCase):
 def test_close_uses_explicit_hidden_transition(self):
  s=(R/'modern-ui/src-tauri/src/main.rs').read_text();close=s.split('if let tauri::WindowEvent::CloseRequested{api,..}=event',1)[1].split('if let tauri::WindowEvent::Resized',1)[0]
  self.assertIn('show_background_windows(window.app_handle())',close);self.assertNotIn('sync_captions',close);self.assertIn('window.hide()',close);self.assertIn('exit(0)',close)
 def test_transcript_setting_has_native_boolean_readback(self):
  s=(R/'modern-ui/src-tauri/src/main.rs').read_text()
  for name in ('overlay','floating_off'):
   body=s.split('async fn '+name,1)[1].split('#[tauri::command]',1)[0];self.assertIn('Result<bool,String>',body);self.assertIn('TranscriptEnabled',body);self.assertIn('save_transcript',body)
 def test_native_fixture_waits_confirmation_but_keeps_close_assertions(self):
  s=(R/'modern-ui/native-smoke.py').read_text();self.assertIn("confirmed='Transcript confirmed '",s);self.assertIn("overlay_text.wait('visible',timeout=10)",s);self.assertIn('assert not ctypes.windll.user32.IsWindowVisible(workspace_handle)',s);self.assertIn("overlay_text.child_window(title='Reopen workspace'",s);self.assertIn("p.wait(timeout=10)",s)
