"""Import only known verified bundled weights. No network or model execution."""
from pathlib import Path
import sys,os,shutil,json,threading
from .models import FILES as SPEECH,digest
from .voice_assets import FILES as VOICES
def specifications():
 from .laya_assets import ASSETS
 specs={name:(sha,cap,None)for name,(_,sha,cap)in SPEECH.items()}
 specs.update({'voices/'+name:(sha,cap,None)for name,(_,sha,cap)in VOICES.items()})
 specs.update({'laya-browser-v32b-161d54d/'+a['name']:(a['sha256'],a['bytes'],a['bytes'])for a in ASSETS})
 manifest=Path(__file__).with_name('embedding-assets.json')
 if manifest.is_file():
  specs.update({'embeddinggemma-2-914f7f8/'+a['name']:(a['sha256'],a['bytes'],a['bytes'])for a in json.loads(manifest.read_text())})
 return specs

def import_verified(source,target,specs=None,notify=lambda *a:None):
 source=Path(source).resolve();target=Path(target).resolve();specs=specs if specs is not None else specifications();installed=[]
 if not source.is_dir():return installed
 for index,(name,(sha,cap,size))in enumerate(specs.items()):
  notify('verifying',name,index,len(specs))
  relative=Path(name)
  if relative.is_absolute()or '..'in relative.parts:raise ValueError('Unsafe bundle asset path')
  src=source/relative;dst=target/relative
  if dst.exists():continue # Preserve owner cache; explicit checks inspect it separately.
  if src.is_symlink()or not src.is_file()or source not in src.resolve().parents:continue
  if src.stat().st_size>cap or(size is not None and src.stat().st_size!=size)or digest(src)!=sha:continue
  # Never overwrite an owner's cache, even if it needs reviewed repair.
  dst.parent.mkdir(parents=True,exist_ok=True)
  if target not in dst.parent.resolve().parents and dst.parent.resolve()!=target:raise ValueError('Unsafe model cache destination')
  tmp=dst.with_name(dst.name+'.bundle-import')
  try:
   notify('importing',name,index,len(specs));shutil.copyfile(src,tmp)
   if digest(tmp)!=sha:raise ValueError('Bundled model changed during import')
   # No replacement of a file another operation just installed.
   try:os.link(tmp,dst);installed.append(name)
   except FileExistsError:pass
  finally:tmp.unlink(missing_ok=True)
 return installed


class BundleSetup:
 def __init__(self):self.lock=threading.RLock();self.busy=False;self.status='No bundled model import running';self.percent=None;self.error='';self.installed=[];self.cancel=threading.Event()
 def stop(self):self.cancel.set()
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'status':self.status,'percent':self.percent,'error':self.error,'installed':list(self.installed),'scope':'Verified bundled assets only, local cache copy. No model inference, download or sensors.'}
 def start(self,source,target,specs=None):
  with self.lock:
   if self.busy:raise ValueError('Bundled setup already running')
   self.busy=True;self.error='';self.percent=0;self.cancel.clear();self.status='Checking bundled models'
  def progress(phase,name,index,total):
   if self.cancel.is_set():raise RuntimeError('Bundled setup stopped; existing files kept')
   with self.lock:self.status=('Checking 'if phase=='verifying'else'Installing ')+name;self.percent=round(index*100/max(1,total))
  def run():
   try:
    installed=import_verified(source,target,specs,progress)
    with self.lock:self.installed=installed;self.percent=100;self.status='Bundled models checked. Sensors remain off.'
   except Exception as e:
    with self.lock:self.error=str(e)[:180];self.status='Bundled setup stopped; use model check to inspect missing files'
   finally:
    with self.lock:self.busy=False
  worker=threading.Thread(target=run,daemon=True);worker.start();return worker
 def start_frozen(self,root):
  if not getattr(sys,'frozen',False):return None
  exe=Path(sys.executable).resolve()
  for source in [exe.parent/'bundled-models',exe.parent.parent/'bundled-models']:
   if source.is_dir():return self.start(source,Path(root)/'models')
  return None
