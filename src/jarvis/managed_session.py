"""Explicit owned-model session: verify, launch, test, then route. Inactive by default."""
import copy,threading,time
from .managed_runtime import ManagedRuntime
from .model_probe import ModelProbe
from .local_endpoint import bind,unbind
from .local_models import CATALOG
class ManagedSession:
 def __init__(self,root,runtime=None,probe=None):
  self.runtime=runtime or ManagedRuntime(root);self.probe=probe or ModelProbe(self.runtime);self.lock=threading.RLock();self.worker=None;self.cancel=threading.Event();self.pending=None;self.status='Off';self.error='';self.active=False;self.generation=0
 def snapshot(self):
  with self.lock:return copy.deepcopy({'pending':self.pending,'busy':bool(self.worker and self.worker.is_alive()),'active':self.active,'status':self.status,'error':self.error,'runtime':self.runtime.snapshot(),'test':self.probe.snapshot(),'scope':'Owned local chat and image route only. Synthetic readiness is not desktop/control or speed acceptance.'})
 def prepare(self,model_id):
  with self.lock:
   if self.active or self.worker and self.worker.is_alive():raise ValueError('Stop the current owned session before switching')
   model=next((m for m in CATALOG['models']if m['id']==model_id),None)
   if not model:raise ValueError('Unknown installed model')
   self.pending={'id':model_id,'label':model['label'],'scope':'Verify installed files, launch local llama.cpp using RAM/graphics memory, and test text plus a synthetic red image. On both tests passing, use this owned model for existing local chat/image routes. No download, microphone, camera or screen capture starts. Stop closes only this owned process.'};self.status='Review model start';self.error=''
  return self.snapshot()
 def start(self,reviewed,confirm=False):
  with self.lock:
   if confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review exact model start first')
   if self.worker and self.worker.is_alive():raise ValueError('Owned session already starting')
   model_id=self.pending['id'];self.pending=None;self.cancel=threading.Event();cancel=self.cancel;self.generation+=1;ticket=self.generation;self.status='Verifying and starting';self.error=''
   self.worker=threading.Thread(target=self._run,args=(model_id,cancel,ticket),daemon=True);self.worker.start()
  return self.snapshot()
 def _run(self,model_id,cancel,ticket):
  try:
   with self.lock:
    if cancel.is_set()or ticket!=self.generation:return
    bind(self)
   self.runtime.start(model_id,True,cancel=cancel)
   deadline=time.monotonic()+300
   while not cancel.is_set()and time.monotonic()<deadline:
    state=self.runtime.check()
    if state['state']=='loaded':break
    if state['state']=='failed':raise ValueError(state['error'])
    cancel.wait(.5)
   else:
    if cancel.is_set():return
    raise TimeoutError('Owned model did not load within five minutes')
   with self.lock:
    if cancel.is_set()or ticket!=self.generation:return
    self.status='Testing text and synthetic image';self.probe.start(True)
   deadline=time.monotonic()+70
   while self.probe.snapshot()['busy']and not cancel.is_set()and time.monotonic()<deadline:cancel.wait(.1)
   if cancel.is_set():return
   result=self.probe.snapshot()
   if result['busy']or any(result[k]!='passed'for k in ('text','image')):raise ValueError(result.get('error')or'Local text/image test did not pass')
   with self.lock:
    if cancel.is_set()or ticket!=self.generation:return
    bind(self);self.active=True;self.status='Local text and image route ready'
  except Exception as e:
   with self.lock:
    if ticket==self.generation:self.status='Owned session failed';self.error=type(e).__name__+': '+str(e)
  finally:
   with self.lock:
    if not self.active:self.probe.stop();self.runtime.stop()
 def stop(self):
  self.cancel.set()
  with self.lock:
   self.generation+=1;self.cancel.set();self.pending=None;self.active=False;unbind(self);self.probe.stop();self.runtime.stop();self.status='Off';self.error=''
  return self.snapshot()
 def route(self):
  with self.lock:
   if not self.active:raise ValueError('Owned model is starting, testing or unavailable; no unrelated fallback')
   return self.runtime.route()
 def check(self):
  with self.lock:
   if self.active:
    try:self.runtime.route() # polls the owned process; snapshot alone can be stale
    except ValueError:self.active=False;self.status='Owned model stopped; route unavailable'
   if self.active and self.runtime.snapshot()['state']!='loaded':self.active=False;self.status='Owned model stopped; route unavailable'
  return self.snapshot()
