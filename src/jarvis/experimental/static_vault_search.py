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
 names=[];texts=[];skipped=0;reason='complete';deadline=time.monotonic()+.75
 for base,dirs,files in os.walk(vault.root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if not d.startswith('.')and not(Path(base)/d).is_symlink())
  for f in sorted(files):
   if f.startswith('.')or not f.endswith('.md')or(Path(base)/f).is_symlink():continue
   if len(names)>=100:reason='note-limit';break
   if time.monotonic()>deadline:reason='time-limit';break
   name=(Path(base)/f).relative_to(vault.root).as_posix()
   try:text=vault.read(name)
   except(ValueError,OSError,UnicodeError):skipped+=1;continue
   names.append(name);texts.append(text[:4096])
  if reason!='complete':break
 if not names:return {'results':[],'scanned':0,'skipped':skipped,'complete':skipped==0,'scope':'English candidates only; no context sent or permission granted'}
 vectors=np.asarray(model.encode(texts),dtype='float32');q=np.asarray(model.encode([query])[0],dtype='float32')
 if vectors.shape!=(len(texts),q.size)or not np.isfinite(vectors).all()or not np.isfinite(q).all():raise ValueError('Invalid embedding result')
 scores=vectors@q/(np.linalg.norm(vectors,axis=1)*np.linalg.norm(q)+1e-12);order=np.argsort(-scores,kind='stable')[:limit]
 return {'results':[{'name':names[int(i)],'preview':texts[int(i)][:160],'score':float(scores[i])}for i in order],'scanned':len(names),'skipped':skipped,'complete':reason=='complete'and skipped==0,'reason':reason,'scope':'English candidates only, first4096characters per note; similarity is not truth or authority; no context sent'}
