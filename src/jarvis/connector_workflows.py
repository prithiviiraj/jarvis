"""Review-bound connector plans. No account credentials, network or automatic sends."""
import hashlib,json,re,time,uuid
from email.utils import parseaddr

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def address(value):
 if not isinstance(value,str)or '\n'in value or '\r'in value:raise ValueError('Invalid email recipient')
 name,mail=parseaddr(value)
 if name or mail!=value or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',mail):raise ValueError('Choose an exact email address, not a name')
 return mail

def email_plan(account,to,subject,body,cc=(),attachments=()):
 address(account)
 if not isinstance(to,(list,tuple))or not to:raise ValueError('Choose the final recipients')
 recipients=[address(x)for x in to];copies=[address(x)for x in cc]
 if not isinstance(subject,str)or not 0<len(subject)<=300 or '\n'in subject or '\r'in subject:raise ValueError('Review a valid subject')
 if not isinstance(body,str)or not 0<len(body)<=20000:raise ValueError('Review bounded email text')
 if attachments:raise ValueError('Attachments need separately verified file content; not supported in this plan yet')
 row={'kind':'email','account':account,'to':recipients,'cc':copies,'subject':subject,'body':body,'attachments':[]}
 return {'payload':row,'sha256':digest(row),'scope':'Exact reviewed recipients and words; a plan is not a send'}

def duplicate_warning(plan,history):
 row=plan['payload'];matches=[]
 if not isinstance(history,dict)or history.get('account')!=row['account']or not isinstance(history.get('messages'),list):raise ValueError('Sent-history account not verified')
 for item in history['messages']:
  if not isinstance(item,dict)or item.get('account')!=row['account']or not item.get('message_id')or item.get('state')!='sent':continue
  fields=('to','cc','subject','body','attachments')
  if all(item.get(k)==row[k]for k in fields):matches.append({'message_id':item['message_id'],'sent_at':item.get('sent_at'),'thread_id':item.get('thread_id')})
 return {'matches':matches,'complete':history.get('complete')is True,'scope':'Exact account/recipient/subject/body/attachment equality only. Absence is not proof when history is partial.'}

class ReviewedEffect:
 def __init__(self,kind):self.kind=kind;self.plan=None;self.state='idle';self.result=None;self.generation=0
 def prepare(self,payload):
  if self.state in ('submitting','uncertain'):raise ValueError('Reconcile the existing action before preparing another')
  if not isinstance(payload,dict)or payload.get('kind')!=self.kind:raise ValueError('Wrong action kind')
  self.generation+=1;self.plan={'payload':json.loads(json.dumps(payload)),'sha256':digest(payload),'review_id':uuid.uuid4().hex};self.state='review';self.result=None;return json.loads(json.dumps(self.plan))
 def cancel(self):
  self.generation+=1
  if self.state=='submitting':self.state='uncertain'
  elif self.state!='uncertain':self.state='cancelled';self.plan=None
 def submit(self,reviewed,confirmed,live_validate,transport):
  if self.state!='review'or not self.plan or confirmed is not True or reviewed!=self.plan or digest(self.plan['payload'])!=self.plan['sha256']:raise ValueError('Review changed; inspect final action again')
  # Caller must verify live account, destination, availability and owner grant.
  if live_validate(json.loads(json.dumps(self.plan['payload'])))is not True:raise ValueError('Live authority/destination check did not pass')
  ticket=self.generation;self.state='submitting'
  try:result=transport(json.loads(json.dumps(self.plan['payload'])))
  except Exception:
   self.state='uncertain';raise ValueError('Submission outcome unknown. Do not retry until reconciled.')from None
  if ticket!=self.generation:self.state='uncertain';raise ValueError('Stopped during submission; outcome must be reconciled')
  if not isinstance(result,dict)or result.get('verified')is not True or not result.get('external_id'):self.state='uncertain';raise ValueError('Server result not verified; reconcile before retry')
  self.state='completed';self.result=result;return result
 def reconcile(self,readback):
  if self.state!='uncertain'or not self.plan:raise ValueError('No uncertain action to reconcile')
  result=readback(json.loads(json.dumps(self.plan['payload'])))
  if not isinstance(result,dict)or result.get('verified')is not True:raise ValueError('Outcome remains unknown')
  if result.get('external_id'):self.state='completed';self.result=result
  elif result.get('definitively_absent')is True:self.state='review'
  else:raise ValueError('Empty result is not verified absence')
  return result
 def snapshot(self):return {'state':self.state,'plan':json.loads(json.dumps(self.plan)),'result':json.loads(json.dumps(self.result)),'scope':'Review-bound state only; live connector/grant checks still required'}
