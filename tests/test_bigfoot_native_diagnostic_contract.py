import unittest,pathlib
class NativeRoute(unittest.TestCase):
 def test_owner_chosen_bigfoot_default_legacy_retained_for_regression(self):
  s=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text()
  self.assertIn('std::env::var("JARVIS_LEGACY_WORKSPACE_DIAGNOSTIC").as_deref()==Ok("1")',s)
  self.assertIn('{"index.html"}else{"bigfoot-ui/jarvis.html"}',s)
