"""Exact finite RAW text updates. Review prior cells; no model entry or retries."""
import json,re,ssl,threading,time,urllib.parse,urllib.request
from .connector_journal import ConnectorJournal
from .google_authorization import GoogleAuthorization
from .google_oauth import SCOPES
from .google_read_connector import NoRedirect
class SheetsWrite:
 def __init__(self,connection,path,transport=None,identity=None):
  self.connection=connection;self.path=path;self.transport=transport;self.identity=identity;self.ledger=None;self.busy=False;self.worker=None;self.generation=0;self.error=''
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'sheets-write')
  return self.ledger
 @staticmethod
 def rectangle(sheet,rectangle,values):
  if not isinstance(sheet,str)or not re.fullmatch(r'[A-Za-z0-9_ ]{1,80}',sheet):raise ValueError('Use exact simple tab name (letters, digits, spaces, underscore)')
  m=re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,5}):([A-Z]{1,3})([1-9][0-9]{0,5})',rectangle or '')
  if not m:raise ValueError('Finite rectangle required')
  def col(s):
   n=0
   for c in s:n=n*26+ord(c)-64
   return n
  width=col(m[3])-col(m[1])+1;height=int(m[4])-int(m[2])+1
  if width<1 or height<1 or width*height>100:raise ValueError('Maximum100ordered cells')
  if not isinstance(values,list)or len(values)!=height or any(not isinstance(r,list)or len(r)!=width or any(not isinstance(c,str)or len(c)>1000 or '\x00'in c for c in r)for r in values):raise ValueError('Exact rectangular text values required')
  if len(json.dumps(values,ensure_ascii=False).encode())>8000:raise ValueError('Keep exact cell text under8KB')
  return "'"+sheet+"'!"+rectangle,height,width
 def request(self,account,file_id,method,range_name=None,values=None):
  if not isinstance(file_id,str)or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',file_id)or method not in ('GET','PUT'):raise ValueError('Exact spreadsheet required')
  if self.connection.account!=account or self.connection.busy:raise ValueError('Google account changed')
  token=self.connection.tokens.access(account,SCOPES['sheets-write'])
  base='https://sheets.googleapis.com/v4/spreadsheets/'+file_id
  if range_name is None:
   if method!='GET':raise ValueError('No spreadsheet mutation')
   url=base+'?fields=spreadsheetId,spreadsheetUrl,properties(title),sheets(properties(sheetId,title,gridProperties))';payload=None
  else:
   url=base+'/values/'+urllib.parse.quote(range_name,safe='')
   if method=='GET':url+='?majorDimension=ROWS&valueRenderOption=FORMULA';payload=None
   else:url+='?valueInputOption=RAW&includeValuesInResponse=true&responseValueRenderOption=UNFORMATTED_VALUE';payload={'range':range_name,'majorDimension':'ROWS','values':values}
  if self.transport:row=self.transport(method,url,payload)
  else:
   import certifi
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   req=urllib.request.Request(url,method=method,data=json.dumps(payload).encode()if payload is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json'})
   with opener.open(req,timeout=15)as reply:raw=reply.read(500001)
   if len(raw)>500000:raise ValueError('Oversized response')
   row=json.loads(raw)
  if not isinstance(row,dict):raise ValueError('Invalid Sheets response')
  return row
 def who(self,account):
  if self.connection.account!=account or self.connection.busy:raise ValueError('Google account changed')
  token=self.connection.tokens.access(account,SCOPES['sheets-write']);who=self.identity(token)if self.identity else GoogleAuthorization().identity(token)
  if not isinstance(who,dict)or who.get('email_verified')is not True or str(who.get('email','')).casefold()!=account.casefold():raise ValueError('Live identity mismatch')
 def metadata(self,account,file_id,sheet):
  row=self.request(account,file_id,'GET');tabs=[x.get('properties',{})for x in row.get('sheets',[])if isinstance(x,dict)]
  tabs=[x for x in tabs if x.get('title')==sheet]
  if row.get('spreadsheetId')!=file_id or len(tabs)!=1 or type(tabs[0].get('sheetId'))is not int or not isinstance(row.get('properties',{}).get('title'),str)or len(row['properties']['title'])>500:raise ValueError('Spreadsheet/tab identity not verified')
  return {'title':row['properties']['title'],'sheet_id':tabs[0]['sheetId'],'sheet':sheet,'grid':tabs[0].get('gridProperties',{}),'url':row.get('spreadsheetUrl')}
 @staticmethod
 def cells(row,range_name,height,width):
  if row.get('range')not in (range_name,range_name.replace("'",''))or row.get('majorDimension')not in (None,'ROWS'):raise ValueError('Returned range changed')
  rows=row.get('values',[])
  if not isinstance(rows,list)or len(rows)>height:raise ValueError('Invalid cell rows')
  for r in rows:
   if not isinstance(r,list)or len(r)>width or any(type(c)not in (str,int,float,bool)or isinstance(c,str)and len(c)>10000 for c in r):raise ValueError('Invalid prior cells')
  return [list(rows[i])+['']*(width-len(rows[i]))if i<len(rows)else ['']*width for i in range(height)]
 def launch(self,work):
  if self.busy or self.connection.busy:raise ValueError('Previous request still running')
  self.busy=True;self.error='';self.generation+=1;ticket=self.generation;conn_ticket=self.connection.generation
  def run():
   try:work(ticket,conn_ticket)
   except Exception:self.error='Sheet action blocked or outcome uncertain. No automatic retry; inspect local ledger and spreadsheet.'
   finally:self.busy=False
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def valid(self,ticket,conn_ticket,account):
  if self.generation!=ticket or self.connection.generation!=conn_ticket or self.connection.account!=account:raise ValueError('Review stopped or account changed')
 def prepare(self,file_id,sheet,rectangle,values,write_scope=False):
  if write_scope is not True:raise ValueError('Review separate Sheets write scope')
  range_name,height,width=self.rectangle(sheet,rectangle,values);account=self.connection.account
  if not account:raise ValueError('Connect exact account first')
  values=json.loads(json.dumps(values));ledger=self.journal()
  if ledger.job.state in ('uncertain','submitting'):raise ValueError('Inspect uncertain result; no retry')
  def work(ticket,conn_ticket):
   self.who(account);meta=self.metadata(account,file_id,sheet);prior=self.cells(self.request(account,file_id,'GET',range_name),range_name,height,width);self.valid(ticket,conn_ticket,account)
   m=re.fullmatch(r'([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)',rectangle);lastcol=0
   for c in m[3]:lastcol=lastcol*26+ord(c)-64
   grid=meta['grid']
   if type(grid.get('rowCount'))is not int or type(grid.get('columnCount'))is not int or int(m[4])>grid['rowCount']or lastcol>grid['columnCount']:raise ValueError('Range outside verified grid')
   if len(json.dumps(prior,ensure_ascii=False).encode())>8000 or len(json.dumps(values,ensure_ascii=False).encode())>8000:raise ValueError('Keep prior/new cell data under8KB each for native review')
   payload={'kind':'sheets-write','expires_at':time.time()+120,'account':account,'file_id':file_id,'metadata':meta,'rectangle':rectangle,'range':range_name,'values':values,'before':prior,'scope':'Overwrites these100or fewer cells with RAW text, including empty strings. No formulas, format changes, append, sharing or deletion. Prior cells rechecked but concurrent edits after check cannot be locked. OAuth permission can edit/create/delete ALL spreadsheets; product limits this action.'}
   ledger.prepare(payload)
  self.launch(work)
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if confirm is not True or ledger.job.state!='review'or reviewed!=ledger.job.plan:raise ValueError('Review exact account/file/tab/prior/new cells first')
  def work(ticket,conn_ticket):
   def validate(p):
    if time.time()>=p['expires_at']:raise ValueError('Review expired; recapture prior cells')
    self.valid(ticket,conn_ticket,p['account']);self.who(p['account']);range_name,h,w=self.rectangle(p['metadata']['sheet'],p['rectangle'],p['values'])
    if range_name!=p['range']or self.metadata(p['account'],p['file_id'],p['metadata']['sheet'])!=p['metadata']or self.cells(self.request(p['account'],p['file_id'],'GET',range_name),range_name,h,w)!=p['before']:raise ValueError('Prior cells or spreadsheet changed; recapture review')
    self.valid(ticket,conn_ticket,p['account']);return True
   def send(p):
    self.valid(ticket,conn_ticket,p['account']);r,h,w=self.rectangle(p['metadata']['sheet'],p['rectangle'],p['values']);row=self.request(p['account'],p['file_id'],'PUT',r,p['values'])
    if row.get('spreadsheetId')!=p['file_id']or row.get('updatedCells')!=h*w:raise ValueError('Write response not verified')
    self.valid(ticket,conn_ticket,p['account']);observed=self.cells(self.request(p['account'],p['file_id'],'GET',r),r,h,w)
    if observed!=p['values']:raise ValueError('Exact RAW cell readback mismatch')
    return {'verified':True,'external_id':p['file_id']+':'+r,'url':p['metadata']['url'],'scope':'Exact cell readback observed; later concurrent edits not prevented.'}
   ledger.submit(reviewed,True,validate,send)
  self.launch(work)
 def stop(self):
  self.generation+=1
  if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  if self.ledger is None and self.path.exists():self.journal()
  return {'busy':self.busy,'error':self.error,**(self.ledger.snapshot()if self.ledger else {'state':'idle','plan':None,'result':None})}
