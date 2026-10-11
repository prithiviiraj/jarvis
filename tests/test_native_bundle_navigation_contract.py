import unittest,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
class NativeBundleNavigationTests(unittest.TestCase):
 def test_composer_not_required_before_visible_route(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text();start=source.index('area=work_area_bounds()');end=source.index('navigation(main,\'Settings\')',start);chunk=source[start:end]
  self.assertLess(chunk.index("navigation(main,'Team room')"),chunk.index("title='Message draft'"))
 def test_bundled_speech_laya_readiness_asserted_not_missing(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text();self.assertIn("'ALREADY DOWNLOADED'in ui_text()",source);self.assertIn("'Laya model verified; engine stopped'in ui_text()",source);self.assertNotIn("click('Download local voice models')",source);self.assertNotIn("click('Download Laya model')",source)
 def test_archive_uses_visible_drawer(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text();self.assertIn("saved=window.child_window(title='packaged-chat-probe',control_type='Button',visible_only=True)",source)
