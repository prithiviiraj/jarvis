"""Local, bounded conversation archive. No sensors, keys, or network payloads."""
import json,sqlite3,time,uuid,threading,re
from pathlib import Path
def valid_name(name):return isinstance(name,str)and (name=='You'or bool(re.fullmatch(r'[A-Z][A-Z0-9_-]{1,23}',name)))
class ChatHistory:
 def __init__(self,path,max_chats=50,max_messages=200):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.max_chats=max_chats;self.max_messages=max_messages;self.lock=threading.RLock()
  self.db=sqlite3.connect(self.path,check_same_thread=False)
  try:
   self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA secure_delete=ON');self.db.execute('CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY,title TEXT NOT NULL,updated REAL NOT NULL,messages TEXT NOT NULL)');self.db.commit()
  except Exception:self.db.close();raise
 def new(self):return uuid.uuid4().hex
 def save(self,chat_id,messages):
  if not isinstance(chat_id,str)or len(chat_id)!=32 or any(c not in '0123456789abcdef' for c in chat_id):raise ValueError('Invalid conversation')
  clean=[]
  for row in messages[-self.max_messages:]:
   if not isinstance(row,dict)or not valid_name(row.get('name'))or not isinstance(row.get('text'),str):raise ValueError('Invalid message')
   item={'name':row['name'],'text':row['text'][:4000]}
   for key in ('provider','model','slot'):
    if key in row:
     if not isinstance(row[key],str)or len(row[key])>200:raise ValueError('Invalid response source')
     item[key]=row[key]
   if 'cloud'in row:
    if type(row['cloud'])is not bool:raise ValueError('Invalid source location')
    item['cloud']=row['cloud']
   clean.append(item)
  title=next((x['text'].replace('\n',' ')[:70]for x in clean if x['name']=='You'),'New conversation')
  with self.lock,self.db:
   self.db.execute('INSERT OR REPLACE INTO chats VALUES (?,?,?,?)',(chat_id,title,time.time(),json.dumps(clean,ensure_ascii=False)))
   self.db.execute('DELETE FROM chats WHERE id NOT IN (SELECT id FROM chats ORDER BY updated DESC LIMIT ?)',(self.max_chats,))
 def list(self):
  with self.lock:return [{'id':r[0],'title':r[1],'updated':r[2]}for r in self.db.execute('SELECT id,title,updated FROM chats ORDER BY updated DESC')]
 def load(self,chat_id):
  with self.lock:
   row=self.db.execute('SELECT messages FROM chats WHERE id=?',(chat_id,)).fetchone()
   if not row:raise ValueError('Conversation not found')
   rows=json.loads(row[0])
   if not isinstance(rows,list)or len(rows)>self.max_messages or any(not isinstance(r,dict)or not valid_name(r.get('name'))or not isinstance(r.get('text'),str)or len(r['text'])>4000 for r in rows):raise ValueError('Saved conversation invalid; file preserved')
   for r in rows:
    if any(k in r and (not isinstance(r[k],str)or len(r[k])>200)for k in ('provider','model','slot'))or ('cloud'in r and type(r['cloud'])is not bool):raise ValueError('Saved source invalid; file preserved')
   legacy=''.join(('K','AI'))
   return [{**r,'name':'SILA'if r['name']==legacy else r['name']}for r in rows]
 def delete(self,chat_id):
  with self.lock,self.db:self.db.execute('DELETE FROM chats WHERE id=?',(chat_id,))
  with self.lock:self.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
 def clear(self):
  with self.lock,self.db:self.db.execute('DELETE FROM chats')
  with self.lock:self.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
 def close(self):self.db.close()
