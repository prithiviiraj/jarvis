"""Different Python processes, same user-owned local archive."""
import json,os,pathlib,subprocess,sys,tempfile,unittest
class ProcessRestart(unittest.TestCase):
 def test_write_exit_restore_delete_exit(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'chat.sqlite';env=dict(os.environ);env['PYTHONPATH']=str(pathlib.Path(__file__).resolve().parents[1]/'src')
   script="from jarvis.chat_history import ChatHistory;import sys;h=ChatHistory(sys.argv[1]);i=h.new();h.save(i,[{'name':'You','text':'hello after restart'},{'name':'JARVIS','text':'Saved locally'}]);print(i);h.close()"
   i=subprocess.check_output([sys.executable,'-c',script,str(p)],env=env,text=True).strip()
   script="from jarvis.chat_history import ChatHistory;import sys,json;h=ChatHistory(sys.argv[1]);print(json.dumps(h.load(sys.argv[2])));h.delete(sys.argv[2]);h.close()"
   rows=json.loads(subprocess.check_output([sys.executable,'-c',script,str(p),i],env=env,text=True));self.assertEqual(rows[1]['text'],'Saved locally')
   script="from jarvis.chat_history import ChatHistory;import sys;h=ChatHistory(sys.argv[1]);print(len(h.list()));h.close()"
   self.assertEqual(subprocess.check_output([sys.executable,'-c',script,str(p)],env=env,text=True).strip(),'0')

 def test_bridge_three_real_processes(self):
  from jarvis.history_acceptance import run
  env=os.environ.get('PYTHONPATH');os.environ['PYTHONPATH']=str(pathlib.Path(__file__).resolve().parents[1]/'src')
  try:result=run([sys.executable,'-u','-m','jarvis.ui_bridge']);self.assertTrue(result['delete_survives_restart'])
  finally:
   if env is None:os.environ.pop('PYTHONPATH',None)
   else:os.environ['PYTHONPATH']=env
