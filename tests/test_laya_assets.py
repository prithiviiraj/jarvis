import unittest,tempfile,pathlib,hashlib,threading,io
from unittest.mock import patch,Mock
from jarvis import laya_assets as a
class LayaAssets(unittest.TestCase):
 def asset(self):return {'name':'model.bin','bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest(),'url':'https://example.com/model'}
 def test_pinned_manifest(self):
  self.assertEqual(a.TOTAL_BYTES,1322020017)
  for x in a.ASSETS:self.assertIn('/161d54d6000913ff279b0afd1ac77faef8685a9b/',x['url']);self.assertEqual(len(x['sha256']),64)
 def test_check_does_not_download(self):
  with tempfile.TemporaryDirectory()as t,patch.object(a,'cache',return_value=pathlib.Path(t)),patch.object(a.urllib.request,'urlopen')as net:
   s=a.LayaSetup();s.start(check=True).join(2);self.assertTrue(s.checked);self.assertFalse(s.ready);net.assert_not_called()
 def test_review_required(self):
  with patch.object(a.urllib.request,'urlopen')as net:
   with self.assertRaises(ValueError):a.LayaSetup().start()
   with self.assertRaises(ValueError):a.download('/tmp/no-laya')
   net.assert_not_called()
 def test_integrity_and_resume(self):
  with tempfile.TemporaryDirectory()as t,patch.object(a,'ASSETS',[self.asset()]),patch.object(a.urllib.request,'urlopen',return_value=io.BytesIO(b'fixture'))as net:
   root=pathlib.Path(t);a.download(root,consent=True);self.assertTrue(a.ready(root));a.download(root,consent=True);self.assertEqual(net.call_count,1)
 def test_bad_hash_preserves_existing(self):
  with tempfile.TemporaryDirectory()as t,patch.object(a,'ASSETS',[self.asset()]),patch.object(a.urllib.request,'urlopen',return_value=io.BytesIO(b'changed')):
   root=pathlib.Path(t);(root/'model.bin').write_bytes(b'old')
   with self.assertRaises(ValueError):a.download(root,consent=True)
   self.assertEqual((root/'model.bin').read_bytes(),b'old');self.assertFalse((root/'model.bin.part').exists())
 def test_cancelled_no_network(self):
  c=threading.Event();c.set()
  with tempfile.TemporaryDirectory()as t,patch.object(a.urllib.request,'urlopen')as net:
   with self.assertRaises(ValueError):a.download(pathlib.Path(t),consent=True,cancel=c)
   net.assert_not_called()
