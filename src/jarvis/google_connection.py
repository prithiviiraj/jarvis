"""Explicit Google connection lifecycle. No automatic mail/calendar effects."""
import hashlib,json,threading,webbrowser
from .google_tokens import GoogleTokens
from .google_authorization import GoogleAuthorization
from .google_loopback import GoogleLoopback
CLIENT_KEY=hashlib.sha256(b'JARVIS registered desktop OAuth client').hexdigest()
class GoogleConnection:
 def __init__(self,tokens=None,authorization=None,opener=None):
  self.tokens=tokens or GoogleTokens();self.auth=authorization or GoogleAuthorization(self.tokens);self.loop=GoogleLoopback(self.auth);self.opener=opener or webbrowser.open;self.lock=threading.RLock();self.generation=0;self.busy=False;self.status='Google not connected';self.account=None;self.grants=[];self.error='';self.worker=None
 def configure(self,client_id,client_secret,consent=False):
  if consent is not True:raise ValueError('Review registered Google desktop credentials first')
  if not isinstance(client_id,str)or not client_id.endswith('.apps.googleusercontent.com')or len(client_id)>250 or any(c.isspace()for c in client_id):raise ValueError('Registered Google desktop client required')
  if client_secret is not None and(not isinstance(client_secret,str)or not client_secret or len(client_secret)>500):raise ValueError('Invalid desktop client credential')
  self.idle_worker();self.stop();self.tokens.secure().set(CLIENT_KEY,json.dumps({'client_id':client_id,'client_secret':client_secret},separators=(',',':')));self.status='Registered client saved in Windows credentials. Connect your Google account next.'
 def begin(self,email,grants,consent=False):
  if consent is not True:raise ValueError('Review Google account and exact scopes before opening Google')
  self.idle_worker();self.stop();raw=self.tokens.secure().get(CLIENT_KEY)
  if not raw:raise ValueError('Register a Google desktop OAuth client first')
  try:client=json.loads(raw)
  except Exception:raise ValueError('Saved desktop credential invalid')from None
  result=self.loop.begin(client['client_id'],grants,email,True)
  with self.lock:self.generation+=1;ticket=self.generation;self.account=email;self.grants=list(grants);self.busy=True;self.error='';self.status='Waiting for Google browser consent'
  try:
   if self.opener(result['authorization_url'])is False:raise ValueError()
  except Exception:self.stop();raise ValueError('Default browser could not open Google consent; nothing connected')from None
  def work():
   import time
   try:
    while self.generation==ticket and self.loop.snapshot()['pending'] and not self.loop.snapshot()['callback_received']:time.sleep(.1)
    if self.generation!=ticket:return
    if not self.loop.snapshot()['callback_received']:raise ValueError('Google authorization expired; nothing connected')
    # The guard serializes just the final secure write against Stop, not HTTP.
    def save_guard(save):
     with self.lock:
      if self.generation!=ticket:raise ValueError('Google authorization cancelled')
      save()
    self.loop.complete(client.get('client_secret'),save_guard)
    with self.lock:
     if self.generation==ticket:self.status='Google connected. Read-only queries require an explicit request; sends and calendar changes need exact review.'
   except Exception:
    with self.lock:
     if self.generation==ticket:self.error='Google authorization failed, expired or account/scopes changed. Nothing was sent or booked.';self.status='Google connection incomplete'
   finally:
    with self.lock:
     if self.generation==ticket:self.busy=False
  self.worker=threading.Thread(target=work,name='google-connect',daemon=True);self.worker.start()
 def idle_worker(self):
  if self.worker and self.worker.is_alive():raise ValueError('Previous authorization is still stopping; wait before reconnecting')
 def stop(self):
  with self.lock:self.generation+=1;self.busy=False
  self.loop.stop();self.auth.save_guard=None
 def disconnect(self,confirm=False):
  if confirm is not True:raise ValueError('Review disconnect for this account')
  self.stop()
  if self.account:self.tokens.disconnect(self.account)
  self.status='Local Google credentials removed. Remove JARVIS access in your Google account to revoke server permission too.';self.error='';self.grants=[]
 def snapshot(self):
  return {'busy':self.busy,'status':self.status,'account':self.account,'grants':list(self.grants),'error':self.error,'scope':'No automatic mail/calendar action. Disconnect removes local token only.'}
