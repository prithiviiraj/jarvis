"""Explicit local speech assets setup. Never opens a mic or sends audio."""
import threading
from .paths import ensure_layout
from . import models,voice_assets
class VoiceSetup:
 def __init__(self):
  self.lock=threading.RLock();self.busy=False;self.status='not checked';self.error='';self.cancel=threading.Event();self.checked=False;self.ready=False;self.kitten_ready=False;self.engine=None
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'status':self.status,'error':self.error,'ready':self.ready,'kitten_ready':self.kitten_ready,'checked':self.checked,'engine':self.engine}
 def select(self,engine):
  if engine not in ('kokoro','kitten','pocket'):raise ValueError('Unsupported voice engine')
  with self.lock:
   if self.busy:raise ValueError('Wait for model setup before changing speech engine')
   self.engine=engine;self.checked=False;self.ready=False;self.error='';self.status=engine.title()+' assets not checked - choose Check local voice models'
 def start(self,consent=False,check=False,engine='kokoro'):
  if engine not in ('kokoro','kitten','pocket'):raise ValueError('Unsupported voice engine')
  if not check and consent is not True:raise ValueError('Review the selected engine and shared recognition download first.')
  with self.lock:
   if self.busy:raise ValueError('Voice setup is already running.')
   self.busy=True;self.cancel.clear();self.error='';self.engine=engine;self.ready=False;self.checked=False;self.status='Checking verified '+engine.title()+' and shared speech assets'
  def run():
   try:
    cache=ensure_layout()/'models'
    def progress(name,total):
     with self.lock:self.status='Downloading '+name+' / '+str(total//1048576)+'MB'
    if not check:
     models.download(cache,consent=True,notify=progress,cancel=self.cancel)
     if engine=='kokoro':voice_assets.download(cache/'voices',consent=True,notify=progress,cancel=self.cancel)
     elif engine=='pocket':
      from . import pocket_assets
      pocket_assets.download(cache/'pocket',consent=True,notify=progress,cancel=self.cancel)
     else:
      from . import kitten_assets
      kitten_assets.download(cache/'kitten',consent=True,notify=progress,cancel=self.cancel)
    from . import kitten_assets
    self.kitten_ready=models.ready(cache)and kitten_assets.ready(cache/'kitten')
    from . import pocket_assets
    ready=models.ready(cache) and (voice_assets.ready(cache/'voices')if engine=='kokoro'else pocket_assets.ready(cache/'pocket')if engine=='pocket'else self.kitten_ready)
    with self.lock:self.ready=ready;self.checked=True;self.status=engine.title()+' assets ready - microphone OFF' if ready else engine.title()+' or shared speech assets missing - choose Download local voice models'
   except Exception as exc:
    with self.lock:self.error=str(exc)[:300];self.status='Setup stopped; existing models preserved'
   finally:
    with self.lock:self.busy=False
  threading.Thread(target=run,daemon=True).start()
 def stop(self):self.cancel.set()
