"""Opt-in English static-embedding candidates. No sends, writes or model authority."""
from pathlib import Path
import hashlib,json,os,time
ASSETS={
 'config.json':(202,'90a28f209637bea10a440b69c1b41b72a24c4cb7d378030172f89c671c254c80'),
 'model.safetensors':(15118424,'8a7140edd17ffab30ddcff1135eda127df57abfae856203dbd7b3d061295c31a'),
 'tokenizer.json':(683666,'e67e803f624fb4d67dea1c730d06e1067e1b14d830e2c2202569e3ef0f70bb50')}
REVISION='9b3cff412d30be9ae8603fe10224c224f3401869'
def checked_model(folder):
 root=Path(folder).resolve(strict=True)
 for name,(size,digest)in ASSETS.items():
  p=root/name
  if p.is_symlink()or not p.is_file()or p.stat().st_size!=size:raise ValueError('Verified embedding assets missing')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Embedding checksum mismatch')
 from model2vec import StaticModel
 return StaticModel.from_pretrained(root)
def search(vault,query,model=None,consent=False,limit=10):
 if consent is not True:raise ValueError('Allow local semantic vault search first')
 if model is None:raise ValueError('Install and verify optional English embedding model first')
 if not isinstance(query,str)or not query.strip()or len(query)>100:raise ValueError('Enter a short search')
 if not query.isascii():raise ValueError('This experimental model is English-only; use exact vault search')
 if type(limit)is not int or not 1<=limit<=30:raise ValueError('Invalid result limit')
 import numpy as np
 names=[];texts=[];skipped=0;scanned=0;reason='complete';deadline=time.monotonic()+.75
 for base,dirs,files in os.walk(vault.root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if not d.startswith('.')and not(Path(base)/d).is_symlink())
  for f in sorted(files):
   if f.startswith('.')or not f.endswith('.md')or(Path(base)/f).is_symlink():continue
   if scanned>=100:reason='note-limit';break
   if time.monotonic()>deadline:reason='time-limit';break
   scanned+=1;name=(Path(base)/f).relative_to(vault.root).as_posix()
   try:text=vault.read(name)
   except(ValueError,OSError,UnicodeError):skipped+=1;continue
   names.append(name);texts.append(text[:4096])
  if reason!='complete':break
 if not names:return {'results':[],'scanned':scanned,'skipped':skipped,'complete':reason=='complete'and skipped==0,'scope':'English candidates only; no context sent or permission granted'}
 vectors=np.asarray(model.encode(texts),dtype='float32');q=np.asarray(model.encode([query])[0],dtype='float32')
 if vectors.shape!=(len(texts),q.size)or not np.isfinite(vectors).all()or not np.isfinite(q).all():raise ValueError('Invalid embedding result')
 scores=vectors@q/(np.linalg.norm(vectors,axis=1)*np.linalg.norm(q)+1e-12);order=np.argsort(-scores,kind='stable')[:limit]
 return {'results':[{'name':names[int(i)],'preview':texts[int(i)][:160],'score':float(scores[i])}for i in order],'scanned':scanned,'skipped':skipped,'complete':reason=='complete'and skipped==0,'reason':reason,'scope':'English candidates only, first4096characters per note; similarity is not truth or authority; no context sent'}
class SearchSetup:
 def __init__(self):
  import threading
  self.busy=False;self.status='Not checked';self.error='';self.cancel=threading.Event();self.model=None
 def start(self,consent=False,check=False):
  if self.busy:raise ValueError('Embedding setup busy')
  if not check and consent is not True:raise ValueError('Review embedding download first')
  import threading
  from ..paths import data_root
  self.busy=True;self.error='';self.cancel.clear()
  def run():
   try:
    root=data_root()/'models'/'potion4';root.mkdir(parents=True,exist_ok=True)
    if not check:
     from ..models import fetch_verified,verified_http
     for name,(size,sha)in ASSETS.items():
      p=root/name
      if not p.is_file()or p.stat().st_size!=size or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:fetch_verified(verified_http(),'https://huggingface.co/minishlab/potion-base-4M/resolve/'+REVISION+'/'+name,p,sha,size,cancel=self.cancel)
    if self.cancel.is_set():return
    candidate=checked_model(root)
    if not self.cancel.is_set():self.model=candidate;self.status='Verified English search model ready'
   except Exception as e:self.error=str(e)[:160];self.status='Search model unavailable; exact search still works'
   finally:self.busy=False
  worker=threading.Thread(target=run,daemon=True);worker.start();return worker
 def stop(self):self.cancel.set();self.model=None;self.status='Semantic search stopped; installed files preserved'
 def snapshot(self):return {'busy':self.busy,'ready':self.model is not None,'status':self.status,'error':self.error,'model_bytes':sum(x[0]for x in ASSETS.values())}
class VaultSearch:
 def __init__(self,setup):
  import threading
  self.setup=setup;self.lock=threading.RLock();self.generation=0;self.busy=False;self.results=[];self.details={};self.error=''
 def start(self,vault,query,consent=False):
  if consent is not True:raise ValueError('Review local semantic search first')
  if self.setup.model is None:raise ValueError('Verify optional English search model first')
  import threading
  with self.lock:
   self.generation+=1;generation=self.generation;self.busy=True;self.results=[];self.details={};self.error='';model=self.setup.model
  def run():
   try:
    result=search(vault,query,model,True)
    with self.lock:
     if generation==self.generation:self.results=result['results'];self.details=result
   except Exception as e:
    with self.lock:
     if generation==self.generation:self.error=str(e)[:160]
   finally:
    with self.lock:
     if generation==self.generation:self.busy=False
  worker=threading.Thread(target=run,daemon=True);worker.start();return worker
 def stop(self):
  with self.lock:self.generation+=1;self.busy=False;self.results=[];self.details={};self.error=''
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'results':list(self.results),'details':dict(self.details),'error':self.error,'scope':'optional English local candidates only; no automatic model context'}
