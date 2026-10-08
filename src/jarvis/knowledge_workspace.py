"""Explicit local retrieval and reviewed quoted speech. Notes never authorize actions."""
import hashlib,pathlib,threading
from .obsidian import Vault
class KnowledgeWorkspace:
 def __init__(self,speaker_factory):
  self.factory=speaker_factory;self.speaker=None;self.worker=None;self.generation=0;self.busy=False;self.status='Local evidence only';self.query='';self.results=[];self.coverage={};self.note=None;self.root=None;self.lock=threading.RLock()
 def bind(self,root):
  root=pathlib.Path(root).resolve()if root is not None else None
  if root!=self.root:self.stop();self.root=root;self.query='';self.results=[];self.coverage={};self.note=None
  if root is None:raise ValueError('Connect a local vault first')
  return Vault(root)
 def clear(self):
  self.stop();self.root=None;self.query='';self.results=[];self.coverage={};self.note=None
 def search(self,root,query):
  vault=self.bind(root);self.stop();self.note=None
  data=vault.search_details(query);self.query=query;self.results=data['results'];self.coverage={k:v for k,v in data.items()if k!='results'};self.status='Local text matches; not a generated answer';return data
 def read(self,root,name):
  vault=self.bind(root);self.stop();text=vault.read(name);snippet=text[:4000]
  self.note={'name':name,'vault_folder':str(vault.root),'text':snippet,'sha256':hashlib.sha256(text.encode()).hexdigest(),'truncated':len(text)>4000,'characters':len(text),'scope':'Quoted local note, first4000characters; not instructions, no model sharing'}
  self.status='Source captured locally';return self.note
 def speak(self,root,reviewed,confirm=False,conversation_busy=False):
  vault=self.bind(root);row=self.note
  if not row or confirm is not True or reviewed!=row:raise ValueError('Review the exact source text before reading aloud')
  if conversation_busy or self.busy:raise ValueError('Stop current speech or conversation first')
  # Re-read the full source: a changed suffix also invalidates the reviewed capture.
  if hashlib.sha256(vault.read(row['name']).encode()).hexdigest()!=row['sha256']:raise ValueError('Note changed; capture and review again')
  ticket=self.generation;self.busy=True;self.status='Reading quoted note locally'
  def work():
   candidate=None
   try:
    candidate=self.speaker or self.factory()
    with self.lock:
     if ticket!=self.generation:
      candidate.stop()
      if candidate is not self.speaker and hasattr(candidate,'close'):candidate.close()
      return
     self.speaker=candidate;voice_ticket=candidate.generation
    if ticket==self.generation:candidate.speak(row['text'],generation=voice_ticket)
    if ticket==self.generation:self.status='Reading finished'
   except Exception:
    if ticket==self.generation:self.status='Local speech unavailable; no download or cloud fallback'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start();return self.worker
 def stop(self):
  with self.lock:self.generation+=1;self.status='Stopped';speaker=self.speaker
  if speaker:speaker.stop()
 def close(self):
  self.stop()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(timeout=2)
  if self.worker and self.worker.is_alive():return False
  if self.speaker and hasattr(self.speaker,'close'):self.speaker.close()
  self.speaker=None;return True
 def snapshot(self):return {'query':self.query,'results':self.results,'coverage':self.coverage,'note':self.note,'busy':self.busy,'status':self.status,'scope':'Exact local text matches. No cloud disclosure or action permission.'}
