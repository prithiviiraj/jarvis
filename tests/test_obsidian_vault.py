import unittest,tempfile,pathlib
from jarvis.obsidian_vault import Vault,NAME
class ObsidianVault(unittest.TestCase):
 def test_scaffold_sync_preserves_user_changes(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base)
   with self.assertRaises(ValueError):v.create(NAME,False)
   v.create(NAME,True);v.sync([{'name':'You','text':'My actual message'}],{'agents':[]},{'tts_engine':'kokoro','secret':'DO NOT EXPORT'},force=True)
   root=base/NAME;self.assertTrue((root/'Team/LYRA.md').is_file());self.assertIn('My actual message',(root/'Conversations/session.md').read_text());self.assertNotIn('DO NOT EXPORT',(root/'Modes/Current settings.md').read_text())
   p=root/'Team/DEX.md';p.write_text('My edited agent note');v.sync([],{'agents':[]},{},force=True);self.assertEqual(p.read_text(),'My edited agent note');self.assertIn('Team/DEX.md',v.skipped)
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
 def test_separate_nodes_links_and_local_exact_knowledge(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base);v.create(NAME,True);v.sync([{'name':'DEX','text':'Actual code reply'}],{'agents':[{'name':'LUNA','voice':'JARVIS','personality':'Friendly'}]},{},force=True);root=base/NAME
   self.assertIn('Agents/LYRA/Node',(root/'Agents index.md').read_text());self.assertFalse((root/'Agents/LUNA/Node.md').is_file());self.assertIn('Actual code reply',(root/'Agents/DEX/Recent replies.md').read_text());self.assertNotIn('Actual code reply',(root/'Agents/LYRA/Recent replies.md').read_text())
   p=root/'Agents/DEX/Knowledge.md';p.write_text('Real helper facts');v.sync([],{'agents':[]},{},force=True);self.assertEqual(p.read_text(),'Real helper facts');m=[{'role':'system','content':'DEX'},{'role':'user','content':'what facts'}];self.assertEqual(v.attach(m,'DEX'),(m,False));v.connect_nodes(True);out,local=v.attach(m,'DEX');self.assertTrue(local);self.assertIn('Real helper facts',out[1]['content']);self.assertNotIn('Real helper facts',v.attach(m,'LYRA')[0][1]['content']);v.disable();self.assertEqual(v.attach(m,'DEX'),(m,False))
 def test_data_centre_plan_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base);v.create(NAME,True);p=base/NAME/'Planning/Today.md';self.assertTrue((base/NAME/'Data Centre/Home.md').is_file());p.write_text('My real plan');v.create(NAME,True);self.assertEqual(p.read_text(),'My real plan')
 def test_visual_map_areas_and_preserve_edits(self):
  import json
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'c.json',lambda:base);v.create(NAME,True);root=base/NAME;c=root/'Brain of Brain.canvas';j=json.loads(c.read_text());self.assertEqual(len(j['nodes']),16);self.assertEqual(len(j['edges']),12)
   for row in j['nodes']:
    if row.get('type')!='file' or row['file']=='Agents index.md':continue
    self.assertTrue((root/row['file']).is_file())
   c.write_text('owner-edited canvas');v.create(NAME,True);self.assertEqual(c.read_text(),'owner-edited canvas')
 def test_registration_error_survives_later_sync(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base)
   with patch('jarvis.obsidian_registry.register',side_effect=RuntimeError('Close Obsidian then retry')):
    v.start('connect',reviewed=NAME,confirm=True).join(3)
   self.assertEqual(v.registration,'needs attention');self.assertIn('Close Obsidian',v.connection_error)
   v.sync([],{'agents':[]},{},force=True)
   self.assertIn('Close Obsidian',v.snapshot()['connection_error']);self.assertEqual(v.snapshot()['registration'],'needs attention')

 def test_managed_vault_connect_before_obsidian_open(self):
  from jarvis.obsidian import Vault as Reader
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config.json',lambda:base);v.create(NAME,True)
   reader=Reader('"'+str(base/NAME)+'"');self.assertEqual(reader.root,(base/NAME).resolve(strict=True));self.assertIn('Brain of Brain',reader.read('README.md'))
   other=base/'ordinary';other.mkdir()
   with self.assertRaises(ValueError):Reader(other)
