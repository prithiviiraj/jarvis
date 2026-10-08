"""Dedicated exact reviewed GitHub issue creation. No model/chat entry or auto retries."""
import json,re,ssl,threading,urllib.request
from .connector_journal import ConnectorJournal
from .project_connectors import NoRedirect
class GitHubIssue:
 def __init__(self,projects,path,transport=None):self.projects=projects;self.path=path;self.transport=transport;self.ledger=None;self.worker=None;self.busy=False;self.generation=0;self.error='';self.lock=threading.RLock()
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'github-issue')
  return self.ledger
 def prepare(self,owner,repo,title,body,write_scope=False):
  if self.busy or self.projects.busy:raise ValueError('Previous project request still running')
  identity=self.projects.accounts.get('github')
  if not identity:raise ValueError('Verify GitHub token identity this session first')
  if write_scope is not True:raise ValueError('Review separate issue-write permission; read access alone is not approval')
  if not isinstance(owner,str)or not re.fullmatch(r'[A-Za-z0-9-]{1,39}',owner)or not isinstance(repo,str)or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',repo)or repo in ('.','..'):raise ValueError('Choose exact repository')
  if not isinstance(title,str)or not 1<=len(title.strip())<=200 or any(ord(c)<32 for c in title):raise ValueError('Review bounded plain issue title')
  if not isinstance(body,str)or not 1<=len(body)<=10000 or '\x00'in body:raise ValueError('Review bounded exact issue body')
  payload={'kind':'github-issue','identity':identity,'owner':owner,'repo':repo,'title':title.strip(),'body':body,'scope':'Creates one GitHub issue and triggers repository notifications. No PR/code changes, labels, assignees, attachments or model content. Token must have Issues write; no scope upgrade performed.'}
  ledger=self.journal()
  if ledger.job.state=='completed' and ledger.job.plan and ledger.job.plan['payload']==payload:raise ValueError('Exact last issue already completed; inspect its URL instead of creating a duplicate')
  self.error='';return ledger.prepare(payload)
 def request(self,method,path,token,payload=None):
  if not re.fullmatch(r'/repos/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}(?:/issues(?:/[1-9][0-9]*)?)?',path)or '..'in path or method not in ('GET','POST')or method=='POST'and not path.endswith('/issues'):raise ValueError('Unsupported issue destination')
  url='https://api.github.com'+path
  if self.transport:return self.transport(method,url,payload,token)
  import certifi
  http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  req=urllib.request.Request(url,method=method,data=json.dumps(payload).encode()if payload is not None else None,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2026-03-10'})
  with http.open(req,timeout=15)as r:raw=r.read(500001)
  if len(raw)>500000:raise ValueError('Oversized issue response')
  row=json.loads(raw)
  if not isinstance(row,dict):raise ValueError('Invalid issue response')
  return row
 def validate(self,p,ticket,project_ticket):
  if self.generation!=ticket or self.projects.generation!=project_ticket or self.projects.busy or self.projects.accounts.get('github')!=p['identity']:raise ValueError('Project identity/session changed')
  token=self.projects.secure().get(self.projects.key('github',p['identity']))
  if not token:raise ValueError('Credential unavailable')
  self.projects.verify('github',p['identity'],token);root='/repos/'+p['owner']+'/'+p['repo'];row=self.request('GET',root,token)
  if not isinstance(row,dict)or row.get('full_name','').casefold()!=(p['owner']+'/'+p['repo']).casefold()or row.get('has_issues')is not True or row.get('archived')is not False:raise ValueError('Exact repository not writable for issue creation')
  if self.generation!=ticket or self.projects.generation!=project_ticket:raise ValueError('Review stopped')
  return token,root
 @staticmethod
 def verified(row,p):
  return isinstance(row,dict)and row.get('title')==p['title']and row.get('body')==p['body']and isinstance(row.get('user'),dict)and row['user'].get('login','').casefold()==p['identity']and 'pull_request'not in row and type(row.get('number'))is int and row['number']>0 and isinstance(row.get('html_url'),str) and row['html_url'].casefold()==('https://github.com/'+p['owner']+'/'+p['repo']+'/issues/'+str(row['number'])).casefold()
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if self.busy or confirm is not True or ledger.job.state!='review'or reviewed!=ledger.job.plan:raise ValueError('Review exact GitHub identity/repository/title/body first')
  self.busy=True;self.generation+=1;ticket=self.generation;project_ticket=self.projects.generation;self.error='';auth={}
  def check(p):auth['token'],auth['root']=self.validate(p,ticket,project_ticket);return True
  def send(p):
   if self.generation!=ticket or self.projects.generation!=project_ticket:raise ValueError('Stopped before issue transport')
   row=self.request('POST',auth['root']+'/issues',auth['token'],{'title':p['title'],'body':p['body']})
   if not self.verified(row,p):raise ValueError('Unverified issue creation response')
   observed=self.request('GET',auth['root']+'/issues/'+str(row['number']),auth['token'])
   if not self.verified(observed,p)or observed['number']!=row['number']or observed['html_url']!=row['html_url']:raise ValueError('Exact issue readback not verified')
   return {'verified':True,'external_id':str(row['number']),'url':row['html_url'],'scope':'Exact issue readback. Notifications may have fired; delivery/reading not verified.'}
  def run():
   try:ledger.submit(reviewed,True,check,send)
   except Exception:self.error='Issue blocked or outcome uncertain; inspect ledger/repository before any retry. No automatic resend.'
   finally:self.busy=False
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def stop(self):
  self.generation+=1
  if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  if self.ledger is None and self.path.exists():self.journal()
  return {'busy':self.busy,'error':self.error,**(self.ledger.snapshot()if self.ledger else{'state':'idle','plan':None,'result':None}),'scope':'Exact UI-reviewed issue only. Private local draft ledger, no startup sends. Uncertain effect is not retryable; inspect GitHub manually.'}
