import tempfile,pathlib,unittest,sqlite3
from jarvis.chat_history import ChatHistory
class HistoryTests(unittest.TestCase):
 def setUp(self):self.dir=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.dir.name)/'chats.sqlite';self.h=ChatHistory(self.path,max_chats=2,max_messages=2)
 def tearDown(self):self.h.close();self.dir.cleanup()
 def test_restart_unicode(self):
  i=self.h.new();rows=[{'name':'You','text':'வணக்கம்'},{'name':'JARVIS','text':'Hello'}];self.h.save(i,rows);self.h.close();self.h=ChatHistory(self.path);self.assertEqual(self.h.load(i),rows)
 def test_reo_roundtrip(self):
  i=self.h.new();rows=[{'name':'You','text':'Reo, plan opening the docs'},{'name':'REO','text':'Plan: open reviewed browser command.'}];self.h.save(i,rows);self.assertEqual(self.h.load(i),rows)
 def test_retention(self):
  ids=[]
  for n in range(3):i=self.h.new();ids.append(i);self.h.save(i,[{'name':'You','text':str(n)}])
  self.assertEqual(len(self.h.list()),2)
  with self.assertRaises(ValueError):self.h.load(ids[0])
 def test_delete_and_clear(self):
  i=self.h.new();self.h.save(i,[{'name':'You','text':'private'}]);self.h.delete(i);self.assertEqual(self.h.list(),[]);self.h.save(i,[]);self.h.clear();self.assertEqual(self.h.list(),[])
 def test_no_metadata(self):
  i=self.h.new();self.h.save(i,[{'name':'You','text':'hello','api_key':'secret','sensor':'camera'}]);self.assertEqual(self.h.load(i),[{'name':'You','text':'hello'}])
 def test_invalid(self):
  with self.assertRaises(ValueError):self.h.save('../elsewhere',[])
  with self.assertRaises(ValueError):self.h.save(self.h.new(),[{'name':'unknown','text':'bad'}])
 def test_corrupt_store_not_overwritten(self):
  p=pathlib.Path(self.dir.name)/'broken.sqlite';p.write_bytes(b'corrupt original')
  with self.assertRaises(sqlite3.DatabaseError):ChatHistory(p)
  self.assertEqual(p.read_bytes(),b'corrupt original')
 def test_memory_restore(self):
  from jarvis.team_memory import TeamMemory
  m=TeamMemory();m.restore([{'name':'You','text':'hello'},{'name':'NOVA','text':'Hi'},{'name':'You','text':'unanswered'}]);self.assertEqual(m.messages(),[{'role':'user','content':'hello'},{'role':'assistant','content':'[NOVA] Hi'}])
 def test_bridge_restart_browse_delete(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  v=WorkspaceVoice();b=Bridge(v,history=self.h);v.notify('transcript','Saved greeting');v.notify('answer',{'text':'Hello','provider':'local'});state=b.execute({'command':'status'});i=state['chat_id'];self.assertEqual(len(self.h.load(i)),2)
  b.execute({'command':'history-new'});self.assertEqual(b.messages,[]);b.execute({'command':'history-open','chat_id':i});self.assertEqual(b.messages[0]['text'],'Saved greeting');b.execute({'command':'history-delete','chat_id':i,'confirm':True});self.assertEqual(self.h.list(),[]);b.close()
 def test_delete_not_resaved_on_status(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice(),history=self.h);b.voice.notify('transcript','erase');state=b.execute({'command':'status'});b.execute({'command':'history-delete','chat_id':state['chat_id'],'confirm':True})
  for _ in range(4):b.execute({'command':'status'})
  self.assertEqual(self.h.list(),[]);b.close()
 def test_long_messages_bound(self):
  i=self.h.new();self.h.save(i,[{'name':'You','text':'x'*8000}]*8);self.assertEqual(len(self.h.load(i)),2);self.assertEqual(len(self.h.load(i)[0]['text']),4000)
 def test_corrupt_row_safe_bridge(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  i=self.h.new();self.h.save(i,[{'name':'You','text':'original'}]);self.h.db.execute('UPDATE chats SET messages=? WHERE id=?',('{broken',i));self.h.db.commit();b=Bridge(WorkspaceVoice(),history=self.h);self.assertIn('preserved',b.history_error);self.assertEqual(self.h.list()[0]['id'],i);b.close()
 def test_history_commands_block_midturn(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice(),history=self.h);b.voice.busy=True
  self.assertTrue(b.execute({'command':'history-new'})['chat_id']);self.assertFalse(b.voice.busy)
  b.voice.busy=False;b.close()
 def test_clear_requires_confirmation(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice(),history=self.h)
  with self.assertRaisesRegex(ValueError,'Confirm'):b.execute({'command':'history-clear'})
  b.close()
 def test_team_multiple_personas_restored(self):
  from jarvis.team_memory import TeamMemory
  m=TeamMemory();m.restore([{'name':'You','text':'topic'},{'name':'NOVA','text':'one'},{'name':'DEX','text':'two'},{'name':'JARVIS','text':'conclusion'}]);self.assertEqual([x['content']for x in m.messages()if x['role']=='assistant'],['[NOVA] one','[DEX] two','[JARVIS] conclusion'])
 def test_pause_preserves_archive_and_active_messages(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice(),history=self.h);b.voice.notify('transcript','keep this');b.voice.notify('answer',{'text':'actual reply'});state=b.execute({'command':'status'});i=state['chat_id'];paused=b.execute({'command':'pause'});self.assertEqual(paused['messages'],state['messages']);self.assertEqual(self.h.load(i),[{'name':x['name'],'text':x['text']}for x in state['messages']]);b.close()
 def test_delete_requires_confirmation(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice(),history=self.h);i=self.h.new();self.h.save(i,[{'name':'You','text':'retain'}])
  with self.assertRaisesRegex(ValueError,'Confirm'):b.execute({'command':'history-delete','chat_id':i})
  self.assertEqual(self.h.load(i)[0]['text'],'retain');b.close()

class Provenance(unittest.TestCase):
 def test_source_survives_archive(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory()as d:
   h=ChatHistory(Path(d)/'chat.db');cid=h.new();rows=[{'name':'DEX','text':'Actual reply','provider':'nim','model':'actual-model','cloud':True}];h.save(cid,rows);self.assertEqual(h.load(cid),rows);h.close()
