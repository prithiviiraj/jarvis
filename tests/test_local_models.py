import unittest,tempfile
from jarvis.local_models import recommendations,detect_hardware,CATALOG
class LocalModels(unittest.TestCase):
 def test_owner_like_fit(self):
  r=recommendations({'ram_gb':16,'vram_gb':6,'dedicated':True,'free_disk_gb':100});self.assertEqual(r['pick'],'qwen3-vl-4b');self.assertTrue(r['options'][0]['available']);self.assertIn('slower',r['options'][1]['note']);self.assertFalse(r['options'][2]['available'])
 def test_small_disk(self):
  r=recommendations({'ram_gb':16,'vram_gb':6,'dedicated':True,'free_disk_gb':1});self.assertTrue(all(not x['available']for x in r['options']))
 def test_invalid(self):
  with self.assertRaises(ValueError):recommendations({'ram_gb':float('nan')})
 def test_pins(self):
  for m in CATALOG['models']:
   for f in m['files']:self.assertEqual(len(f['sha256']),64);self.assertIn('/resolve/',f['url']);self.assertGreater(f['size'],0)
 def test_scan_no_process_or_download(self):
  with tempfile.TemporaryDirectory()as d:self.assertGreater(detect_hardware(d)['free_disk_gb'],0)
