import unittest,importlib.util,pathlib
from unittest.mock import Mock
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('native_input',ROOT/'modern-ui/native-input.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class NoPatternInterfaceError(Exception):pass
class NativeInputContractTests(unittest.TestCase):
 def test_standard_invoke_retained(self):
  c=Mock();n.activate(c);c.wrapper_object.return_value.invoke.assert_called_once();c.wrapper_object.return_value.click_input.assert_not_called()
 def test_summary_real_mouse_fallback(self):
  c=self.fallback_control();n.activate(c);c.wrapper_object.return_value.click_input.assert_called_once()
 def test_other_errors_remain_failures(self):
  c=Mock();c.wrapper_object.return_value.invoke.side_effect=ValueError('fixture failure')
  with self.assertRaises(ValueError):n.activate(c)
  c.wrapper_object.return_value.click_input.assert_not_called()
 def test_all_native_invokes_use_shared_pattern_handling(self):
  self.assertNotIn('.invoke()', (ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8'))

 def fallback_control(self,bottom=100):
  c=Mock();w=c.wrapper_object.return_value;w.invoke.side_effect=NoPatternInterfaceError();w.window_text.return_value='Native fixture target'
  w.rectangle.return_value=SimpleNamespace(top=20,bottom=bottom,left=20,right=100,width=lambda:80,height=lambda:bottom-20)
  w.top_level_parent.return_value.rectangle.return_value=SimpleNamespace(top=0,bottom=800,left=0,right=1000)
  return c
 def test_clipped_mouse_target_refuses_instead_of_hitting_other_control(self):
  c=self.fallback_control(bottom=900)
  with self.assertRaisesRegex(RuntimeError,'outside its window'):n.activate(c)
  c.wrapper_object.return_value.click_input.assert_not_called()
