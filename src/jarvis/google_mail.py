"""Exact reviewed Gmail sends with durable no-retry uncertainty and readback.
Never called by conversation/model content. UI review names account and all words.
"""
import base64,email.policy,json,ssl,threading,urllib.parse,urllib.request
from email.message import EmailMessage
from .connector_workflows import email_plan,digest
from .connector_journal import ConnectorJournal
from .google_mail_draft import encode,plain_message
from .google_oauth import SCOPES
from .google_read_connector import GoogleReadConnector,NoRedirect
class GoogleMail:
 def __init__(self,connection,path,transport=None):self.connection=connection;self.path=path;self.transport=transport;self.ledger=None;self.busy=False;self.error='';self.worker=None;self.lock=threading.RLock();self.generation=0
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'email')
  return self.ledger
 def prepare(self,to,subject,body,cc=()):
  if self.busy:raise ValueError('Previous Gmail action still stopping')
  if not self.connection.account or self.connection.busy:raise ValueError('Choose a connected Google account first')
  plan=email_plan(self.connection.account,to,subject,body,cc)
  self.error='';return self.journal().prepare(plan['payload'])
 def request(self,method,url,payload=None,account=None):
  parsed=urllib.parse.urlsplit(url);base='https://gmail.googleapis.com/gmail/v1/users/me/'
  allowed=(method=='POST'and url==base+'messages/send')or(method=='GET'and url.startswith(base+'messages/'))
  if not allowed or parsed.fragment or any(s in parsed.path for s in ('..','%2e','%2E')):raise ValueError('Unsupported Gmail destination')
  if not account or self.connection.account!=account:raise ValueError('Google account changed')
  token=self.connection.tokens.access(account,SCOPES['mail-send'if method=='POST'else'mail-read'])
  if self.transport:return self.transport(method,url,payload)
  import certifi
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  req=urllib.request.Request(url,method=method,data=json.dumps(payload).encode()if payload else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json'})
  with opener.open(req,timeout=15)as r:raw=r.read(2_000_001)
  if len(raw)>2_000_000:raise ValueError('Gmail response too large')
  result=json.loads(raw)
  if not isinstance(result,dict):raise ValueError('Gmail response invalid')
  return result
 def reader(self,email):return GoogleReadConnector(lambda:self.connection.tokens.access(email,SCOPES['mail-read']),email,self.transport)
 @staticmethod
 def same(sent,payload):
  return sent.get('complete')is True and sent.get('state')=='sent'and sent.get('account')==payload['account']and sent.get('to')==payload['to']and sent.get('cc')==payload['cc']and sent.get('subject')==payload['subject']and sent.get('body','')==payload['body'].replace('\r\n','\n')+(''if payload['body'].endswith('\n')else'\n')and not sent.get('attachments')
 def validate(self,payload,ticket,connection_ticket):
  if self.generation!=ticket or self.connection.generation!=connection_ticket or self.connection.busy or self.connection.account!=payload['account']:raise ValueError('Account or review changed')
  reader=self.reader(payload['account']);reader.verify_mail_account()
  # Inspect one bounded complete SENT page. Partial history blocks this first
  # implementation rather than pretending absence means no duplicate.
  history=reader.sent_ids(limit=100)
  if not history['complete']:raise ValueError('Sent history is partial; duplicate check is incomplete. Send manually or narrow in a later version.')
  for row in history['messages']:
   message=plain_message(reader.read_message(row['message_id'])['message'],payload['account'])
   if self.same(message,payload):raise ValueError('Exact message already sent; no duplicate send')
   if message.get('complete')is not True and message.get('to')==payload['to']and message.get('cc')==payload['cc']and message.get('subject')==payload['subject']:raise ValueError('Potential duplicate has unreadable body or attachments; inspect Google Sent before sending')
  if self.generation!=ticket or self.connection.generation!=connection_ticket:raise ValueError('Review stopped during validation')
  return True
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if self.busy:raise ValueError('Previous Gmail action still running')
  if confirm is not True or ledger.job.state!='review' or reviewed!=ledger.job.plan:raise ValueError('Review final Gmail account, recipients and words again')
  self.busy=True;self.error='';self.generation+=1;ticket=self.generation;connection_ticket=self.connection.generation
  def transport(payload):
   if self.generation!=ticket or self.connection.generation!=connection_ticket:raise ValueError('Send stopped before transport')
   encoded=encode({'payload':payload,'sha256':digest(payload)})
   # Fixed message ID aids finding an uncertain send after restart. Reuses the
   # durable review ID, never adds recipients, BCC, attachments or a reply thread.
   from email import message_from_bytes
   msg=message_from_bytes(base64.urlsafe_b64decode(encoded['raw']+'='*(-len(encoded['raw'])%4)),policy=email.policy.SMTP);msg['Message-ID']='<jarvis-'+reviewed['review_id']+'@jarvis.local>'
   body={'raw':base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip('=')}
   row=self.request('POST','https://gmail.googleapis.com/gmail/v1/users/me/messages/send',body,payload['account'])
   mid=row.get('id')
   if not isinstance(mid,str)or not mid or len(mid)>200:raise ValueError('Send response identity invalid')
   read=self.request('GET','https://gmail.googleapis.com/gmail/v1/users/me/messages/'+urllib.parse.quote(mid,safe='')+'?format=full',account=payload['account'])
   if read.get('id')!=mid or not self.same(plain_message(read,payload['account']),payload):raise ValueError('Exact sent readback not verified')
   return {'verified':True,'external_id':mid,'thread_id':row.get('threadId'),'scope':'Exact sent message readback verified. Delivery/recipient reading not proved.'}
  def work():
   try:ledger.submit(reviewed,True,lambda p:self.validate(p,ticket,connection_ticket),transport)
   except Exception as e:
    self.error='Gmail action blocked or outcome uncertain. Inspect ledger state before any retry.'
    # Only local predefined validation errors are surfaced, never transport text.
    if isinstance(e,ValueError)and str(e)in ('Exact message already sent; no duplicate send','Sent history is partial; duplicate check is incomplete. Send manually or narrow in a later version.'):self.error=str(e)
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='gmail-reviewed-send',daemon=True);self.worker.start()
 def stop(self):
  self.generation+=1
  if self.ledger:self.ledger.cancel()
 def reconcile(self,consent=False):
  if consent is not True or self.busy:raise ValueError('Review uncertain Gmail readback first')
  ledger=self.journal()
  if ledger.job.state!='uncertain':raise ValueError('No uncertain Gmail send')
  self.busy=True;self.error=''
  def work():
   try:
    def readback(payload):
     if self.connection.account!=payload['account']:raise ValueError('Connect original account to reconcile')
     reader=self.reader(payload['account']);reader.verify_mail_account();key='jarvis-'+ledger.job.plan['review_id']+'@jarvis.local';ids=reader.sent_ids(query='rfc822msgid:'+key,limit=20)
     for row in ids['messages']:
      sent=plain_message(reader.read_message(row['message_id'])['message'],payload['account'])
      if self.same(sent,payload):return {'verified':True,'external_id':row['message_id'],'scope':'Exact sent message found. Delivery not proved.'}
     # Empty search is not definitive absence and never unlocks resending.
     raise ValueError('Outcome remains unknown; inspect Google Sent manually')
    ledger.reconcile(readback)
   except Exception:self.error='Gmail outcome remains unknown. Do not retry; inspect Google Sent manually.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='gmail-reconcile',daemon=True);self.worker.start()
 def snapshot(self):
  try:state=self.journal().snapshot()
  except Exception:state={'state':'blocked','plan':None,'result':None};self.error='Connector ledger invalid. Preserve it and reconcile externally; no send or retry.'
  return {**state,'busy':self.busy,'error':self.error,'scope':'Exact new-message review only. No replies/attachments/BCC. Partial SENT history blocks send. Uncertain actions cannot be retried.'}
