import pathlib,unittest
class Tests(unittest.TestCase):
 def test_frozen_phone_dispatch_and_workflow(self):
  root=pathlib.Path(__file__).resolve().parents[1];entry=(root/'modern-ui/frozen-entry.py').read_text();workflow=(root/'.github/workflows/modern-voice.yml').read_text()
  self.assertIn("sys.argv[1]=='--phone-self-test'",entry);self.assertIn('from jarvis.phone_acceptance import run',entry);self.assertIn('jarvis-local-core.exe --phone-self-test',workflow)

 def test_phone_static_assets_present_not_auto_started(self):
  root=pathlib.Path(__file__).resolve().parents[1];page=root/'modern-ui/phone-web'
  for name in ('index.html','phone.css','phone.js','capture.js'):self.assertTrue((page/name).is_file())
  package=(root/'modern-ui/package-windows.py').read_text();self.assertIn("shutil.copytree(root/'phone-web',out/'phone-web')",package)
  js=(page/'phone.js').read_text();self.assertNotIn('localStorage',js);self.assertNotIn('sessionStorage',js);self.assertIn('window.isSecureContext',js);self.assertIn("window.addEventListener('pagehide'",js)
