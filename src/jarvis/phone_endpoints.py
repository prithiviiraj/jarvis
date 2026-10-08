"""Prepared phone HTTP routing only. No server/socket. Host must enforce trusted TLS and local scope."""
import base64,json,secrets,threading,time
from .phone_session import PhoneSession
class PhoneEndpoints:
 def __init__(self,controller,clock=time.monotonic):self.controller=controller;self.clock=clock;self.claim=None;self.pending=None;self.delivery=None;self.claim_deadline=0;self.lock=threading.RLock()
 def approve_local(self,reviewed,confirm=False):
  with self.lock:
   if not self.claim or self.clock()>=self.claim_deadline:raise ValueError('Phone request expired')
   self.delivery=self.controller.approve(reviewed,confirm)
 def stop_local(self):
  with self.lock:self.controller.stop();self.claim=None;self.pending=None;self.delivery=None;self.claim_deadline=0
 def handle(self,path,body,token='',trusted_https=False,same_origin=False):
  # Booleans must come from future server-side TLS/Host/Origin checks, never client JSON.
  if trusted_https is not True or same_origin is not True:raise ValueError('Trusted same-origin HTTPS required')
  if path not in ('/phone/pair','/phone/pair-result','/phone/turn','/phone/reply','/phone/stop'):raise ValueError('Unsupported phone endpoint')
  if not isinstance(body,bytes)or len(body)>1280200:raise ValueError('Phone request too large')
  try:data=json.loads(body or b'{}')
  except (ValueError,UnicodeError):raise ValueError('Invalid phone request')from None
  if not isinstance(data,dict):raise ValueError('Phone request must be an object')
  with self.lock:
   if path=='/phone/pair':
    if set(data)!={'code','label'}:raise ValueError('Invalid pairing fields')
    if self.claim and self.clock()<self.claim_deadline:raise ValueError('A phone already awaits local approval')
    self.pending=self.controller.request_pair(data['code'],data['label']);self.claim=secrets.token_urlsafe(32);self.claim_deadline=self.clock()+120;self.delivery=None;return {'claim':self.claim}
   if path=='/phone/pair-result':
    if set(data)!={'claim'}or not self.claim or data['claim']!=self.claim or self.clock()>=self.claim_deadline:raise ValueError('Phone claim expired or invalid')
    if not self.delivery:return {'waiting':True}
    result={'token':self.delivery};self.delivery=None;self.claim=None;self.pending=None;return result
   self.controller.session.authorize(token)
   if path=='/phone/turn':
    if set(data)!={'wav'}or not isinstance(data['wav'],str)or len(data['wav'])>1280060:raise ValueError('Invalid bounded phone audio')
    try:raw=base64.b64decode(data['wav'],validate=True)
    except ValueError:raise ValueError('Invalid phone audio encoding')from None
    self.controller.submit(token,raw);return {'submitted':True}
   if data:raise ValueError('Unexpected phone fields')
   if path=='/phone/reply':
    result=self.controller.take_reply(token)
    if result:return {'text':result['text'],'wav':base64.b64encode(result['wav']).decode()}
    state=self.controller.snapshot()
    if state['error']:raise ValueError('Local phone turn failed')
    return {'waiting':True}
   self.stop_local();return {'stopped':True}
 def snapshot(self):return {'transport':'Not configured; no server or socket','pending':self.pending,'scope':'Only pairing, bounded audio reply and Stop. Local approval never accepted through HTTP.'}
