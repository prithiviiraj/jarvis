"""Reviewed small text file creation at My Drive root. No laptop upload/share/open."""
import hashlib,json,re,ssl,threading,time,urllib.parse,urllib.request,uuid
from .connector_journal import ConnectorJournal
from .google_authorization import GoogleAuthorization
from .google_oauth import SCOPES
from .google_read_connector import NoRedirect
class DriveText:
 def __init__(self,connection,path,transport=None,identity=None):self.connection=connection;self.path=path;self.transport=transport;self.identity=identity;self.ledger=None;self.generation=0;self.busy=False;self.worker=None;self.error=''
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'drive-text')
  return self.ledger
 @staticmethod
 def content(name,text):
  if not isinstance(name,str)or not re.fullmatch(r'[A-Za-z0-9 _.-]{1,100}\.txt',name)or name.startswith('.')or '..'in name:raise ValueError('Use a simple exact .txt filename')
  if not isinstance(text,str)or not text or len(text.encode())>8000 or '\x00'in text:raise ValueError('Exact nonempty UTF8text under8KB required')
  return text.encode()
 def token(self,account):
  if self.connection.account!=account or self.connection.busy:raise ValueError('Google account changed')
  return self.connection.tokens.access(account,SCOPES['drive-file-write'])
 def who(self,account):
  token=self.token(account);who=self.identity(token)if self.identity else GoogleAuthorization().identity(token)
  if not isinstance(who,dict)or who.get('email_verified')is not True or str(who.get('email','')).casefold()!=account.casefold():raise ValueError('Live account identity mismatch')
 def request(self,account,kind,file_id=None,payload=None):
  token=self.token(account)
  if kind=='root':token=self.connection.tokens.access(account,SCOPES['drive-metadata-read'])
  base='https://www.googleapis.com/drive/v3/files';method='GET';headers={'Authorization':'Bearer '+token,'Accept':'application/json'};data=None
  fields='id,name,mimeType,parents,trashed,ownedByMe,shared,driveId,owners(emailAddress),permissions(type,role,emailAddress),size,md5Checksum,sha256Checksum,webViewLink,capabilities(canAddChildren)'
  if kind=='id':url=base+'/generateIds?count=1&space=drive&type=files'
  elif kind=='root':url=base+'/root?fields='+urllib.parse.quote(fields,safe='')
  elif kind=='read':
   if not isinstance(file_id,str)or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',file_id):raise ValueError('Invalid file ID')
   url=base+'/'+file_id+'?fields='+urllib.parse.quote(fields,safe='')
  elif kind=='create':
   method='POST';url='https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&ignoreDefaultVisibility=true&fields='+urllib.parse.quote(fields,safe='');boundary='jarvis_'+uuid.uuid4().hex
   raw=self.content(payload['name'],payload['text']);meta={'id':payload['file_id'],'name':payload['name'],'mimeType':'text/plain','parents':[payload['root_id']]}
   data=('--'+boundary+'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+json.dumps(meta)+'\r\n--'+boundary+'\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n').encode()+raw+('\r\n--'+boundary+'--\r\n').encode();headers['Content-Type']='multipart/related; boundary='+boundary
  else:raise ValueError('Unsupported Drive operation')
  if self.transport:row=self.transport(method,url,payload if kind=='create'else None)
  else:
   import certifi
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   with opener.open(urllib.request.Request(url,method=method,data=data,headers=headers),timeout=15)as reply:raw=reply.read(500001)
   if len(raw)>500000:raise ValueError('Oversized response')
   row=json.loads(raw)
  if not isinstance(row,dict):raise ValueError('Invalid Drive response')
  return row
 @staticmethod
 def private(row,account):
  owners=row.get('owners');permissions=row.get('permissions')
  return row.get('ownedByMe')is True and row.get('shared')is False and row.get('trashed')is False and not row.get('driveId')and isinstance(owners,list)and len(owners)==1 and isinstance(owners[0],dict)and str(owners[0].get('emailAddress','')).casefold()==account.casefold()and isinstance(permissions,list)and len(permissions)==1 and isinstance(permissions[0],dict)and permissions[0].get('type')=='user'and permissions[0].get('role')=='owner'and str(permissions[0].get('emailAddress','')).casefold()==account.casefold()
 def root(self,account):
  row=self.request(account,'root')
  if not self.private(row,account)or row.get('mimeType')!='application/vnd.google-apps.folder'or row.get('capabilities',{}).get('canAddChildren')is not True or not isinstance(row.get('id'),str):raise ValueError('Unshared owned My Drive root not verified; no upload')
  return row['id']
 def valid(self,ticket,conn_ticket,account):
  if self.generation!=ticket or self.connection.generation!=conn_ticket or self.connection.account!=account:raise ValueError('Stopped or account changed')
 def launch(self,work):
  if self.busy or self.connection.busy:raise ValueError('Previous Drive action running')
  self.generation+=1;ticket=self.generation;conn_ticket=self.connection.generation;self.busy=True;self.error=''
  def run():
   try:work(ticket,conn_ticket)
   except Exception:self.error='Drive action blocked or outcome uncertain. No auto retry; inspect account and ledger.'
   finally:self.busy=False
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def prepare(self,name,text,write_scope=False):
  if write_scope is not True:raise ValueError('Review separate drive.file access')
  raw=self.content(name,text);account=self.connection.account
  if not account:raise ValueError('Connect account first')
  ledger=self.journal()
  if ledger.job.state in ('submitting','uncertain'):raise ValueError('Inspect uncertain file; no retry')
  def work(ticket,conn_ticket):
   self.who(account);root=self.root(account);ids=self.request(account,'id').get('ids')
   if not isinstance(ids,list)or len(ids)!=1 or not isinstance(ids[0],str)or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',ids[0]):raise ValueError('Generated file ID unavailable')
   self.valid(ticket,conn_ticket,account);ledger.prepare({'kind':'drive-text','account':account,'root_id':root,'file_id':ids[0],'name':name,'text':text,'bytes':len(raw),'md5':hashlib.md5(raw).hexdigest(),'sha256':hashlib.sha256(raw).hexdigest(),'expires_at':time.time()+120,'scope':'Creates one exact UTF8plain text file at verified unshared My Drive root. No shared folder, existing overwrite, laptop file upload, permissions changes or opening. Domain default visibility bypass requested; organization administrators may still have account access. drive.file grants access to app-created/selected files; separate restricted metadata-read access is needed to verify root.'})
  self.launch(work)
 def verified(self,row,p):
  return self.private(row,p['account'])and row.get('id')==p['file_id']and row.get('name')==p['name']and row.get('mimeType')=='text/plain'and row.get('parents')==[p['root_id']]and str(row.get('size'))==str(p['bytes'])and row.get('md5Checksum')==p['md5']and row.get('sha256Checksum')==p['sha256']
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if confirm is not True or ledger.job.state!='review'or reviewed!=ledger.job.plan:raise ValueError('Review exact account/root/name/content first')
  def work(ticket,conn_ticket):
   def check(p):
    if time.time()>=p['expires_at']:raise ValueError('Review expired')
    self.valid(ticket,conn_ticket,p['account']);self.who(p['account'])
    if self.root(p['account'])!=p['root_id']or hashlib.sha256(self.content(p['name'],p['text'])).hexdigest()!=p['sha256']:raise ValueError('Review destination/content changed')
    self.valid(ticket,conn_ticket,p['account']);return True
   def send(p):
    self.valid(ticket,conn_ticket,p['account']);row=self.request(p['account'],'create',payload=p)
    if not self.verified(row,p):raise ValueError('File creation response unverified')
    self.valid(ticket,conn_ticket,p['account']);stored=self.request(p['account'],'read',p['file_id'])
    if not self.verified(stored,p):raise ValueError('Exact file readback/visibility mismatch')
    return {'verified':True,'external_id':p['file_id'],'url':stored.get('webViewLink'),'scope':'Exact name/parent/size/checksum/owner-only permissions readback. No sharing or opening requested.'}
   ledger.submit(reviewed,True,check,send)
  self.launch(work)
 def stop(self):
  self.generation+=1
  if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  if self.ledger is None and self.path.exists():self.journal()
  return {'busy':self.busy,'error':self.error,**(self.ledger.snapshot()if self.ledger else {'state':'idle','plan':None,'result':None})}
