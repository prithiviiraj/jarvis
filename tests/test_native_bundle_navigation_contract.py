import unittest,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
class NativeBundleNavigationTests(unittest.TestCase):
 def test_composer_not_required_before_visible_route(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');start=source.index('area=work_area_bounds()');end=source.index('navigation(main,\'Settings\')',start);chunk=source[start:end]
  self.assertLess(chunk.index("navigation(main,'Team room')"),chunk.index("title='Message draft'"))
 def test_bundled_speech_laya_readiness_asserted_not_missing(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("'ALREADY DOWNLOADED'in ui_text()",source);self.assertIn("'Laya model verified; engine stopped'in ui_text()",source);self.assertNotIn("click('Download local voice models')",source);self.assertNotIn("click('Download Laya model')",source)
 def test_archive_uses_visible_drawer(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("saved=drawer_control(window,'packaged-chat-probe',group='Saved chat list')",source)
 def test_camera_screen_scope_literals_match_current_ui(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');ui=(ROOT/'modern-ui/src/main.tsx').read_text(encoding='utf-8')
  for text in ('One switch: presence + local vision. Cloud images need the separate reviewed opt-in.','Full primary screen, including private windows. Local background analysis only; cloud questions need the separate reviewed opt-in. No recording.'):
   self.assertIn(text,source);self.assertIn(text,ui)

 def test_drawer_scrolls_real_native_viewport(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("activate(drawer_control(main,name))",source);self.assertIn("mouse.scroll(coords=(bounds.right-25",source);self.assertIn("rect.bottom<=bounds.bottom",source)
 def test_each_welcome_capture_waits_for_current_title(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("for index,title in enumerate(welcome_titles)",source);self.assertIn("main.child_window(title=title,control_type='Text').wait('visible',timeout=10)",source)

 def test_missing_weight_mode_is_explicit_and_diagnostic_package_bound(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');self.assertIn("os.environ.get('JARVIS_NATIVE_WEIGHTS_DIAGNOSTIC')=='1'",source);self.assertIn("marker=exe.parent/'DIAGNOSTIC ONLY.txt'",source);self.assertIn('Heavy speech/Laya/embedding runtimes excluded',source);self.assertEqual(source.count('if not weights_diagnostic:'),2);self.assertIn("'Kokoro or shared speech assets missing'in ui_text()",source);self.assertIn("'Laya model missing; review Download Laya model'in ui_text()",source)
 def test_shipping_job_does_not_enable_missing_weight_mode(self):
  workflow=(ROOT/'.github/workflows/modern-voice.yml').read_text(encoding='utf-8');self.assertEqual(workflow.count("$env:JARVIS_NATIVE_WEIGHTS_DIAGNOSTIC = '1'"),1);self.assertNotIn('JARVIS_NATIVE_WEIGHTS_DIAGNOSTIC',workflow[workflow.index('  windows:'):])

 def test_notes_search_summary_has_native_button_role_and_exact_drawer_binding(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8');ui=(ROOT/'modern-ui/src/main.tsx').read_text(encoding='utf-8')
  self.assertIn('role="button" aria-label="Expand notes and chats"',ui)
  self.assertIn("activate(drawer_control(window,'Expand notes and chats'))",source)
  self.assertNotIn("title='Notes and chats',control_type='Button'",source)

 def test_settings_rail_has_its_own_scroll_target_not_content_margin(self):
  source=(ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8')
  self.assertIn('rail_names=',source);self.assertIn('bounds.left+340,bounds.top+420',source);self.assertIn('Settings rail target remains clipped',source)
