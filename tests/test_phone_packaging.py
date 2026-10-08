import pathlib,unittest
class Tests(unittest.TestCase):
 def test_frozen_phone_dispatch_and_workflow(self):
  root=pathlib.Path(__file__).resolve().parents[1];entry=(root/'modern-ui/frozen-entry.py').read_text();workflow=(root/'.github/workflows/modern-voice.yml').read_text()
  self.assertIn("sys.argv[1]=='--phone-self-test'",entry);self.assertIn('from jarvis.phone_acceptance import run',entry);self.assertIn('jarvis-local-core.exe --phone-self-test',workflow)
