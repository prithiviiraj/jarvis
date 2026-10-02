"""Catch unimported UI syntax regressions even on headless test hosts."""
import ast,pathlib,unittest
class SourceCompileTests(unittest.TestCase):
 def test_all_application_source_parses(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'src'
  for p in root.rglob('*.py'):
   with self.subTest(path=str(p)):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
