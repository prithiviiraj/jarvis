"""One-use installed authorization exchange with verified Google account identity.
No browser or listener starts here. Private exchange fields never enter snapshots.
"""
import json,ssl,urllib.request
from .google_oauth import GoogleOAuth,SCOPES
from .google_tokens import GoogleTokens
from .connector_workflows import address
from .google_read_connector import NoRedirect
IDENTITY={'openid','https://www.googleapis.com/auth/userinfo.email'}
class GoogleAuthorization:
 def __init__(self,tokens=None,identity_transport=None):self.oauth=GoogleOAuth();self.tokens=tokens or GoogleTokens();self.identity_transport=identity_transport;self.expected=None;self.grants=[];self.save_guard=None
 def begin(self,client_id,port,grants,email,consent=False):
  email=address(email);result=self.oauth.begin(client_id,port,grants,consent)
  import urllib.parse
  u=urllib.parse.urlsplit(result['authorization_url']);q=urllib.parse.parse_qs(u.query);q['scope']=[q['scope'][0]+' '+' '.join(sorted(IDENTITY))];result['authorization_url']=urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,urllib.parse.urlencode({k:v[0]for k,v in q.items()}),''));result['identity_scopes']=sorted(IDENTITY);result['account']=email
  self.expected=email;self.grants=list(grants);return result
 def identity(self,token):
  if self.identity_transport:return self.identity_transport(token)
  import certifi
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  req=urllib.request.Request('https://openidconnect.googleapis.com/v1/userinfo',headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
  try:
   with opener.open(req,timeout=15)as r:raw=r.read(16385)
   if len(raw)>16384:raise ValueError()
   return json.loads(raw)
  except Exception:raise ValueError('Google account identity could not be verified; nothing saved')from None
 def complete(self,callback_url,client_secret=None,save_guard=None):
  expected=self.expected;grants=list(self.grants);guard=save_guard or self.save_guard
  payload=self.oauth.accept(callback_url);self.expected=None;self.grants=[]
  if client_secret is not None:
   if not isinstance(client_secret,str)or not client_secret or len(client_secret)>500:raise ValueError('Invalid desktop client credential')
   payload['client_secret']=client_secret
  try:
   row=self.tokens.request(payload)
   if not isinstance(row,dict)or row.get('token_type','').lower()!='bearer'or not isinstance(row.get('access_token'),str)or not row['access_token']or any(c.isspace()for c in row['access_token']):raise ValueError()
   scopes=row.get('scope')
   if not isinstance(scopes,str):raise ValueError()
   granted=set(scopes.split());requested={SCOPES[g]for g in grants}
   if not requested.issubset(granted)or not granted.issubset(requested|IDENTITY):raise ValueError()
   who=self.identity(row['access_token'])
   if not isinstance(who,dict)or who.get('email_verified')is not True or not isinstance(who.get('email'),str)or address(who['email']).casefold()!=expected.casefold()or not isinstance(who.get('sub'),str)or not who['sub']:raise ValueError()
   save=lambda:self.tokens.save(expected,payload['client_id'],row.get('refresh_token'),sorted(requested),confirm=True,client_secret=client_secret)
   if guard:guard(save)
   else:save()
  except Exception:raise ValueError('Google authorization incomplete or account/scopes mismatched; nothing connected. Review authorization again.')from None
  return {'account':expected,'connected':True,'grants':grants,'scope':'Verified Google identity and saved local refresh credential. No mail/calendar action performed.'}
 def cancel(self):self.oauth.cancel();self.expected=None;self.grants=[]
 def snapshot(self):return {**self.oauth.snapshot(),'account':self.expected,'identity_scopes':sorted(IDENTITY)}
