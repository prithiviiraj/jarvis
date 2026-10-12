"""Explicit managed local asset preparation. No automatic download or launch."""
import pathlib,threading,copy
from .local_models import CATALOG,detect_hardware,recommendations
from .local_model_files import download_checked,extract_runtime,verify_runtime_receipt,verified
class ModelManager:
 def __init__(self,root,scan=None,download=None,extract=None):
  self.root=pathlib.Path(root);self.scan=scan or detect_hardware;self.download=download or download_checked;self.extract=extract or extract_runtime;self.lock=threading.RLock();self.cancel=threading.Event();self.worker=None;self.hardware=None;self.choices=None;self.pending=None;self.status='Not checked';self.error='';self.progress={};self.installed=[];self.operation=''
 def snapshot(self):
  with self.lock:return copy.deepcopy({'hardware':self.hardware,'recommendations':self.choices,'pending':self.pending,'busy':self.worker is not None and self.worker.is_alive(),'status':self.status,'error':self.error,'progress':self.progress,'installed':self.installed,'operation':self.operation,'scope':'Prepared assets only. No model launch or text/image readiness claimed.'})
 def inspect(self):
  if self.worker is not None and self.worker.is_alive():raise ValueError('Stop current preparation first')
  hw=self.scan(self.root);choices=recommendations(hw)
  with self.lock:self.hardware=hw;self.choices=choices;self.pending=None;self.status='Hardware checked';self.error=''
  return self.snapshot()
 def prepare(self,model_id):
  self.inspect();model=next((m for m in CATALOG['models']if m['id']==model_id),None)
  if not model:raise ValueError('Unknown model')
  option=next(o for o in self.choices['options']if o['id']==model_id)
  if not option['available']:raise ValueError(option['note'])
  review={'id':model_id,'label':model['label'],'bytes':option['bytes'],'files':[{'name':f['name'],'size':f['size'],'sha256':f['sha256'],'source':f['url']}for f in [CATALOG['runtime'],*model['files']]],'destination':str(self.root.resolve()),'scope':'Download/verify only. Keeps partial files on Stop. Does not launch a model, microphone or screen capture.'}
  with self.lock:self.pending=review;self.status='Review download'
  return self.snapshot()
 def start(self,reviewed,confirm=False):
  with self.lock:
   if confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review exact model download first')
   if self.worker is not None and self.worker.is_alive():raise ValueError('Download already running')
   review=copy.deepcopy(self.pending);self.pending=None;self.cancel=threading.Event();self.error='';self.status='Downloading';self.progress={}
   self.worker=threading.Thread(target=self._run,args=(review,self.cancel),daemon=True);self.worker.start()
  return self.snapshot()
 def _run(self,review,cancel):
  try:
   current=self.scan(self.root);option=next(o for o in recommendations(current)['options']if o['id']==review['id'])
   if not option['available']:raise ValueError(option['note'])
   model=next(m for m in CATALOG['models']if m['id']==review['id']);runtime=CATALOG['runtime'];archive=self.root/'downloads'/runtime['name'];destination=self.root/'runtime'/runtime['tag']
   def notify(kind,value):
    with self.lock:self.progress={'stage':kind,**value}
   self.download(runtime,archive,cancel,notify)
   # Existing runtime is never overwritten. Launch will re-verify its receipt.
   if not destination.exists():self.extract(archive,destination,cancel)
   elif not verify_runtime_receipt(destination):raise ValueError('Existing runtime changed; preserved, not ready')
   for f in model['files']:self.download(f,self.root/'models'/model['id']/f['name'],cancel,notify)
   if cancel.is_set():raise InterruptedError('Stopped')
   with self.lock:
    if model['id']not in self.installed:self.installed.append(model['id'])
    self.status='Assets verified; model not started'
  except InterruptedError:
   with self.lock:self.status='Stopped; partial files kept'
  except Exception as e:
   with self.lock:self.status='Preparation failed';self.error=str(e)
 def check_installed(self,consent=False):
  # Multi-GB hashes stay off the UI thread. No download or launch.
  if consent is not True:raise ValueError('Check installed local assets explicitly')
  with self.lock:
   if self.worker and self.worker.is_alive():raise ValueError('Stop current asset preparation first')
   self.cancel=threading.Event();cancel=self.cancel;self.pending=None;self.operation='verify';self.status='Checking installed assets';self.error='';self.installed=[]
   def run():
    try:
     runtime=self.root/'runtime'/CATALOG['runtime']['tag']
     if not verify_runtime_receipt(runtime):raise ValueError('Installed runtime missing or changed; review a verified download')
     found=[]
     for model in CATALOG['models']:
      if cancel.is_set():raise InterruptedError('Stopped')
      if all(verified(self.root/'models'/model['id']/f['name'],f,cancel)for f in model['files']):found.append(model['id'])
     with self.lock:self.installed=found;self.status='Installed assets checked; no model started'if found else'No complete installed model verified'
    except InterruptedError:
     with self.lock:self.status='Installed check stopped'
    except Exception as error:
     with self.lock:self.status='Installed check failed';self.error=str(error)
   self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
  return self.snapshot()
 def stop(self):
  with self.lock:self.cancel.set();self.pending=None;self.status='Stopping; partial files kept'if self.worker and self.worker.is_alive()else'Stopped'
  return self.snapshot()
