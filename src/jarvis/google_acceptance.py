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
  connection.begin(email,['calendar-freebusy'],True);q=urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query);callback=q['redirect_uri'][0]+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'})
  assert urllib.parse.urlsplit(callback).hostname=='127.0.0.1'
  with urllib.request.urlopen(callback,timeout=3)as reply:assert reply.status==200 and reply.headers['Cache-Control']=='no-store'
  connection.worker.join(5);assert not connection.busy and not connection.error,connection.snapshot();assert store.status(key)['present'];assert tokens.access(email,scope)=='fixture-refreshed';assert len(calls)==2
  assert 'fixture-secret'not in json.dumps(connection.snapshot());connection.disconnect(True);assert not store.status(key)['present'];connection.stop()
  result={'host':'actual frozen Windows core','windows_credential_write_read_delete':True,'real_ipv4_loopback_callback':True,'PKCE_state_and_verified_identity_fixture':True,'exchange_refresh_local_disconnect_fixture':True,'live_google':False,'real_registered_client':False,'mail_sent':False,'calendar_changed':False}
  Path('ui-evidence').mkdir(exist_ok=True);Path('ui-evidence/frozen-google-acceptance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 finally:store.delete(key);store.delete(probe)
