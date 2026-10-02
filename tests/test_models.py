import tempfile,unittest,pathlib
from jarvis.models import ready,download,DownloadError,digest
class ModelTests(unittest.TestCase):
 def test_consent(self):
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(DownloadError):download(p)
   self.assertEqual(list(pathlib.Path(p).iterdir()),[])
 def test_missing(self):
  with tempfile.TemporaryDirectory() as p:self.assertFalse(ready(p))
 def test_hash(self):
  with tempfile.TemporaryDirectory() as p:
   f=pathlib.Path(p)/'x';f.write_bytes(b'abc');self.assertEqual(digest(f),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
