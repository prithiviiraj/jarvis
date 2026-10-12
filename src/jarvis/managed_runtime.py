"""Owned llama.cpp process boundary. Inactive until explicit verified start.

No shell, external bind, static port, model download, automatic restart or
unrelated process cleanup. Endpoint credentials remain in RAM.
"""
import json,pathlib,secrets,socket,subprocess,threading,urllib.request
from .local_models import CATALOG
from .local_model_files import verified

class ManagedRuntime:
 def __init__(self,root,spawn=None,health=None,log=None):
  self.root=pathlib.Path(root).resolve();self.spawn=spawn or subprocess.Popen;self.health=health or self._health;self.child=None;self.endpoint=None;self.state='off';self.error='';self.lock=threading.RLock();self.log=log
 def snapshot(self):
  with self.lock:return{'state':self.state,'error':self.error,'model':self.endpoint['model']if self.endpoint else'','scope':'Owned local runtime, not tested text/image readiness'}
 def start(self,model_id,consent=False,cancel=None):
  if consent is not True:raise ValueError('Start the reviewed local model explicitly')
  with self.lock:
   if self.child is not None:raise ValueError('Stop the owned local model before switching')
  m=next((x for x in CATALOG['models']if x['id']==model_id),None)
  if not m:raise ValueError('Unknown local model')
  model_dir=self.root/'models'/model_id;runtime=self.root/'runtime'/CATALOG['runtime']['tag'];exe=runtime/'llama-server.exe'
  # Runtime integrity receipt must bind every extracted executable/DLL before launch.
  try:receipt=json.loads((runtime/'verified-files.json').read_text())
  except (ValueError,OSError):raise ValueError('Runtime verification receipt missing')from None
  import hashlib
  if receipt.get('archive_sha256')!=CATALOG['runtime']['sha256']:raise ValueError('Wrong runtime receipt')
  files=receipt.get('files')
  if not isinstance(files,dict) or 'llama-server.exe'not in files:raise ValueError('Invalid runtime receipt')
  for name,digest in files.items():
   if cancel and cancel.is_set():raise InterruptedError('Owned start stopped')
   p=runtime/name
   if pathlib.PurePosixPath(name).is_absolute()or '..'in pathlib.PurePosixPath(name).parts or '\\'in name or ':'in name or not isinstance(digest,str)or len(digest)!=64 or p.is_symlink()or not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Runtime files changed; verify again')
  actual={str(p.relative_to(runtime)).replace('\\','/')for p in runtime.rglob('*')if p.is_file()and p.suffix.lower()in('.exe','.dll')}
  expected={n for n in files if pathlib.PurePosixPath(n).suffix.lower()in('.exe','.dll')}
  if actual!=expected:raise ValueError('Runtime executable set changed')
  for f in m['files']:
   if not verified(model_dir/f['name'],f,cancel):raise ValueError('Model files changed or missing; verify again')
  if cancel and cancel.is_set():raise InterruptedError('Owned start stopped')
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  token=secrets.token_urlsafe(32)
  args=[str(exe),'--host','127.0.0.1','--port',str(port),'--api-key',token,'--alias',model_id,'--jinja','--model',str(model_dir/m['files'][0]['name']),'--mmproj',str(model_dir/m['files'][1]['name']),'--ctx-size','8192','--parallel','1','--n-gpu-layers','auto','--fit','on','--no-webui','--no-repack']
  kwargs={'cwd':str(runtime),'stdin':subprocess.DEVNULL,'stdout':self.log if self.log is not None else subprocess.DEVNULL,'stderr':self.log if self.log is not None else subprocess.DEVNULL}
  if hasattr(subprocess,'CREATE_NO_WINDOW'):kwargs['creationflags']=subprocess.CREATE_NO_WINDOW
  with self.lock:
   if self.child is not None:raise ValueError('Another owned start already loaded')
   if cancel and cancel.is_set():raise InterruptedError('Owned start stopped')
   self.child=self.spawn(args,**kwargs);self.endpoint={'url':f'http://127.0.0.1:{port}/v1','key':token,'model':model_id};self.state='loading';self.error=''
   return self.snapshot()
 def check(self):
  with self.lock:
   if not self.child:return self.snapshot()
   if self.child.poll()is not None:self.state='failed';self.error='Owned model process stopped';self.child=None;self.endpoint=None;return self.snapshot()
   try:
    if self.health(self.endpoint):self.state='loaded';self.error=''
   except Exception:self.error='Still loading or local health unavailable'
   return self.snapshot()
 def route(self):
  with self.lock:
   if self.child is not None and self.child.poll()is not None:self.state='failed';self.error='Owned model process stopped';self.child=None;self.endpoint=None
   if self.state!='loaded'or not self.endpoint:raise ValueError('Managed local model not loaded')
   return dict(self.endpoint)
 def stop(self):
  with self.lock:
   child=self.child;self.child=None;self.endpoint=None;self.state='off';self.error=''
  if child:
   try:child.terminate();child.wait(timeout=5)
   except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
  return self.snapshot()
 @staticmethod
 def _health(endpoint):
  from .router import local_http
  req=urllib.request.Request(endpoint['url'].removesuffix('/v1')+'/health',headers={'Authorization':'Bearer '+endpoint['key']})
  with local_http().open(req,timeout=3)as r:return r.status==200
