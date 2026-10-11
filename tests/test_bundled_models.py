import unittest,tempfile,hashlib
from pathlib import Path
from jarvis.bundled_models import import_verified
class BundleTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/'bundle';self.target=self.root/'cache';self.source.mkdir();self.sha=hashlib.sha256(b'known weights').hexdigest();(self.source/'known.bin').write_bytes(b'known weights');self.spec={'known.bin':(self.sha,30,None)}
 def test_verified_offline_import(self):
  self.assertEqual(import_verified(self.source,self.target,self.spec),['known.bin']);self.assertEqual((self.target/'known.bin').read_bytes(),b'known weights');self.assertEqual(import_verified(self.source,self.target,self.spec),[])
 def test_corrupt_and_oversize_skip(self):
  (self.source/'known.bin').write_bytes(b'bad');self.assertEqual(import_verified(self.source,self.target,self.spec),[]);self.assertFalse(self.target.exists())
 def test_owner_cache_never_overwritten(self):
  self.target.mkdir();(self.target/'known.bin').write_bytes(b'owner');import_verified(self.source,self.target,self.spec);self.assertEqual((self.target/'known.bin').read_bytes(),b'owner')
 def test_path_escape_refused(self):
  with self.assertRaises(ValueError):import_verified(self.source,self.target,{'../oops':(self.sha,30,None)})
 def test_symlink_skipped(self):
  (self.source/'known.bin').unlink();outside=self.root/'outside';outside.write_bytes(b'known weights');(self.source/'known.bin').symlink_to(outside);self.assertEqual(import_verified(self.source,self.target,self.spec),[])
 def test_background_setup_publishes_real_progress(self):
  from jarvis.bundled_models import BundleSetup
  setup=BundleSetup();worker=setup.start(self.source,self.target,self.spec);worker.join(2);state=setup.snapshot();self.assertFalse(state['busy']);self.assertEqual(state['percent'],100);self.assertEqual(state['installed'],['known.bin']);self.assertFalse(state['error'])
