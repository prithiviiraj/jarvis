import tempfile,pathlib,hashlib,json,unittest
from unittest.mock import patch
from jarvis.native_frontend import verified_frontend
class NativeManifestTests(unittest.TestCase):
 def test_manifest_bytes_and_tamper(self):
  with tempfile.TemporaryDirectory() as root,patch('sys._MEIPASS',root,create=True):
   base=pathlib.Path(root)/'native-voice';base.mkdir();rows={}
   for name in ['phonemis_runner.exe','en-us/lexicon_full.json','en-us/phonemizer_en_us.bin','en-us/tagger.json']:
    p=base/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'synthetic');rows[name]=hashlib.sha256(b'synthetic').hexdigest()
   (base/'manifest.json').write_text(json.dumps(rows));self.assertEqual(verified_frontend()[0],base/'phonemis_runner.exe')
   (base/'phonemis_runner.exe').write_bytes(b'altered')
   with self.assertRaises(RuntimeError):verified_frontend()
 def test_missing_manifest(self):
  with tempfile.TemporaryDirectory() as root,patch('sys._MEIPASS',root,create=True):
   with self.assertRaises(RuntimeError):verified_frontend()
