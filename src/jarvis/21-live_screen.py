"""Local selected-window stream: newest-frame backpressure, no recording or cloud."""
import threading,time,hashlib,base64
from .game_companion import capture
class LiveScreen:
 def __init__(self,notify,source=capture,clock=time.monotonic,interval=.25,max_age=8):
  self.notify=notify;self.source=source;self.clock=clock;self.interval=interval;self.max_age=max_age;self.lock=threading.RLock();self.enabled=False;self.audio=False;self.export=False;self.generation=0;self.target=None;self.model=None;self.busy=False;self.status='Off';self.preview=None;self.latest=None;self.analysis_paused=False;self.focus_epoch=0;self.sequence=0;self.last_comment='';self.last_spoken=-1e20;self.metrics={};self.cancel=threading.Event();self.workers=[]
 def enable(self,target,reviewed,model,consent=False,audio=False,export=False):
  if consent is not True or target!=reviewed or type(audio)is not bool or export is not False:raise ValueError('Choose the exact local window and session audio; recording/export is unavailable')
  if not isinstance(target,dict)or set(target)!={'id','title'}or type(target['id'])is not int or target['id']<=0 or not isinstance(target['title'],str)or not 0<len(target['title'])<=160:raise ValueError('Invalid selected window')
  if self.enabled:raise ValueError('Stop the live screen session before changing window or model')
  if any(t.is_alive()for t in self.workers):raise ValueError('Previous local analysis is still stopping; wait before restart')
  model.verify();self.stop()
  with self.lock:
   self.generation+=1;ticket=self.generation;self.target=dict(target);self.model=model;self.enabled=True;self.audio=audio;self.cancel=threading.Event();cancel=self.cancel;self.status='Starting local capture';self.analysis_paused=False;self.focus_epoch=0;self.sequence=0;self.last_comment='';self.last_spoken=-1e20;self.metrics={}
  self.workers=[threading.Thread(target=self._capture,args=(ticket,cancel),daemon=True),threading.Thread(target=self._analyze,args=(ticket,cancel),daemon=True)]
  for t in self.workers:t.start()
 def valid(self,ticket):return self.enabled and ticket==self.generation
 def stop(self):
  with self.lock:self.generation+=1;self.enabled=False;self.audio=False;self.busy=False;self.cancel.set();self.latest=None;self.preview=None;self.status='Stopped; transient frames cleared'
 def _capture(self,ticket,cancel):
  while not cancel.is_set():
   try:
    frame=self.source(self.target)
    with self.lock:
     if not self.valid(ticket):return
     if frame is None:self.focus_epoch+=1;self.latest=None;self.preview=None;self.status='Paused: selected window is unavailable or not foreground'
     else:
      if not isinstance(frame,bytes)or not frame or len(frame)>200000:raise ValueError('Invalid transient frame')
      self.sequence+=1;self.latest=(self.sequence,self.clock(),frame,self.focus_epoch);self.preview='data:image/jpeg;base64,'+base64.b64encode(frame).decode();self.status='Capture live; local analysis may lag';self.metrics['captured_frames']=self.sequence
   except Exception as e:
    with self.lock:
     if self.valid(ticket):self.stop();self.status='Capture stopped: '+str(e)[:120]
    return
   cancel.wait(self.interval)
 def _analyze(self,ticket,cancel):
  previous=None
  while not cancel.is_set():
   with self.lock:
    if not self.valid(ticket):return
    item=None if self.analysis_paused else self.latest
   if item is None:cancel.wait(.05);continue
   seq,at,frame,epoch=item;digest=(epoch,hashlib.sha256(frame).digest())
   if digest==previous:cancel.wait(.1);continue
   previous=digest
   if self.clock()-at>self.max_age:continue
   started=self.clock()
   with self.lock:self.busy=True
   try:
    row=self.model.analyze(frame)
    if not isinstance(row,dict):raise ValueError('Invalid local scene response')
    with self.lock:
     if not self.valid(ticket):return
     elapsed=self.clock()-started;self.metrics.update(analysis_s=round(elapsed,3),analyzed_sequence=seq,inflight_limit=1)
     if self.analysis_paused or epoch!=self.focus_epoch or self.latest is None or self.clock()-at>self.max_age:previous=None;self.status='Capture live; stale analysis skipped';continue
     comment=row.get('comment','');observed=row.get('observed','')
     if not isinstance(observed,str)or len(observed)>600:raise ValueError('Invalid scene observation')
     if row.get('confidence')=='low' or not isinstance(comment,str)or not comment.strip()or len(comment)>240:continue
     if comment==self.last_comment or self.clock()-self.last_spoken<4:continue
     self.last_comment=comment;self.last_spoken=self.clock()
     self.notify('game-comment',{**row,'audio':self.audio,'generation':ticket,'frame_at':at,'analysis_s':round(elapsed,3),'live':True})
   except RuntimeError as e:
    if 'busy'not in str(e).lower():
     with self.lock:
      if self.valid(ticket):self.stop();self.status='Analysis stopped: '+str(e)[:120]
     return
    with self.lock:
     if self.valid(ticket):self.status='Capture live; local model busy, analysis paused';previous=None
    cancel.wait(.5)
   except Exception as e:
    with self.lock:
     if self.valid(ticket):self.stop();self.status='Analysis stopped: '+str(e)[:120]
    return
   finally:
    with self.lock:
     if ticket==self.generation:self.busy=False
 def poll(self,conversation_busy=False):
  with self.lock:self.analysis_paused=bool(conversation_busy)
  return None
 def snapshot(self):
  with self.lock:return {'enabled':self.enabled,'busy':self.busy,'target':self.target,'audio':self.audio,'export':False,'status':self.status,'metrics':dict(self.metrics),'preview':self.preview,'scope':'Selected foreground window only; newest frame in RAM; no recording, external broadcast, cloud fallback or export. Capture rate is not model response latency.'}
