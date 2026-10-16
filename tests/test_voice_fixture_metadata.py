import unittest,pathlib,ast
class VoiceFixtureMetadata(unittest.TestCase):
 def test_loaded_fixture_key_and_failure_exit(self):
  root=pathlib.Path(__file__).resolve().parents[1];s=(root/'src/jarvis/voice_acceptance.py').read_text(encoding='utf-8')
  self.assertIn("'key':'speech-fixture-not-real-llm'",s)
  entry=(root/'modern-ui/frozen-entry.py').read_text(encoding='utf-8');section=entry.split("sys.argv[1]=='--voice-self-test':",1)[1].split("elif len",1)[0]
  self.assertIn('traceback.print_exc();code=1',section);self.assertIn('os._exit(code)',section);ast.parse(entry)
