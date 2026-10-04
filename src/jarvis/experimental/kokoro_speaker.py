"""Optional evaluation speaker, not the default. Uses approved local synthesis assets.
No monitoring, download, mic or playback on creation. Pause cancels queued/active audio.
"""
import threading
class KokoroSpeaker:
 def __init__(self,synth,output_factory=None):
  self.synth=synth;self.output_factory=output_factory;self.lock=threading.RLock();self.generation=0;self.output=None;self.profiles=None;self.profile=None;self.playback_event=lambda *a:None
 def select_profile(self,name):
  with self.lock:
   if self.profiles is None or name not in self.profiles:raise ValueError('Voice profile unavailable')
   if self.output is not None:raise RuntimeError('Cannot change voice during playback')
   self.synth=self.profiles[name];self.profile=name
 def speak(self,text,generation=None):
  with self.lock:
   ticket=self.generation if generation is None else generation
   if ticket!=self.generation:return
  prepared=self.prepare(text,ticket)
  if prepared is not None:self.play_prepared(prepared,ticket)
 def prepare(self,text,generation=None):
  with self.lock:
   ticket=self.generation if generation is None else generation
   if ticket!=self.generation:return None
  from ..speech_text import speech_text
  text=speech_text(text)
  if not text:return None
  audio,sr=self.synth.synthesize(text)
  with self.lock:
   if ticket!=self.generation:return None
  return text,audio,sr
 def play_prepared(self,prepared,generation=None):
  ticket=self.generation if generation is None else generation
  text,audio,sr=prepared
  # Synthesis can finish after Pause. Do not acquire/play an output then.
  with self.lock:
   if ticket!=self.generation:return
   if self.output_factory is None:
    import sounddevice
    output=sounddevice.OutputStream(samplerate=sr,channels=1,dtype='float32',blocksize=512)
   else:output=self.output_factory(sr)
   self.output=output
  try:
   with self.lock:
    if ticket!=self.generation:return
    output.start()
    self.playback_event('start',text,self.profile,sr,len(audio))
   for offset in range(0,len(audio),512):
    with self.lock:
     if ticket!=self.generation:return
    output.write(audio[offset:offset+512])
   with self.lock:
    if ticket==self.generation:output.stop()
  finally:
   try:output.close()
   finally:
    with self.lock:
     if self.output is output:self.output=None
     self.playback_event('finish','',self.profile,sr,0)
 def stop(self):
  with self.lock:
   self.generation+=1;output=self.output;self.output=None
  self.playback_event('finish','',self.profile,0,0)
  if output:
   try:output.abort()
   except Exception:pass
