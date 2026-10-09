import unittest,tempfile,pathlib
from unittest.mock import patch
from jarvis.brave_path import find_brave
class BraveTests(unittest.TestCase):
 def test_known_path_only(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'BraveSoftware/Brave-Browser/Application/brave.exe';p.parent.mkdir(parents=True);p.touch()
   with patch('jarvis.brave_path.Path',type(p)),patch('jarvis.brave_path.os.name','nt'),patch.dict('jarvis.brave_path.os.environ',{'PROGRAMFILES':d}):self.assertEqual(find_brave(),str(p))
 def test_nonwindows_honest_block(self):
  with patch('jarvis.brave_path.os.name','posix'):
   with self.assertRaisesRegex(RuntimeError,'Windows'):find_brave()
