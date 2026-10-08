"""One reviewed plain paragraph replacement. No creation/append/delete/model route."""
import json,ssl,threading,time,urllib.request
from .connector_journal import ConnectorJournal
from .project_connectors import NoRedirect
class NotionText:
 def __init__(self,projects,path,transport=None):self.projects=projects;self.path=path;self.transport=transport;self.ledger=None;self.generation=0;self.busy=False;self.worker=None;self.error=''
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'notion-text')
  return self.ledger
 def request(self,method,block,token,text=None):
  block=self.projects.identity('notion',block)
  if method not in ('GET','PATCH'):raise ValueError('Unsupported paragraph method')
  url='https://api.notion.com/v1/blocks/'+block;payload={'paragraph':{'rich_text':[{'type':'text','text':{'content':text}}]if text else []}}if method=='PATCH'else None
  if self.transport:row=self.transport(method,url,payload,token)
  else:
   import certifi
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   req=urllib.request.Request(url,method=method,data=json.dumps(payload).encode()if payload is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json','Notion-Version':'2026-03-11'})
   with opener.open(req,timeout=15)as reply:raw=reply.read(500001)
   if len(raw)>500000:raise ValueError('Oversized response')
   row=json.loads(raw)
  if not isinstance(row,dict):raise ValueError('Invalid block response')
  return row
 def plain(self,row,block):
  if row.get('object')!='block'or self.projects.identity('notion',row.get('id'))!=block or row.get('type')!='paragraph'or row.get('in_trash')is not False or row.get('has_children')is not False:raise ValueError('Only existing active leaf paragraphs supported')
  body=row.get('paragraph',{});rich=body.get('rich_text');text=''
  if body.get('color')not in (None,'default')or not isinstance(rich,list)or len(rich)>20 or any(k not in ('rich_text','color')for k in body):raise ValueError('Styled/extended paragraphs not supported')
  for x in rich:
   if not isinstance(x,dict)or x.get('type')!='text'or not isinstance(x.get('text'),dict)or not isinstance(x['text'].get('content'),str)or x['text'].get('link')is not None or x.get('href')is not None:raise ValueError('Links/mentions/equations not supported')
   a=x.get('annotations',{})
   if not isinstance(a,dict):raise ValueError('Invalid annotations')
   if any(a.get(k,False)is not False for k in ('bold','italic','strikethrough','underline','code'))or a.get('color','default')!='default'or any(k not in ('bold','italic','strikethrough','underline','code','color')for k in a):raise ValueError('Rich formatting would be lost; refused')
   if x.get('plain_text',x['text']['content'])!=x['text']['content']:raise ValueError('Plain text mismatch')
   text+=x['text']['content']
  if len(text)>2000 or len(text.encode())>6000:raise ValueError('Prior paragraph too large')
  parent=row.get('parent');edited=row.get('last_edited_time')
  if not isinstance(parent,dict)or parent.get('type')not in ('page_id','block_id')or not isinstance(edited,str):raise ValueError('Parent/edit identity unavailable')
  self.projects.identity('notion',parent.get(parent['type']))
  return {'text':text,'parent':parent,'last_edited_time':edited}
 def token(self,identity):
  if self.projects.busy or self.projects.accounts.get('notion')!=identity:raise ValueError('Project identity changed')
  token=self.projects.secure().get(self.projects.key('notion',identity))
  if not token:raise ValueError('Credential unavailable')
  self.projects.verify('notion',identity,token);return token
 def valid(self,ticket,project_ticket,identity):
  if self.generation!=ticket or self.projects.generation!=project_ticket or self.projects.accounts.get('notion')!=identity:raise ValueError('Review stopped/identity changed')
 def launch(self,work):
  if self.busy or self.projects.busy:raise ValueError('Previous project request running')
  self.generation+=1;ticket=self.generation;project_ticket=self.projects.generation;self.busy=True;self.error=''
  def run():
   try:work(ticket,project_ticket)
   except Exception:self.error='Paragraph action blocked or outcome uncertain. No automatic retry; inspect Notion and local ledger.'
   finally:self.busy=False
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def prepare(self,block,text,write_scope=False):
  if write_scope is not True:raise ValueError('Review separate Notion update-content capability')
  block=self.projects.identity('notion',block);identity=self.projects.accounts.get('notion')
  if not identity:raise ValueError('Verify Notion bot identity first')
  if not isinstance(text,str)or len(text)>2000 or len(text.encode())>6000 or '\x00'in text:raise ValueError('Bounded exact text required; empty clears paragraph')
  ledger=self.journal()
  if ledger.job.state in ('submitting','uncertain'):raise ValueError('Inspect uncertain result; no retry')
  def work(ticket,project_ticket):
   token=self.token(identity);before=self.plain(self.request('GET',block,token),block);self.valid(ticket,project_ticket,identity)
   ledger.prepare({'kind':'notion-text','identity':identity,'block_id':block,'before':before,'text':text,'expires_at':time.time()+120,'scope':'Replaces this one plain leaf paragraph. Empty text clears it. No append, creation, links, formatting, child edits or deletion. Token requires separate update-content capability on shared pages. Concurrent changes after precheck cannot be locked.'})
  self.launch(work)
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if confirm is not True or ledger.job.state!='review'or reviewed!=ledger.job.plan:raise ValueError('Review bot/block/parent/prior/new text first')
  def work(ticket,project_ticket):
   auth={}
   def check(p):
    self.valid(ticket,project_ticket,p['identity'])
    if time.time()>=p['expires_at']:raise ValueError('Review expired; recapture')
    auth['token']=self.token(p['identity'])
    if self.plain(self.request('GET',p['block_id'],auth['token']),p['block_id'])!=p['before']:raise ValueError('Prior block changed; recapture')
    self.valid(ticket,project_ticket,p['identity']);return True
   def send(p):
    self.valid(ticket,project_ticket,p['identity']);row=self.request('PATCH',p['block_id'],auth['token'],p['text']);observed=self.plain(row,p['block_id'])
    if observed['text']!=p['text']or observed['parent']!=p['before']['parent']:raise ValueError('Paragraph write response mismatch')
    self.valid(ticket,project_ticket,p['identity']);observed=self.plain(self.request('GET',p['block_id'],auth['token']),p['block_id'])
    if observed['text']!=p['text']or observed['parent']!=p['before']['parent']:raise ValueError('Exact paragraph readback mismatch')
    return {'verified':True,'external_id':p['block_id'],'scope':'Exact plain paragraph readback, later edits not prevented.'}
   ledger.submit(reviewed,True,check,send)
  self.launch(work)
 def stop(self):
  self.generation+=1
  if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  try:
   if self.ledger is None and self.path.exists():self.journal()
   state=self.ledger.snapshot()if self.ledger else {'state':'idle','plan':None,'result':None}
  except Exception:
   state={'state':'blocked','plan':None,'result':None};self.error='Local paragraph ledger invalid. Preserve it and inspect external state; no action or retry.'
  return {'busy':self.busy,'error':self.error,**state}
