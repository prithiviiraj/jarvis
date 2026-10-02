"""Optional evaluation speaker, not the default. Uses approved local synthesis assets.
No monitoring, download, mic or playback on creation. Pause cancels queued/active audio.
"""
import threading
class KokoroSpeaker:
 def __init__(self,synth,output_factory=None):
  self.synth=synth;self.output_factory=output_factory;self.lock=threading.RLock();self.generation=0;self.output=None
 def speak(self,text,generation=None):
  with self.lock:
   ticket=self.generation if generation is None else generation
   if ticket!=self.generation:return
  audio,sr=self.synth.synthesize(text)
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
 def stop(self):
  with self.lock:
   self.generation+=1;output=self.output;self.output=None
  if output:
   try:output.abort()
   except Exception:pass
