"""Explicit local speech assets setup. Never opens a mic or sends audio."""
import threading
from .paths import ensure_layout
from . import models,voice_assets
class VoiceSetup:
 def __init__(self):
  self.lock=threading.RLock();self.busy=False;self.status='not checked';self.error='';self.cancel=threading.Event();self.checked=False;self.ready=False
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'status':self.status,'error':self.error,'ready':self.ready}
 def start(self,consent=False,check=False):
  if not check and consent is not True:raise ValueError('Approve roughly500MB local speech model download first.')
  with self.lock:
   if self.busy:raise ValueError('Voice setup is already running.')
   self.busy=True;self.cancel.clear();self.error='';self.status='checking verified speech assets'
  def run():
   try:
    cache=ensure_layout()/'models'
    def progress(name,total):
     with self.lock:self.status='Downloading '+name+' / '+str(total//1048576)+'MB'
    if not check:
     models.download(cache,consent=True,notify=progress,cancel=self.cancel)
     voice_assets.download(cache/'voices',consent=True,notify=progress,cancel=self.cancel)
    ready=models.ready(cache) and voice_assets.ready(cache/'voices')
    with self.lock:self.ready=ready;self.checked=True;self.status='Ready - microphone OFF' if ready else 'Speech assets missing - choose Download local voice models'
   except Exception as exc:
    with self.lock:self.error=str(exc)[:300];self.status='Setup stopped; existing models preserved'
   finally:
    with self.lock:self.busy=False
  threading.Thread(target=run,daemon=True).start()
 def stop(self):self.cancel.set()
