"""Frozen subprocess archive acceptance, temporary data only."""
import json,subprocess,sys,tempfile,pathlib,os

def run(exe):
 with tempfile.TemporaryDirectory()as folder:
  env=dict(os.environ,JARVIS_DATA_DIR=folder)
  def session(commands):
   process=subprocess.Popen([exe] if isinstance(exe,str) else exe,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
   rows=[]
   try:
    for command in commands:
     process.stdin.write(json.dumps(command)+'\n');process.stdin.flush();row=json.loads(process.stdout.readline());assert row['ok'],row;rows.append(row['data'])
    process.stdin.write('{"command":"close"}\n');process.stdin.flush();process.stdout.readline();process.wait(timeout=15)
   finally:
    if process.poll()is None:process.kill();process.wait()
   return rows
  # Seed only a synthetic transcript, not owner data or a model request.
  from .chat_history import ChatHistory
  h=ChatHistory(pathlib.Path(folder)/'chat-history.sqlite');i=h.new();h.save(i,[{'name':'You','text':'Frozen restart greeting'},{'name':'JARVIS','text':'Local archive restored'}]);h.close()
  first=session([{'command':'status'}]);assert first[0]['messages'][1]['text']=='Local archive restored'
  second=session([{'command':'history-open','chat_id':i},{'command':'history-delete','chat_id':i,'confirm':True}]);assert not second[-1]['history']
  third=session([{'command':'status'}]);assert not third[0]['history']
  return {'frozen_process_restart':True,'restored_messages':True,'delete_survives_restart':True,'synthetic_data_only':True}
