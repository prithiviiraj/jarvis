"""Google refresh tokens in isolated Windows credentials. No plaintext or cross-app token reuse."""
import hashlib,json,re,threading,time,urllib.parse,urllib.request,ssl
from .security import WindowsCredentials,CredentialError
from .google_read_connector import NoRedirect
class GoogleCredentials(WindowsCredentials):
 @staticmethod
 def target(account):
  if not isinstance(account,str)or not re.fullmatch(r'[a-f0-9]{64}',account):raise CredentialError('Invalid Google account key')
  return 'JARVIS/google/'+account
class GoogleTokens:
 def __init__(self,store=None,transport=None,clock=time.monotonic):self.store=store;self.transport=transport;self.clock=clock;self.cache={};self.lock=threading.RLock()
 def secure(self):
  if self.store is None:self.store=GoogleCredentials()
  return self.store
 @staticmethod
 def key(email):
  from .connector_workflows import address
  return hashlib.sha256(address(email).casefold().encode()).hexdigest()
 def save(self,email,client_id,refresh_token,scopes,confirm=False,client_secret=None):
  if confirm is not True:raise ValueError('Verify account identity and reviewed Google grant before saving')
  if not isinstance(client_id,str)or not client_id.endswith('.apps.googleusercontent.com')or not isinstance(refresh_token,str)or not refresh_token or len(refresh_token)>700:raise ValueError('Invalid installed Google token')
  from .google_oauth import SCOPES
  if not isinstance(scopes,list)or not scopes or any(s not in SCOPES.values()for s in scopes):raise ValueError('Unreviewed Google scopes')
  if client_secret is not None and (not isinstance(client_secret,str)or not client_secret or len(client_secret)>500):raise ValueError('Invalid desktop client credential')
  value=json.dumps({'client_id':client_id,'refresh_token':refresh_token,'scopes':scopes,'client_secret':client_secret},separators=(',',':'))
  self.secure().set(self.key(email),value);self.cache.pop(self.key(email),None)
 def request(self,payload):
  if self.transport:
   try:return self.transport(payload)
   except Exception:raise ValueError('Google token request failed; no retry or secret details logged')from None
  import certifi
  http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  req=urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode(payload).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'},method='POST')
  try:
   with http.open(req,timeout=15)as r:
    raw=r.read(16385)
    if len(raw)>16384:raise ValueError()
   return json.loads(raw)
  except Exception:raise ValueError('Google token refresh failed; reconnect the account. No retry or token details logged.')from None
 def access(self,email,required_scope):
  with self.lock:
   key=self.key(email);raw=self.secure().get(key)
   if not raw:raise ValueError('Google account is not connected')
   try:row=json.loads(raw)
   except ValueError:raise ValueError('Google saved credential invalid')from None
   if required_scope not in row.get('scopes',[]):raise ValueError('Google scope was not granted')
   cached=self.cache.get(key)
   if cached and self.clock()<cached['until']:
    if required_scope not in cached['scopes']:raise ValueError('Google token scope changed; review authorization again')
    return cached['token']
   payload={'client_id':row['client_id'],'refresh_token':row['refresh_token'],'grant_type':'refresh_token'}
   if row.get('client_secret'):payload['client_secret']=row['client_secret']
   result=self.request(payload)
   if not isinstance(result,dict)or result.get('token_type','').lower()!='bearer'or not isinstance(result.get('access_token'),str)or not result['access_token']or any(c.isspace()for c in result['access_token'])or type(result.get('expires_in'))is not int or not 60<=result['expires_in']<=86400:raise ValueError('Google token response invalid')
   returned=result.get('scope')
   if returned is not None and (not isinstance(returned,str)or required_scope not in returned.split()or not set(returned.split()).issubset(set(row['scopes'])|{'openid','https://www.googleapis.com/auth/userinfo.email'})):raise ValueError('Google token scope changed; review authorization again')
   self.cache[key]={'token':result['access_token'],'until':self.clock()+result['expires_in']-30,'scopes':returned.split()if returned is not None else row['scopes']};return result['access_token']
 def disconnect(self,email):
  with self.lock:
   key=self.key(email);self.cache.pop(key,None);self.secure().delete(key)
 def status(self,email):return {'account':email,'credential_present':self.secure().status(self.key(email)).get('present',False),'scope':'Local credential presence only, not live account authorization'}
