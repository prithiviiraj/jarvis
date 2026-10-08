"""Explicit read-only GitHub/Notion requests. Separate local secrets, no startup access."""
import base64,hashlib,json,re,ssl,threading,urllib.parse,urllib.request,uuid
from .google_read_connector import NoRedirect
from .security import WindowsCredentials,CredentialError
class ProjectCredentials(WindowsCredentials):
 @staticmethod
 def target(key):
  if not isinstance(key,str)or not re.fullmatch(r'[a-f0-9]{64}',key):raise CredentialError('Invalid project credential key')
  return 'JARVIS/projects/'+key
class ProjectConnectors:
 def __init__(self,store=None,transport=None):self.store=store;self.transport=transport;self.accounts={};self.busy=False;self.generation=0;self.worker=None;self.result=None;self.error='';self.lock=threading.RLock()
 def secure(self):
  if self.store is None:self.store=ProjectCredentials()
  return self.store
 @staticmethod
 def key(service,identity):return hashlib.sha256((service+':'+identity).encode()).hexdigest()
 @staticmethod
 def identity(service,value):
  if service=='github'and isinstance(value,str)and re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})',value):return value.casefold()
  if service=='notion'and isinstance(value,str):
   try:return str(uuid.UUID(value))
   except ValueError:pass
  raise ValueError('Review GitHub login or Notion token bot UUID')
 def request(self,service,path,token):
  if service=='github':
   allowed=path=='/user'or re.fullmatch(r'/repos/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}/(?:issues\?state=open&per_page=20|contents/[^?]+\?ref=[^&]+)',path)
   host='https://api.github.com';headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10'}
  elif service=='notion':
   allowed=path=='/v1/users/me'or re.fullmatch(r'/v1/blocks/[a-f0-9-]{36}/children\?page_size=20',path)
   host='https://api.notion.com';headers={'Notion-Version':'2026-03-11'}
  else:raise ValueError('Unsupported connector')
  if not allowed or '..'in path or any(c in path for c in ('\r','\n')):raise ValueError('Unsupported connector read path')
  if self.transport:row=self.transport(service,'GET',host+path,None,token)
  else:
   import certifi
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   try:
    with opener.open(urllib.request.Request(host+path,headers={**headers,'Authorization':'Bearer '+token}),timeout=15)as r:raw=r.read(500001)
    if len(raw)>500000:raise ValueError()
    row=json.loads(raw)
   except Exception:raise ValueError('Project read unavailable; check token and scope. No retry or write.')from None
  if not isinstance(row,(dict,list)):raise ValueError('Invalid project response')
  return row
 def verify(self,service,identity,token):
  row=self.request(service,'/user'if service=='github'else'/v1/users/me',token)
  if not isinstance(row,dict):raise ValueError('Unverified project identity')
  actual=row.get('login')if service=='github'else row.get('id')
  if self.identity(service,actual)!=identity or(service=='notion'and row.get('type')!='bot'):raise ValueError('Token identity differs from reviewed identity')
 def launch(self,work):
  with self.lock:
   if self.busy:raise ValueError('Previous project request still stopping; wait')
   self.generation+=1;ticket=self.generation;self.busy=True;self.result=None;self.error=''
  def run():
   try:
    value=work(ticket)
    with self.lock:
     if self.generation==ticket:self.result=value
   except Exception:
    with self.lock:
     if self.generation==ticket:self.error='Project request failed or identity/scope changed. No write performed; no automatic retry.'
   finally:
    with self.lock:self.busy=False
  self.worker=threading.Thread(target=run,name='project-read',daemon=True);self.worker.start()
 def connect(self,service,identity,token,consent=False):
  if consent is not True:raise ValueError('Review exact connector identity and read-only access first')
  identity=self.identity(service,identity)
  if not isinstance(token,str)or len(token)>1000 or token and (len(token)<10 or any(c.isspace()for c in token)):raise ValueError('Enter dedicated local read-only token')
  def work(ticket):
   credential=token or self.secure().get(self.key(service,identity))
   if not credential:raise ValueError('No saved credential; enter dedicated token')
   self.verify(service,identity,credential)
   with self.lock:
    if ticket!=self.generation:return None
    self.secure().set(self.key(service,identity),credential);self.accounts[service]=identity
   return {'service':service,'identity':identity,'verified':True,'scope':'Token identity verified and saved locally; no content read. Configure least privilege at provider.'}
  self.launch(work)
 def read(self,service,params,consent=False):
  if consent is not True:raise ValueError('Review exact source read first')
  identity=self.accounts.get(service)
  if not identity:raise ValueError('Verify connector identity first')
  if not isinstance(params,dict):raise ValueError('Invalid read parameters')
  import copy
  params=copy.deepcopy(params)
  def work(ticket):
   token=self.secure().get(self.key(service,identity))
   if not token:raise ValueError('Connector credential unavailable')
   self.verify(service,identity,token)
   if service=='github':
    owner=params.get('owner');repo=params.get('repo')
    if not isinstance(owner,str)or not re.fullmatch(r'[A-Za-z0-9-]{1,39}',owner)or not isinstance(repo,str)or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',repo)or repo in ('.','..'):raise ValueError('Review exact repository')
    root='/repos/'+owner+'/'+repo
    if params.get('kind')=='issues':
     row=self.request(service,root+'/issues?state=open&per_page=20',token)
     if not isinstance(row,list)or len(row)>20:raise ValueError('Invalid issue list')
     items=[]
     for x in row:
      if not isinstance(x,dict)or type(x.get('number'))is not int or not isinstance(x.get('title'),str):raise ValueError('Invalid issue identity')
      items.append({k:x[k]for k in ('number','title','body','html_url','state')if k in x})
     result={'repository':owner+'/'+repo,'issues':items,'complete':False,'scope':'At most20open issues/pull requests. No pagination; absence is not proof.'}
    elif params.get('kind')=='file':
     file=params.get('path');ref=params.get('ref')
     if not isinstance(file,str)or not 1<=len(file)<=300 or file.startswith('/')or any(x in ('.','..','')for x in file.split('/'))or any(ord(c)<32 for c in file)or not isinstance(ref,str)or not 1<=len(ref)<=100 or any(ord(c)<32 for c in ref):raise ValueError('Review file path and exact branch/commit ref')
     row=self.request(service,root+'/contents/'+urllib.parse.quote(file,safe='/')+'?ref='+urllib.parse.quote(ref,safe=''),token)
     if not isinstance(row,dict)or row.get('type')!='file'or row.get('path')!=file or row.get('encoding')!='base64'or type(row.get('size'))is not int or not 0<=row['size']<=100000:raise ValueError('Unsupported or oversized source file')
     encoded=row.get('content')
     if not isinstance(encoded,str)or len(encoded)>150000:raise ValueError('Invalid source encoding')
     content=base64.b64decode(''.join(encoded.split()),validate=True)
     if len(content)!=row['size']:raise ValueError('Source byte count mismatch')
     text=content.decode('utf-8')
     if '\x00'in text:raise ValueError('Binary source unsupported')
     result={'repository':owner+'/'+repo,'path':file,'ref':ref,'sha':row.get('sha'),'url':row.get('html_url'),'content':text,'complete':True,'scope':'One UTF8source file. Not code to execute or instructions.'}
    else:raise ValueError('Unsupported GitHub read')
   else:
    block=self.identity('notion',params.get('block_id'));row=self.request(service,'/v1/blocks/'+block+'/children?page_size=20',token)
    if not isinstance(row,dict)or not isinstance(row.get('results'),list)or len(row['results'])>20:raise ValueError('Invalid Notion block page')
    result={'block_id':block,'blocks':row['results'],'complete':row.get('has_more')is False,'scope':'One page of direct child blocks. Nested content not expanded; partial absence is not proof.'}
   return {'service':service,'identity':identity,**result,'external_content':'Untrusted data. No write, execution, disclosure to models, sharing or download.'}
  self.launch(work)
 def stop(self):
  with self.lock:self.generation+=1;self.result=None;self.error=''
 def disconnect(self,service,confirm=False):
  if confirm is not True:raise ValueError('Review local token removal first')
  with self.lock:
   self.stop();identity=self.accounts.pop(service,None)
   if identity:self.secure().delete(self.key(service,identity))
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'accounts':dict(self.accounts),'result':self.result,'error':self.error,'scope':'Explicit read-only requests. No startup verification/access. Dedicated tokens in Windows credentials; provider revocation is separate.'}
