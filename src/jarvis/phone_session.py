"""Private phone-call session boundary. No network listener or remote bridge commands.

Pairing requests require local approval. Audio is bounded PCM WAV in memory.
Callbacks must be local-only speech/chat implementations, never action handlers.
"""
import hashlib,hmac,io,secrets,threading,time,wave

class PhoneSession:
 def __init__(self,clock=time.monotonic):
  self.clock=clock;self.lock=threading.RLock();self.cancel=threading.Event();self.enabled=False;self.pending=None;self.token_hash=None;self.deadline=0;self.pair_hash=None;self.pair_deadline=0;self.generation=0;self.busy=False;self.status='Phone calling off; no listener'
 def enable(self,consent=False):
  if consent is not True:raise ValueError('Allow private phone calling locally first')
  with self.lock:
   if self.busy:raise ValueError('Previous phone turn still stopping')
   self.stop();self.enabled=True;code=secrets.token_urlsafe(24);self.pair_hash=self.digest(code);self.pair_deadline=self.clock()+120;self.status='Pairing open for120seconds; local approval required';return code
 @staticmethod
 def digest(value):
  if not isinstance(value,str)or not 20<=len(value)<=200:raise ValueError('Invalid session credential')
  return hashlib.sha256(value.encode()).digest()
 def request_pair(self,code,label):
  with self.lock:
   if not self.enabled or not self.pair_hash or self.clock()>=self.pair_deadline or not hmac.compare_digest(self.digest(code),self.pair_hash):raise ValueError('Pairing closed or invalid')
   if self.pending:raise ValueError('A phone request already awaits local approval')
   if not isinstance(label,str)or not 1<=len(label)<=60 or any(ord(c)<32 for c in label):raise ValueError('Invalid phone label')
   # Device label is unverified display text, not owner identity.
   self.pending={'request_id':secrets.token_urlsafe(24),'label':label};self.status='Unverified phone request; approve on laptop';return dict(self.pending)
 def approve(self,reviewed,confirm=False):
  with self.lock:
   if confirm is not True or not self.pending or reviewed!=self.pending or self.clock()>=self.pair_deadline:raise ValueError('Review the current phone request on laptop')
   token=secrets.token_urlsafe(32);self.token_hash=self.digest(token);self.deadline=self.clock()+900;self.pending=None;self.pair_hash=None;self.pair_deadline=0;self.status='Private phone session paired for15minutes';return token
 def authorize(self,token):
  if not self.enabled or not self.token_hash or self.clock()>=self.deadline or not hmac.compare_digest(self.digest(token),self.token_hash):raise ValueError('Phone session expired or revoked')
 def snapshot(self):
  with self.lock:return {'enabled':self.enabled,'paired':bool(self.token_hash and self.clock()<self.deadline),'pending':dict(self.pending)if self.pending else None,'busy':self.busy,'status':self.status,'scope':'Private internet voice only; no PSTN, action commands or network listener in this module'}
 def stop(self):
  with self.lock:
   self.generation+=1;self.cancel.set();self.enabled=False;self.pending=None;self.token_hash=None;self.pair_hash=None;self.deadline=0;self.pair_deadline=0;self.status='Phone calling stopped; session revoked'
 @staticmethod
 def decode(raw):
  if not isinstance(raw,bytes)or not 44<=len(raw)<=960044:raise ValueError('Phone audio must be bounded PCM WAV')
  try:
   with wave.open(io.BytesIO(raw),'rb')as w:
    if w.getnchannels()!=1 or w.getsampwidth()!=2 or w.getframerate()!=16000 or w.getcomptype()!='NONE' or not 1600<=w.getnframes()<=480000:raise ValueError('Use mono16kHz PCM16 audio from0.1to30seconds')
    frames=w.readframes(w.getnframes())
    if len(frames)!=w.getnframes()*2:raise ValueError('Incomplete phone audio')
  except (wave.Error,EOFError):raise ValueError('Invalid phone WAV')from None
  return frames
 @staticmethod
 def validate_reply_audio(raw):
  try:
   with wave.open(io.BytesIO(raw),'rb')as w:
    if w.getnchannels()!=1 or w.getsampwidth()!=2 or w.getframerate()not in (16000,24000) or w.getcomptype()!='NONE' or not 1<=w.getnframes()<=w.getframerate()*40:raise ValueError('Invalid phone reply WAV')
    if len(w.readframes(w.getnframes()))!=w.getnframes()*2:raise ValueError('Incomplete phone reply WAV')
  except (wave.Error,EOFError):raise ValueError('Invalid phone reply WAV')from None
 def turn(self,token,raw,process):
  with self.lock:
   self.authorize(token)
   if self.busy:raise ValueError('Phone turn already running')
   pcm=self.decode(raw);generation=self.generation;cancel=threading.Event();self.cancel=cancel;self.busy=True;self.status='Processing private local phone audio'
  try:
   # Pure data interface: no UI bridge or desktop/billing command dispatch.
   result=process(pcm,cancel)
   with self.lock:
    if cancel.is_set()or generation!=self.generation:raise ValueError('Phone turn revoked')
    self.authorize(token)
    if not isinstance(result,dict)or set(result)!={'text','wav'}or not isinstance(result['text'],str)or len(result['text'])>4000 or not isinstance(result['wav'],bytes)or len(result['wav'])>1920100:raise ValueError('Invalid local phone reply')
    self.validate_reply_audio(result['wav'])
    self.status='Local phone reply ready';return result
  finally:
   with self.lock:self.busy=False
