import unittest,tempfile,pathlib
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);(self.root/'.obsidian').mkdir();(self.root/'a.md').write_text('source evidence');self.b=Bridge(WorkspaceVoice());self.b.execute({'command':'vault-connect','vault_folder':str(self.root),'consent':True})
 def tearDown(self):self.b.close();self.tmp.cleanup()
 def test_results_snapshot_read_and_disconnect(self):
  s=self.b.execute({'command':'knowledge-search','query':'evidence'});self.assertEqual(s['knowledge']['results'][0]['name'],'a.md');self.assertEqual(s['knowledge_graph']['nodes'][0]['id'],'a.md')
  s=self.b.execute({'command':'knowledge-read','note_name':'a.md'});self.assertEqual(s['knowledge']['note']['text'],'source evidence')
  s=self.b.execute({'command':'vault-disconnect'});self.assertIsNone(s['knowledge']['note']);self.assertEqual(s['knowledge']['results'],[])
 def test_stop_and_scoped_interruption(self):
  before=self.b.knowledge.generation;self.b.execute({'command':'conversation-interrupt'});self.assertGreater(self.b.knowledge.generation,before)
  before=self.b.knowledge.generation;self.b.execute({'command':'pause'});self.assertGreater(self.b.knowledge.generation,before)
 def test_voice_assets_required_no_implicit_download(self):
  row=self.b.execute({'command':'knowledge-read','note_name':'a.md'})['knowledge']['note']
  with self.assertRaisesRegex(ValueError,'installed local voice'):self.b.execute({'command':'knowledge-speak','reviewed':row,'confirm':True})
  self.assertIsNone(self.b.knowledge.worker);self.assertFalse(self.b.setup.busy)
 def test_native_shell_reaches_all_new_actions(self):
  s=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text();gate=s.split('.contains(&command)')[0]
  for cmd in ('knowledge-search','knowledge-read','knowledge-speak','knowledge-stop'):self.assertIn('"'+cmd+'"',gate)
