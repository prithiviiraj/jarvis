import unittest,pathlib
class Contract(unittest.TestCase):
 def test_owned_input_proof_is_explicit_windows_only_no_owner_app(self):
  s=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/desktop-native-proof.py').read_text()
  self.assertIn("if os.name!='nt'",s);self.assertIn('process=child.pid',s)
  self.assertIn("w['pid']==child.pid",s);self.assertIn('actual literal Win32 input equals owned app readback',s)
  self.assertIn('controller.stop()',s);self.assertIn('changed actual window blocked next input',s)
