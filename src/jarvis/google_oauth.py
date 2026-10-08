"""Installed Google PKCE preparation. No listener/browser/network/token persistence.
App client registration and owner scope consent must exist before wiring effects.
"""
import base64,hashlib,hmac,secrets,time,urllib.parse
SCOPES={'sheets-write':'https://www.googleapis.com/auth/spreadsheets','drive-metadata-read':'https://www.googleapis.com/auth/drive.metadata.readonly','sheets-read':'https://www.googleapis.com/auth/spreadsheets.readonly','mail-read':'https://www.googleapis.com/auth/gmail.readonly','mail-send':'https://www.googleapis.com/auth/gmail.send','calendar-read':'https://www.googleapis.com/auth/calendar.events.readonly','calendar-write-owned':'https://www.googleapis.com/auth/calendar.events.owned','calendar-freebusy':'https://www.googleapis.com/auth/calendar.freebusy'}
class GoogleOAuth:
 def __init__(self,clock=time.monotonic):self.clock=clock;self.pending=None;self.verifier=None;self.state=None;self.deadline=0
 def begin(self,client_id,port,grants,consent=False):
  if consent is not True:raise ValueError('Review Google account scopes first')
  if not isinstance(client_id,str)or not client_id.endswith('.apps.googleusercontent.com')or any(c.isspace()for c in client_id)or len(client_id)>250:raise ValueError('Registered Google desktop client required')
  if type(port)is not int or not 1024<=port<=65535:raise ValueError('Use an allocated loopback callback port')
  if not isinstance(grants,list)or not grants or len(set(grants))!=len(grants)or any(g not in SCOPES for g in grants):raise ValueError('Choose explicit supported Google scopes')
  self.cancel();self.verifier=secrets.token_urlsafe(48);self.state=secrets.token_urlsafe(32);self.deadline=self.clock()+300;redirect=f'http://127.0.0.1:{port}/callback';scope=' '.join(SCOPES[g]for g in grants)
  challenge=base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode('ascii')).digest()).rstrip(b'=').decode()
  self.pending={'client_id':client_id,'redirect_uri':redirect,'grants':list(grants),'scope':scope}
  params={'client_id':client_id,'redirect_uri':redirect,'response_type':'code','scope':scope,'state':self.state,'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline','prompt':'consent'}
  return {'authorization_url':'https://accounts.google.com/o/oauth2/v2/auth?'+urllib.parse.urlencode(params),'redirect_uri':redirect,'grants':list(grants),'expires_in_seconds':300,'scope':'Prepared OAuth link only. No browser/listener starts, no account connected.'}
 def accept(self,callback_url):
  if not self.pending or self.clock()>=self.deadline:raise ValueError('Google authorization expired or cancelled')
  u=urllib.parse.urlsplit(callback_url);expected=urllib.parse.urlsplit(self.pending['redirect_uri'])
  if u.scheme!=expected.scheme or u.netloc!=expected.netloc or u.path!=expected.path or u.fragment:raise ValueError('Wrong OAuth callback destination')
  q=urllib.parse.parse_qs(u.query,keep_blank_values=True)
  if any(len(v)!=1 for v in q.values())or set(q)-{'state','code','scope','authuser','prompt','error','error_description'}:raise ValueError('Invalid OAuth callback fields')
  state=q.get('state',[''])[0]
  if not hmac.compare_digest(state,self.state):raise ValueError('OAuth state mismatch')
  if 'error'in q:self.cancel();raise ValueError('Google authorization denied; nothing connected')
  code=q.get('code',[''])[0]
  if not isinstance(code,str)or not 1<=len(code)<=2048 or any(ord(c)<32 for c in code):raise ValueError('Missing authorization code')
  # These fields are private token-exchange data, never UI status/history/logs.
  result={'client_id':self.pending['client_id'],'redirect_uri':self.pending['redirect_uri'],'code':code,'code_verifier':self.verifier,'grant_type':'authorization_code'};self.cancel();return result
 def cancel(self):self.pending=None;self.verifier=None;self.state=None;self.deadline=0
 def snapshot(self):return {'pending':self.pending is not None and self.clock()<self.deadline,'grants':self.pending['grants']if self.pending else[],'scope':'Prepared installed OAuth. No token store or connected account.'}
