"""Local press-and-hold capture. Device opens only while the reviewed keys are held.

Bounded RAM audio, no file recording, transcription or upload in this adapter.
Release submits audio once; stop discards it. No automatic capture after reply.
"""
import threading
class HoldMic:
 def __init__(self,vad,on_utterance,on_state=lambda *a:None,stream_factory=None,max_frames=625):
  self.vad=vad;self.on_utterance=on_utterance;self.on_state=on_state;self.factory=stream_factory;self.max_frames=max_frames;self.lock=threading.RLock();self.frames=[];self.stream=None;self.accepting=False;self.enabled=False;self.on_onset=None;self.generation=0;self.endpointer=None;self.overflow=False
 def start(self,consent=False):
  if consent is not True:raise ValueError('Hold microphone needs session consent')
  with self.lock:self.enabled=True;self.accepting=False
  self.on_state('state','hold Ctrl+Alt to talk')
 def hold(self):
  with self.lock:
   if not self.enabled:raise ValueError('Enable the reviewed hold-to-talk session first')
   if self.stream is not None:return False
   self.generation+=1;ticket=self.generation;self.frames=[];self.overflow=False;self.accepting=True
   def callback(data,count,when,status):
    if not self.lock.acquire(blocking=False):return
    try:
     if ticket!=self.generation or not self.accepting:return
     import numpy as np
     try:
      if status or len(self.frames)>=self.max_frames or count!=512:raise ValueError('Capture buffer failed')
      frame=np.asarray(data)
      if frame.shape!=(512,1)or not np.isfinite(frame).all():raise ValueError('Capture samples failed')
      self.frames.append(frame[:,0].copy())
     except Exception:
      self.overflow=True;self.accepting=False;threading.Thread(target=self._fail_close,args=(ticket,),daemon=True).start()
    finally:self.lock.release()
   if self.factory is None:
    import sounddevice as sd
    factory=sd.InputStream
   else:factory=self.factory
   try:
    self.stream=factory(samplerate=16000,channels=1,dtype='float32',blocksize=512,callback=callback);self.stream.start()
   except Exception:
    self._close_locked();self.frames=[];self.accepting=False;raise RuntimeError('Hold microphone could not open. Check Windows input permission and device.')from None
  self.on_state('state','capturing while Ctrl+Alt held');return True
 def _close_locked(self):
  stream=self.stream;self.stream=None
  if stream:
   try:stream.abort();stream.close()
   except Exception:pass
 def release(self):
  with self.lock:
   self.accepting=False;self.generation+=1;self._close_locked();frames=self.frames;self.frames=[];overflow=self.overflow;self.overflow=False;enabled=self.enabled
  if not enabled:return False
  if overflow:self.on_state('error','Hold audio exceeded the twenty-second limit or device failed. Audio discarded.');return False
  if len(frames)<6:self.on_state('state','Hold longer to speak; audio discarded');return False
  import numpy as np
  self.on_utterance(np.concatenate(frames));return True
 def _fail_close(self,ticket):
  with self.lock:
   if ticket!=self.generation:return
   self.accepting=False;self.generation+=1;self._close_locked();self.frames=[]
 def suspend(self):
  with self.lock:self.accepting=False;self.generation+=1;self._close_locked();self.frames=[]
 def resume(self):
  # Called after a reply by VoiceRuntime. Never opens the device or accepts audio.
  self.on_state('state','hold Ctrl+Alt to talk')
 def close(self):
  with self.lock:self.enabled=False;self.accepting=False;self.generation+=1;self._close_locked();self.frames=[]
