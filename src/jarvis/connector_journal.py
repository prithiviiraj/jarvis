"""Durable exact-review ledger. Interrupted effects never become retryable by restart.
Payloads may contain private user drafts. Local user data only; no token storage.
"""
import json,os,threading
from .connector_workflows import ReviewedEffect,digest
class ConnectorJournal:
 def __init__(self,path,kind):
  self.path=path;self.job=ReviewedEffect(kind);self.lock=threading.RLock()
  if path.exists():
   try:
    row=json.loads(path.read_text(encoding='utf-8'))
    if row.get('kind')!=kind or row.get('version')!=1:raise ValueError()
    state=row['state'];plan=row.get('plan')
    if state not in ('review','submitting','uncertain','completed','cancelled','idle'):raise ValueError()
    if plan and (not isinstance(plan,dict)or not isinstance(plan.get('review_id'),str)or plan.get('payload',{}).get('kind')!=kind or digest(plan['payload'])!=plan['sha256']):raise ValueError()
    if state in ('review','submitting','uncertain','completed')and not plan:raise ValueError()
    self.job.plan=plan;self.job.state='uncertain'if state=='submitting'else state;self.job.result=row.get('result')
   except Exception:raise ValueError('Connector ledger invalid. Preserve the file and reconcile externally; no send or retry.')from None
 def save(self):
  row={'version':1,'kind':self.job.kind,'state':self.job.state,'plan':self.job.plan,'result':self.job.result}
  self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp')
  with temp.open('w',encoding='utf-8')as f:json.dump(row,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
  os.replace(temp,self.path)
 def prepare(self,payload):
  with self.lock:
   result=self.job.prepare(payload);self.save();return result
 def cancel(self):
  with self.lock:self.job.cancel();self.save()
 def submit(self,reviewed,confirmed,live_validate,transport):
  def durable_transport(payload):
   # Persist before the first possible external effect. Disk failure stops send.
   with self.lock:
    if self.job.state!='submitting':raise ValueError('Effect stopped before transport; reconcile before retry')
    self.save()
   return transport(payload)
  try:return self.job.submit(reviewed,confirmed,live_validate,durable_transport)
  finally:
   with self.lock:self.save()
 def reconcile(self,readback):
  with self.lock:
   result=self.job.reconcile(readback);self.save();return result
 def snapshot(self):
  with self.lock:return self.job.snapshot()
