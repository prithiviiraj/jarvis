"""Reviewed quoted-page playback only. No mic, model, download or tool execution."""
import threading
from .news_page import validate
class NewsSpeech:
 def __init__(self,factory):self.factory=factory;self.speaker=None;self.generation=0;self.busy=False;self.status='Off';self.lock=threading.RLock();self.worker=None
 def stop(self):
  with self.lock:self.generation+=1;speaker=self.speaker;self.status='Stopped'
  if speaker:speaker.stop()
 def play(self,row,reviewed,current_url,confirm=False,conversation_busy=False):
  text=validate(row)
  if confirm is not True or reviewed!=row or current_url()!=row['url']:raise ValueError('Review exact current page text before speech')
  with self.lock:
   if self.busy or conversation_busy:raise ValueError('Wait for current speech or conversation to stop')
   self.busy=True;ticket=self.generation;self.status='Preparing reviewed local speech'
  def valid():return ticket==self.generation and current_url()==row['url']
  def work():
   candidate=None
   try:
    candidate=self.speaker or self.factory()
    with self.lock:
     if not valid():
      candidate.stop()
      if candidate is not self.speaker and hasattr(candidate,'close'):candidate.close()
      return
     self.speaker=candidate;voice_ticket=candidate.generation;self.status='Reading quoted page text locally'
    # External text goes only to a local speech engine, never an LLM/tool dispatcher.
    if valid():candidate.speak(text,generation=voice_ticket)
    with self.lock:
     if ticket==self.generation:self.status='Reading finished' if valid() else 'Page changed; reading stopped'
   except Exception:
    with self.lock:self.status='Local reading unavailable; no download or cloud fallback'
   finally:
    with self.lock:self.busy=False
  thread=threading.Thread(target=work,daemon=True);self.worker=thread;thread.start();return thread
 def close(self):
  self.stop()
  worker=self.worker
  if worker and worker is not threading.current_thread():worker.join(timeout=2)
  with self.lock:
   if worker and worker.is_alive():self.status='Stopped; local synthesis still finishing';return False
   speaker=self.speaker;self.speaker=None
  if speaker and hasattr(speaker,'close'):speaker.close()
  return True
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'status':self.status}
