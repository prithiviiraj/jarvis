import unittest,pathlib
class NativeRoute(unittest.TestCase):
 def test_copied_ui_is_explicit_diagnostic_only_legacy_shipping_default_preserved(self):
  s=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text()
  self.assertIn('std::env::var("JARVIS_BIGFOOT_DIAGNOSTIC").as_deref()==Ok("1")',s)
  self.assertIn('{"bigfoot-ui/jarvis.html"}else{"index.html"}',s)
