"""Frozen Windows credential/callback software acceptance. Google replies are fixtures."""
import hashlib,json,threading,urllib.parse,urllib.request
from .google_tokens import GoogleTokens,GoogleCredentials
from .google_authorization import GoogleAuthorization,IDENTITY
from .google_connection import GoogleConnection
from .google_oauth import SCOPES

def run():
 from pathlib import Path
 import uuid
 email='fixture-'+uuid.uuid4().hex+'@example.invalid';client='fixture.apps.googleusercontent.com';secret='fixture-secret';scope=SCOPES['calendar-freebusy'];store=GoogleCredentials();key=GoogleTokens.key(email);probe=hashlib.sha256(uuid.uuid4().bytes).hexdigest()
 try:
  store.set(probe,'fixture-credential');assert store.status(probe)['present'];assert store.get(probe)=='fixture-credential';store.delete(probe);assert not store.status(probe)['present']
  calls=[]
  def transport(payload):
   calls.append(payload.copy())
   if payload['grant_type']=='authorization_code':return {'access_token':'fixture-access','refresh_token':'fixture-refresh','token_type':'Bearer','scope':' '.join({scope}|IDENTITY)}
   assert payload['client_secret']==secret
   return {'access_token':'fixture-refreshed','token_type':'Bearer','expires_in':3600,'scope':scope}
  tokens=GoogleTokens(store,transport);auth=GoogleAuthorization(tokens,lambda t:{'email':email,'email_verified':True,'sub':'fixture-subject'});urls=[];connection=GoogleConnection(tokens,auth,lambda u:urls.append(u)or True)
  # Never overwrite the product client's target in a fixture. Supply a disposable
  # test store mapping for that fixed key, while account tokens use real WinCred.
  from .google_connection import CLIENT_KEY
  class Scoped:
   def get(self,k):return json.dumps({'client_id':client,'client_secret':secret})if k==CLIENT_KEY else store.get(k)
   def set(self,k,v):
    assert k!=CLIENT_KEY;store.set(k,v)
   def status(self,k):return store.status(k)
   def delete(self,k):assert k!=CLIENT_KEY;store.delete(k)
  tokens.store=Scoped()
  connection.begin(email,['calendar-freebusy'],True)
  import time
  deadline=time.monotonic()+2
  while not urls and time.monotonic()<deadline:time.sleep(.01)
  q=urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query);callback=q['redirect_uri'][0]+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'})
  assert urllib.parse.urlsplit(callback).hostname=='127.0.0.1'
  with urllib.request.urlopen(callback,timeout=3)as reply:assert reply.status==200 and reply.headers['Cache-Control']=='no-store'
  connection.worker.join(5);assert not connection.busy and not connection.error,connection.snapshot();assert store.status(key)['present'];assert tokens.access(email,scope)=='fixture-refreshed';assert len(calls)==2
  assert 'fixture-secret'not in json.dumps(connection.snapshot())
  # Real frozen review/journal/encoding/readback with entirely controlled Gmail
  # transport. No network mail side effect and no owner's account credential.
  import tempfile,email as mailparser
  from .google_mail import GoogleMail
  tokens.save(email,client,'fixture-refresh',[SCOPES['mail-read'],SCOPES['mail-send']],True,secret)
  tokens.transport=lambda p:{'access_token':'fixture-mail','token_type':'Bearer','expires_in':3600,'scope':SCOPES['mail-read']+' '+SCOPES['mail-send']}
  fixture_sent={};fixture_posts=[]
  def mail_transport(method,url,payload):
   if url.endswith('/profile'):return {'emailAddress':email}
   if 'messages?'in url:return {'messages':[]}
   if method=='POST':
    fixture_posts.append(payload)
    msg=mailparser.message_from_bytes(__import__('base64').urlsafe_b64decode(payload['raw']+'='*(-len(payload['raw'])%4)),policy=mailparser.policy.default)
    fixture_sent.update({'id':'fixture-sent','labelIds':['SENT'],'payload':{'mimeType':'text/plain','headers':[{'name':k,'value':str(msg[k])}for k in ('To','Subject','Message-ID')],'body':{'data':__import__('base64').urlsafe_b64encode(msg.get_content().encode()).decode()}}});return {'id':'fixture-sent'}
   return fixture_sent
  with tempfile.TemporaryDirectory()as folder:
   ledger=Path(folder)/'mail.json';mail=GoogleMail(connection,ledger,mail_transport);review=mail.prepare(['friend@example.invalid'],'Fixture review','Exact fixture words');mail.submit(review,True);mail.worker.join(5);assert mail.snapshot()['state']=='completed',mail.snapshot();assert len(fixture_posts)==1;assert GoogleMail(connection,ledger,mail_transport).snapshot()['state']=='completed'
  connection.disconnect(True);assert not store.status(key)['present'];connection.stop()
  result={'host':'actual frozen Windows core','windows_credential_write_read_delete':True,'real_ipv4_loopback_callback':True,'PKCE_state_and_verified_identity_fixture':True,'exchange_refresh_local_disconnect_fixture':True,'live_google':False,'real_registered_client':False,'reviewed_Gmail_send_readback_and_restart_fixture':True,'mail_sent':False,'calendar_changed':False}
  Path('ui-evidence').mkdir(exist_ok=True);Path('ui-evidence/frozen-google-acceptance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 finally:store.delete(key);store.delete(probe)
