import copy,pathlib,tempfile,unittest
from jarvis.design_draft import DesignDraft
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)/'design';self.now=0;self.d=DesignDraft(self.root,clock=lambda:self.now);self.f={'title':'A local poster','body':'Exact owner wording only.','footer':'Draft','theme':'paper'}
 def tearDown(self):self.tmp.cleanup()
 def test_review_save_exact_no_open_external_assets(self):
  r=self.d.prepare(self.f,True);self.assertFalse(self.root.exists());out=self.d.save(r,True);self.assertEqual(pathlib.Path(out['path']).read_text(),r['svg']);self.assertNotIn('href=',r['svg']);self.assertNotIn('<script',r['svg']);self.assertIsNone(self.d.pending)
 def test_escape_script_text(self):
  self.f['body']='<script>alert(1)</script><image href="https://example.com"/>';r=self.d.prepare(self.f,True);self.assertIn('&lt;script&gt;',r['svg']);self.assertNotIn('<image',r['svg'])
 def test_tampered_no_confirm_stopped_expired_refuse(self):
  r=self.d.prepare(self.f,True);bad=copy.deepcopy(r);bad['facts']['body']='changed'
  for reviewed,confirm in ((bad,True),(r,False)):
   with self.assertRaises(ValueError):self.d.save(reviewed,confirm)
  self.now=121
  with self.assertRaises(ValueError):self.d.save(r,True)
  r=self.d.prepare(self.f,True);self.d.cancel()
  with self.assertRaises(ValueError):self.d.save(r,True)
 def test_bounds_theme_fields_and_layout(self):
  for f in ({**self.f,'theme':'remote'},{**self.f,'body':'a'*601},{**self.f,'title':'a'*81},{**self.f,'body':'\0x'},{**self.f,'url':'https://example.com'}):
   with self.assertRaises(ValueError):self.d.prepare(f,True)
 def test_symlink_save_refused(self):
  self.root.symlink_to(pathlib.Path(self.tmp.name),target_is_directory=True);r=self.d.prepare(self.f,True)
  with self.assertRaises(ValueError):self.d.save(r,True)
