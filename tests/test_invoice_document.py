import unittest,tempfile,pathlib
from jarvis.invoice_document import InvoiceDocument
import test_invoice_draft as invoice
class Tests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.j=InvoiceDocument(pathlib.Path(self.t.name)/'invoices')
 def tearDown(self):self.t.cleanup()
 def test_missing_no_file_and_review_exact_save_readback(self):
  r=self.j.prepare({'seller':'Fixture'});self.assertEqual(r['state'],'needs-details');self.assertFalse(self.j.root.exists());r=self.j.prepare(invoice.Tests().facts())
  with self.assertRaises(ValueError):self.j.save(r)
  with self.assertRaises(ValueError):self.j.save(dict(r,sha256='changed'),True)
  result=self.j.save(r,True);text=pathlib.Path(result['path']).read_text();self.assertIn('INR 0.20',text);self.assertIn('Draft invoice',text);self.assertNotIn('<script',text)
  with self.assertRaises(ValueError):self.j.save(r,True)
 def test_escape_markup_no_remote_assets(self):
  f=invoice.Tests().facts();f['seller']='<script>alert(1)</script>';f['items'][0]['description']='<img src="https://attack.invalid/a">';r=self.j.prepare(f);text=self.j.render(r['document']);self.assertIn('&lt;script&gt;',text);self.assertNotIn('<script>',text);self.assertNotIn('<img',text);self.assertNotIn('<link',text)
 def test_cancel_stale_review(self):
  r=self.j.prepare(invoice.Tests().facts());self.j.cancel()
  with self.assertRaises(ValueError):self.j.save(r,True)
  self.assertFalse(self.j.root.exists())
 def test_symlink_folder_rejected(self):
  dest=pathlib.Path(self.t.name)/'target';dest.mkdir();self.j.root.symlink_to(dest,target_is_directory=True);r=self.j.prepare(invoice.Tests().facts())
  with self.assertRaises(ValueError):self.j.save(r,True)
 def test_open_only_exact_unchanged_saved_local_draft(self):
  calls=[];self.j.opener=lambda p:calls.append(p);r=self.j.prepare(invoice.Tests().facts());result=self.j.save(r,True)
  with self.assertRaises(ValueError):self.j.open_saved(result)
  self.j.open_saved(result,True);self.assertEqual(len(calls),1);pathlib.Path(result['path']).write_text('Changed')
  with self.assertRaises(ValueError):self.j.open_saved(result,True)
  self.assertEqual(len(calls),1)
