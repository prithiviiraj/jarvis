"""Bigfoot-style prepared acknowledgement. No synthesis on the request path.

Adapted from Bigfoot95f7ffdb main/audio.js and kokoro.js (GPL-3.0-or-later).
Only plays an explicitly prepared local clip on the current owned speaker.
"""
import threading,time
class FastAck:
 def __init__(self,speaker,clock=time.monotonic):
  self.speaker=speaker;self.clock=clock;self.clips={};self.lock=threading.RLock();self.worker=None;self.error='';self.metrics={}
 def prepare(self,persona):
  """Run during explicit voice preparation, never inside acknowledgement()."""
  self.speaker.select_profile(persona);clip=self.speaker.prepare('On it.',self.speaker.generation)
  if clip is None:raise ValueError('Acknowledgement preparation stopped')
  with self.lock:self.clips[persona]=clip
 def acknowledge(self,persona,generation,cancel):
  with self.lock:
   if cancel.is_set()or generation!=self.speaker.generation or self.speaker.profile!=persona or self.worker and self.worker.is_alive():return False
   clip=self.clips.get(persona)
   if clip is None:return False
   self.metrics={'scope':'Prepared clip dispatch only; not measured audible hardware latency'};self.error='';started=self.clock()
   def play():
    try:
     if cancel.is_set()or generation!=self.speaker.generation:return
     self.speaker.play_prepared(clip,generation)
     with self.lock:self.metrics['playback_adapter_s']=self.clock()-started
    except Exception as e:
     with self.lock:self.error=type(e).__name__
   self.worker=threading.Thread(target=play,daemon=True);self.worker.start();return True
 def wait(self,cancel):
  """Reply output waits for short ack so two outputs never overlap."""
  worker=self.worker
  while worker and worker.is_alive():
   if cancel.wait(.01):return False
  return not cancel.is_set()
 def clear(self):
  with self.lock:self.clips={};self.metrics={};self.error=''
