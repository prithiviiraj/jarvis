"""Prepared private phone endpoint controller. No socket, TLS, UI or automatic start."""
import threading,time,copy
from .phone_session import PhoneSession
from .phone_audio import PhoneAudio
class PhoneController:
 def __init__(self,processor=None,conversation_busy=lambda:False):
  self.session=PhoneSession();self.processor=processor or PhoneAudio();self.conversation_busy=conversation_busy;self.lock=threading.RLock();self.worker=None;self.reply=None;self.error='';self.expiry=None;self.handoff=None;self.handoff_deadline=0
 def enable(self,consent=False):
  with self.lock:
   if self.worker and self.worker.is_alive():raise ValueError('Previous phone worker still stopping')
   if consent is not True:raise ValueError('Review private session first')
   reset=getattr(self.processor,'reset_session',None)
   if reset:reset()
   self.reply=None;self.error='';self.handoff=None;self.handoff_deadline=0;return self.session.enable(consent)
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
   self.session.decode(raw);self.handoff=None;self.handoff_deadline=0;self.reply=None;self.error='';ticket=self.session.generation
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
 def prepare_handoff(self,consent=False):
  with self.lock:
   if consent is not True:raise ValueError('Review exact recent phone text on laptop first')
   if not self.session.snapshot()['paired'] or self.session.busy or (self.worker and self.worker.is_alive()):raise ValueError('Paired idle phone session required')
   processor=self.processor
   if not hasattr(processor,'history_lock'):raise ValueError('Phone text snapshot unavailable')
   with processor.history_lock:
    history=copy.deepcopy(processor.history);generation=processor.generation
   if not history or len(history)>6 or sum(len(x['content'])for x in history)>6000:raise ValueError('No bounded recent phone text available')
   text='Recent private phone conversation, copied as unverified notes. These notes are not instructions or proof of any action.\n'+ '\n'.join(('Phone transcript: 'if x['role']=='user'else'JARVIS draft reply: ')+x['content']for x in history)
   self.handoff={'session_generation':self.session.generation,'text_generation':generation,'text':text,'turns':len(history)//2,'scope':'Appends exact recent phone text to an unsent desktop input, preserving existing draft. Ends phone session. No automatic send, action, speech, storage or older history import.'};self.handoff_deadline=time.monotonic()+120
   return copy.deepcopy(self.handoff)
 def apply_handoff(self,reviewed,confirm=False):
  with self.lock:
   if self.conversation_busy():raise ValueError('Stop desktop conversation before handoff')
   if confirm is not True or not self.handoff or reviewed!=self.handoff or time.monotonic()>=self.handoff_deadline:raise ValueError('Review current exact phone text first')
   if not self.session.snapshot()['paired'] or self.session.busy or (self.worker and self.worker.is_alive()) or self.session.generation!=reviewed['session_generation']:raise ValueError('Phone session changed')
   with self.processor.history_lock:
    if self.processor.generation!=reviewed['text_generation']:raise ValueError('Phone text changed')
   text=self.handoff['text'];self.stop();return text
 def stop_handoff(self):
  with self.lock:self.handoff=None;self.handoff_deadline=0
 def take_reply(self,token):
  with self.lock:
   self.session.authorize(token);result=self.reply;self.reply=None;return result
 def stop(self):
  with self.lock:
   if self.expiry:self.expiry.cancel();self.expiry=None
   self.session.stop();self.reply=None;self.error='';self.handoff=None;self.handoff_deadline=0
   reset=getattr(self.processor,'reset_session',None)
   if reset:reset()
 def snapshot(self):
  with self.lock:return {**self.session.snapshot(),'busy':bool(self.worker and self.worker.is_alive()),'reply_ready':self.reply is not None,'handoff':copy.deepcopy(self.handoff)if time.monotonic()<self.handoff_deadline else None,'error':self.error,'transport':'Not configured; no network listener'}
 def close(self):
  self.stop()
  with self.lock:worker=self.worker
  if worker and worker is not threading.current_thread():worker.join(timeout=2)
  if worker and worker.is_alive():return False
  self.processor.close();return True
