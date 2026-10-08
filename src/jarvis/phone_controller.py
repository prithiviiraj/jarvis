"""Prepared private phone endpoint controller. No socket, TLS, UI or automatic start."""
import threading
from .phone_session import PhoneSession
from .phone_audio import PhoneAudio
class PhoneController:
 def __init__(self,processor=None,conversation_busy=lambda:False):
  self.session=PhoneSession();self.processor=processor or PhoneAudio();self.conversation_busy=conversation_busy;self.lock=threading.RLock();self.worker=None;self.reply=None;self.error='';self.expiry=None
 def enable(self,consent=False):
  with self.lock:
   if self.worker and self.worker.is_alive():raise ValueError('Previous phone worker still stopping')
   if consent is not True:raise ValueError('Review private session first')
   reset=getattr(self.processor,'reset_session',None)
   if reset:reset()
   self.reply=None;self.error='';return self.session.enable(consent)
 def request_pair(self,code,label):return self.session.request_pair(code,label)
 def approve(self,reviewed,confirm=False):
  with self.lock:
   token=self.session.approve(reviewed,confirm);token_hash=self.session.digest(token)
   if self.expiry:self.expiry.cancel()
   def expire():
    with self.lock:
     if self.session.token_hash==token_hash:self.stop()
   self.expiry=threading.Timer(900,expire);self.expiry.daemon=True;self.expiry.start();return token
 def submit(self,token,raw):
  with self.lock:
   self.session.authorize(token)
   if self.conversation_busy():raise ValueError('Desktop conversation is active; phone turn not started')
   if self.worker and self.worker.is_alive():raise ValueError('Current phone turn still running or stopping')
   self.session.decode(raw);self.reply=None;self.error='';ticket=self.session.generation
   def run():
    try:
     result=self.session.turn(token,raw,self.processor)
     with self.lock:
      if ticket==self.session.generation:self.reply=result
    except Exception:
     with self.lock:
      # Never include tokens, transcripts, WAV bytes or callback errors in status.
      if ticket==self.session.generation:self.error='Local phone turn failed; no action performed'
   self.worker=threading.Thread(target=run,daemon=True);self.worker.start();return self.worker
 def take_reply(self,token):
  with self.lock:
   self.session.authorize(token);result=self.reply;self.reply=None;return result
 def stop(self):
  with self.lock:
   if self.expiry:self.expiry.cancel();self.expiry=None
   self.session.stop();self.reply=None;self.error=''
   reset=getattr(self.processor,'reset_session',None)
   if reset:reset()
 def snapshot(self):
  with self.lock:return {**self.session.snapshot(),'busy':bool(self.worker and self.worker.is_alive()),'reply_ready':self.reply is not None,'error':self.error,'transport':'Not configured; no network listener'}
 def close(self):
  self.stop()
  with self.lock:worker=self.worker
  if worker and worker is not threading.current_thread():worker.join(timeout=2)
  if worker and worker.is_alive():return False
  self.processor.close();return True
