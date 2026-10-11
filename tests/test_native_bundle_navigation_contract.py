import unittest,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
class NativeBundleNavigationTests(unittest.TestCase):
 def test_composer_not_required_before_visible_route(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');start=source.index('area=work_area_bounds()');end=source.index('navigation(main,\'Settings\')',start);chunk=source[start:end]
  self.assertLess(chunk.index("navigation(main,'Team room')"),chunk.index("title='Message draft'"))
 def test_bundled_speech_laya_readiness_asserted_not_missing(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("'ALREADY DOWNLOADED'in ui_text()",source);self.assertIn("'Laya model verified; engine stopped'in ui_text()",source);self.assertNotIn("click('Download local voice models')",source);self.assertNotIn("click('Download Laya model')",source)
 def test_archive_uses_visible_drawer(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("saved=window.child_window(title='packaged-chat-probe',control_type='Button',visible_only=True)",source)
 def test_camera_screen_scope_literals_match_current_ui(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');ui=(ROOT/'modern-ui/src/main.tsx').read_text(encoding='utf-8')
  for text in ('One switch: presence + local vision. Cloud images need the separate reviewed opt-in.','Full primary screen, including private windows. Local background analysis only; cloud questions need the separate reviewed opt-in. No recording.'):
   self.assertIn(text,source);self.assertIn(text,ui)
