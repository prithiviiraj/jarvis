"""Pinned local Laya assets. Check/download only, never inference or actions."""
import hashlib,json,pathlib,threading,urllib.request
from .paths import data_root
ASSETS=json.loads((pathlib.Path(__file__).parent/'laya-assets.json').read_text())
TOTAL_BYTES=sum(a['bytes'] for a in ASSETS)
def cache():return data_root()/'models'/'laya-browser-v32b-161d54d'
def valid(path,asset):
 if not path.is_file() or path.stat().st_size!=asset['bytes']:return False
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()==asset['sha256']
def ready(root):return all(valid(root/a['name'],a) for a in ASSETS)
def download(root,consent=False,cancel=None,notify=lambda *a:None):
 if consent is not True:raise ValueError('Review the 1.32GB Laya model download first')
 cancel=cancel or threading.Event();root=pathlib.Path(root)
 for a in ASSETS:
  if cancel.is_set():raise ValueError('Laya download cancelled')
  path=root/a['name']
  if valid(path,a):continue
  path.parent.mkdir(parents=True,exist_ok=True);part=path.with_suffix(path.suffix+'.part')
  try:
   with urllib.request.urlopen(a['url'],timeout=60)as response,part.open('wb')as f:
    size=0
    while True:
     if cancel.is_set():raise ValueError('Laya download cancelled')
     b=response.read(1048576)
     if not b:break
     size+=len(b)
     if size>a['bytes']:raise ValueError('Oversize Laya asset')
     f.write(b);notify(a['name'],size,a['bytes'])
   if not valid(part,a):raise ValueError('Laya model integrity check failed')
   part.replace(path)
  finally:part.unlink(missing_ok=True)
class LayaSetup:
 def __init__(self):
  self.lock=threading.RLock();self.cancel=threading.Event();self.busy=False;self.checked=False;self.ready=False;self.status='Laya model not checked';self.error=''
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'checked':self.checked,'ready':self.ready,'status':self.status,'error':self.error,'model_bytes':TOTAL_BYTES}
 def stop(self):self.cancel.set()
 def start(self,consent=False,check=False):
  if not check and consent is not True:raise ValueError('Review the Laya model download first')
  with self.lock:
   if self.busy:raise ValueError('Laya model setup already running')
   self.busy=True;self.cancel.clear();self.ready=False;self.checked=False;self.error='';self.status='Checking verified Laya model assets'
  def run():
   try:
    root=cache()
    def progress(name,size,total):
     with self.lock:self.status='Downloading Laya '+name+': '+str(size//1048576)+' / '+str(total//1048576)+'MB'
    if not check:download(root,consent=True,cancel=self.cancel,notify=progress)
    ok=ready(root)
    with self.lock:self.ready=ok;self.checked=True;self.status='Laya model verified; engine stopped' if ok else 'Laya model missing; review Download Laya model'
   except Exception as error:
    with self.lock:self.error=type(error).__name__+': '+str(error)[:200];self.status='Laya setup stopped; existing verified files preserved'
   finally:
    with self.lock:self.busy=False
  thread=threading.Thread(target=run,daemon=True);thread.start();return thread
