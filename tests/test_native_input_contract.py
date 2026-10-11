import unittest,importlib.util,pathlib
from unittest.mock import Mock
ROOT=pathlib.Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('native_input',ROOT/'modern-ui/native-input.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class NoPatternInterfaceError(Exception):pass
class NativeInputContractTests(unittest.TestCase):
 def test_standard_invoke_retained(self):
  c=Mock();n.activate(c);c.wrapper_object.return_value.invoke.assert_called_once();c.wrapper_object.return_value.click_input.assert_not_called()
 def test_summary_real_mouse_fallback(self):
  c=Mock();c.wrapper_object.return_value.invoke.side_effect=NoPatternInterfaceError();n.activate(c);c.wrapper_object.return_value.click_input.assert_called_once()
 def test_other_errors_remain_failures(self):
  c=Mock();c.wrapper_object.return_value.invoke.side_effect=ValueError('fixture failure')
  with self.assertRaises(ValueError):n.activate(c)
  c.wrapper_object.return_value.click_input.assert_not_called()
 def test_all_native_invokes_use_shared_pattern_handling(self):
  self.assertNotIn('.invoke()', (ROOT/'modern-ui/native-smoke.py').read_text(encoding='utf-8'))
