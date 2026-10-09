"""Local visual review. Generated replies and quoted notes never execute actions."""
import hashlib,re,threading
class NeuralPanel:
 def __init__(self,factory):
  self.factory=factory;self.row=None;self.picture=None;self.seq=0;self.worker=None;self.speaker=None;self.generation=0;self.busy=False;self.status='No visual answer yet';self.lock=threading.RLock()
 def offer(self,kind,actor,title,text,source='Generated reply, not a verified plan'):
  if not isinstance(text,str)or not text.strip():raise ValueError('No visual text')
  self.stop();self.picture=None;self.seq+=1;text=text[:4000]
  with self.lock:self.row={'id':self.seq,'kind':kind,'actor':actor,'title':title[:120],'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'source':source,'question':'Master, read pannava?','scope':'Visual review only. No app opening, saving, sending or tools.'};self.status='Waiting for Master: Read aloud or Not now'
  return self.row
 def generated(self,row,topic):
  if not isinstance(row,dict)or not isinstance(row.get('text'),str)or row.get('name')=='You':return
  plan=bool(re.search(r'\b(?:plan|planning|schedule|steps|roadmap|strategy)\b',str(topic),re.I))
  self.offer('plan'if plan else'answer',row.get('name','JARVIS'),'Your plan'if plan else'Agent answer',row['text'])
 def stop(self):
  with self.lock:self.generation+=1;speaker=self.speaker;self.status='Reading stopped'
  if speaker:speaker.stop()
 def clear(self):self.stop();self.row=None;self.picture=None;self.status='No visual answer yet'
 def speak(self,reviewed,confirm=False,conversation_busy=False,prompt_only=False):
  with self.lock:
   row=self.row
   if not row or confirm is not True or reviewed!=row:raise ValueError('Review the current visual popup before reading')
   if conversation_busy or self.busy:raise ValueError('Stop the current voice/conversation before popup reading')
   ticket=self.generation;self.busy=True;self.status='Preparing local speech';text='Master, shall I read this aloud?'if prompt_only else row['text']
  def work():
   candidate=None
   try:
    candidate=self.speaker or self.factory()
    with self.lock:
     if ticket!=self.generation:
      candidate.stop()
      if candidate is not self.speaker and hasattr(candidate,'close'):candidate.close()
      return
     self.speaker=candidate;voice_ticket=candidate.generation;self.status='Asking Master locally'if prompt_only else'Reading visual text locally'
    if callable(getattr(type(candidate),'prepare_stream',None))and callable(getattr(type(candidate),'play_prepared',None)):
     for prepared in candidate.prepare_stream(text,generation=voice_ticket):
      if ticket!=self.generation:break
      candidate.play_prepared(prepared,generation=voice_ticket)
    elif ticket==self.generation:candidate.speak(text,generation=voice_ticket)
    with self.lock:
     if ticket==self.generation:self.status='Waiting for Master: Read aloud or Not now'if prompt_only else'Reading finished'
   except Exception:
    with self.lock:
     if ticket==self.generation:self.status='Local speech unavailable. No cloud fallback or download.'
   finally:
    with self.lock:self.busy=False
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start();return self.worker
 def snapshot(self):
  with self.lock:return {'row':dict(self.row)if self.row else None,'picture':self.picture,'busy':self.busy,'status':self.status}
 def close(self):
  self.stop()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(timeout=2)
  if self.worker and self.worker.is_alive():return False
  if self.speaker and hasattr(self.speaker,'close'):self.speaker.close()
  self.speaker=None;return True
