import unittest,importlib.util,pathlib,tempfile,hashlib,json
from unittest.mock import patch
class OptionalLaya(unittest.TestCase):
 def module(self):
  p=pathlib.Path(__file__).parents[1]/'optional-laya/runtime.py';spec=importlib.util.spec_from_file_location('optional_laya',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_missing_assets_do_not_download_on_serve(self):
  m=self.module()
  with tempfile.TemporaryDirectory()as t,patch.object(m,'CACHE',pathlib.Path(t)),patch.object(m.urllib.request,'urlopen')as net:
   with self.assertRaises(RuntimeError):m.serve()
   net.assert_not_called()
 def test_integrity_requires_exact_size_and_hash(self):
  m=self.module()
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t)/'asset';p.write_bytes(b'fixture');a={'bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest()};self.assertTrue(m.valid(p,a));p.write_bytes(b'changed');self.assertFalse(m.valid(p,a));p.unlink();self.assertFalse(m.valid(p,a))
 def test_pinned_download_review_and_loopback_only(self):
  m=self.module();self.assertEqual(sum(a['bytes']for a in m.ASSETS),1322020017)
  for a in m.ASSETS:self.assertIn('/161d54d6000913ff279b0afd1ac77faef8685a9b/',a['url']);self.assertEqual(len(a['sha256']),64)
  s=(pathlib.Path(__file__).parents[1]/'optional-laya/runtime.py').read_text();self.assertIn("('127.0.0.1',8000)",s);self.assertNotIn('subprocess',s);self.assertNotIn('browser.submit',s)
