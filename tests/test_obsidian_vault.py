import unittest,tempfile,pathlib
from jarvis.obsidian_vault import Vault,NAME
class ObsidianVault(unittest.TestCase):
 def test_scaffold_sync_preserves_user_changes(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base)
   with self.assertRaises(ValueError):v.create(NAME,False)
   v.create(NAME,True);v.sync([{'name':'You','text':'My actual message'}],{'agents':[]},{'tts_engine':'kokoro','secret':'DO NOT EXPORT'},force=True)
   root=base/NAME;self.assertTrue((root/'Team/LYRA.md').is_file());self.assertIn('My actual message',(root/'Conversations/session.md').read_text());self.assertNotIn('DO NOT EXPORT',(root/'Modes/Current settings.md').read_text())
   p=root/'Team/NOVA.md';p.write_text('My edited agent note');v.sync([],{'agents':[]},{},force=True);self.assertEqual(p.read_text(),'My edited agent note');self.assertIn('Team/NOVA.md',v.skipped)
   work=root/'Active Work.md';work.write_text('Real work');v.create(NAME,True);self.assertEqual(work.read_text(),'Real work')
   v.disable();self.assertTrue(work.exists());self.assertFalse(v.enabled)
 def test_unmanaged_folder_never_overwritten(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);(base/NAME).mkdir();(base/NAME/'mine.md').write_text('Keep')
   v=Vault(base/'config.json',lambda:base)
   with self.assertRaisesRegex(ValueError,'already exists'):v.create(NAME,True)
   self.assertEqual((base/NAME/'mine.md').read_text(),'Keep')
 def test_symlink_escape_stops_sync(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);out=base/'outside';out.mkdir();v=Vault(base/'config.json',lambda:base);v.create(NAME,True);(base/NAME/'Team').symlink_to(out,target_is_directory=True)
   v.sync([],{'agents':[]},{},force=True);self.assertIn('redirected',v.error);self.assertFalse(list(out.iterdir()))
