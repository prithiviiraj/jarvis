import unittest,pathlib
class NativeRoute(unittest.TestCase):
 def test_unified_owner_chosen_first_interface_route(self):
  s=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text(encoding='utf-8')
  self.assertIn('let entry="index.html";',s)
  self.assertNotIn('JARVIS_LEGACY_WORKSPACE_DIAGNOSTIC',s)
