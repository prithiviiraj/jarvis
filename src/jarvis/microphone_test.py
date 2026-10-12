"""Visible, consented five-second level test. No transcription/save/cloud route."""
import threading,time,math
class MicrophoneTest:
 def __init__(self,factory=None,clock=time.monotonic,wait=None):
  self.factory=factory;self.clock=clock;self.wait=wait or (lambda event: event.wait(5));self.lock=threading.RLock();self.stream=None;self.worker=None;self.cancel=threading.Event();self.status='Not tested';self.error='';self.level=0.;self.peak=0.;self.frames=0
 def snapshot(self):
  with self.lock:return {'busy':bool(self.worker and self.worker.is_alive()),'status':self.status,'error':self.error,'level':self.level,'peak':self.peak,'frames':self.frames,'scope':'Five-second local level test. No audio saved, transcription or cloud upload.'}
 def start(self,consent=False):
  if consent is not True:raise ValueError('Start the reviewed five-second microphone test explicitly')
  with self.lock:
   if self.worker and self.worker.is_alive():raise ValueError('Microphone test already running')
   self.cancel=threading.Event();self.status='Testing microphone for five seconds';self.error='';self.level=0.;self.peak=0.;self.frames=0;self.worker=threading.Thread(target=self._run,args=(self.cancel,),daemon=True);state=self.snapshot();state['busy']=True;self.worker.start()
  return state
 def _run(self,cancel):
  stream=None
  try:
   factory=self.factory
   if factory is None:
    import sounddevice
    factory=sounddevice.InputStream
   def callback(data,count,when,status):
    # Audio callbacks cannot wait on UI/stop locks while a device is closing.
    if cancel.is_set()or not self.lock.acquire(blocking=False):return
    try:
     if cancel.is_set():return
     if status:raise ValueError('Microphone buffer failed')
     values=data[:,0];rms=math.sqrt(float((values*values).mean()))
     if not math.isfinite(rms):raise ValueError('Invalid microphone samples')
     self.level=min(1.,rms);self.peak=max(self.peak,self.level);self.frames+=count
    except Exception:
     self.error='Microphone buffer or samples failed';self.status='Test failed';cancel.set()
    finally:self.lock.release()
   stream=factory(samplerate=16000,channels=1,dtype='float32',blocksize=512,callback=callback)
   with self.lock:self.stream=stream
   if not cancel.is_set():stream.start();self.wait(cancel)
   with self.lock:
    if not self.error:self.status='Stopped'if cancel.is_set()else'Working capture; speak louder or check input'if self.frames and self.peak<.005 else'Working capture and sound detected'if self.frames else'No samples received; check device and permission'
  except Exception as e:
   with self.lock:self.error=type(e).__name__+': '+str(e);self.status='Microphone unavailable; check Windows permission/input'
  finally:
   if stream:
    try:stream.abort();stream.close()
    except Exception:pass
   with self.lock:self.stream=None;self.level=0.
 def stop(self):
  self.cancel.set()
  stream=self.stream
  if stream:
   try:stream.abort()
   except Exception:pass
  return self.snapshot()
