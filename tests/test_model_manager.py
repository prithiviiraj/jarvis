import unittest,tempfile,pathlib
from jarvis.model_manager import ModelManager
class ManagerTests(unittest.TestCase):
 def manager(self,d,**kw):return ModelManager(d,scan=lambda root:{'ram_gb':16,'vram_gb':6,'dedicated':True,'free_disk_gb':100},**kw)
 def test_no_effect_on_construct(self):
  with tempfile.TemporaryDirectory()as d:
   m=self.manager(d);self.assertIsNone(m.worker);self.assertEqual(list(pathlib.Path(d).iterdir()),[])
 def test_review_without_download(self):
  with tempfile.TemporaryDirectory()as d:
   m=self.manager(d);p=m.prepare('qwen3-vl-4b')['pending'];self.assertEqual(len(p['files']),3);self.assertIsNone(m.worker)
 def test_exact_review(self):
  with tempfile.TemporaryDirectory()as d:
   m=self.manager(d);p=m.prepare('qwen3-vl-4b')['pending']
   with self.assertRaises(ValueError):m.start(p)
   with self.assertRaises(ValueError):m.start({**p,'bytes':1},True)
 def test_real_callback_with_transport_only_mocked(self):
  with tempfile.TemporaryDirectory()as d:
   calls=[]
   def download(item,target,cancel,notify):calls.append(item['name']);return target
   def extract(archive,dest,cancel):calls.append('extract');return dest
   m=self.manager(d,download=download,extract=extract);p=m.prepare('qwen3-vl-4b')['pending'];m.start(p,True);m.worker.join(2);s=m.snapshot();self.assertFalse(s['busy']);self.assertEqual(s['installed'],['qwen3-vl-4b']);self.assertEqual(len(calls),4);self.assertIn('not started',s['status'])
 def test_stop_clears_review(self):
  with tempfile.TemporaryDirectory()as d:
   m=self.manager(d);p=m.prepare('qwen3-vl-4b')['pending'];m.stop()
   with self.assertRaises(ValueError):m.start(p,True)
 def test_changed_existing_runtime_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   from jarvis.local_models import CATALOG
   dest=pathlib.Path(d)/'runtime'/CATALOG['runtime']['tag'];dest.mkdir(parents=True);(dest/'llama-server.exe').write_bytes(b'changed')
   m=self.manager(d,download=lambda item,target,cancel,notify:target);p=m.prepare('qwen3-vl-4b')['pending'];m.start(p,True);m.worker.join(2)
   self.assertEqual(m.snapshot()['installed'],[]);self.assertIn('preserved',m.snapshot()['error']);self.assertEqual((dest/'llama-server.exe').read_bytes(),b'changed')

 def test_saved_asset_check_requires_consent_and_no_download(self):
  from unittest.mock import patch,Mock
  with tempfile.TemporaryDirectory()as d:
   download=Mock();m=self.manager(d,download=download)
   with self.assertRaises(ValueError):m.check_installed()
   with patch('jarvis.model_manager.verify_runtime_receipt',return_value=True),patch('jarvis.model_manager.verified',return_value=True):
    m.check_installed(True);m.worker.join(2);self.assertEqual(len(m.installed),3);download.assert_not_called();self.assertIn('no model started',m.status)
 def test_changed_runtime_not_rediscovered_as_ready(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory()as d:
   m=self.manager(d)
   with patch('jarvis.model_manager.verify_runtime_receipt',return_value=False):m.check_installed(True);m.worker.join(2)
   self.assertEqual(m.installed,[]);self.assertIn('changed',m.error)
