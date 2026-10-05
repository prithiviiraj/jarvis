"""Managed in-process Laya inference. Never executes a browser action."""
import os,threading
from . import laya_assets
from .experimental.browser_proposals import request,propose
from .experimental.laya_local import normalize
class LayaEngine:
 def __init__(self):
  self.lock=threading.Lock();self.agent=None;self.loading=False;self.error='';self.generation=0
 def snapshot(self):return {'ready':self.agent is not None,'loading':self.loading,'error':self.error,'backend':'inbuilt CPU Laya; no external server'}
 def stop(self):self.generation+=1;self.agent=None;self.error=''
 def load(self,consent=False):
  if consent is not True:raise ValueError('Review loading the local Laya CPU model first')
  if self.loading:raise ValueError('Laya engine already loading')
  ticket=self.generation;self.loading=True;self.error=''
  def run():
   try:
    root=laya_assets.cache()
    if not laya_assets.ready(root):raise ValueError('Download and verify Laya model first')
    os.environ.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','USE_TF':'0','HF_HUB_DISABLE_TELEMETRY':'1'})
    import laya,torch
    torch.set_num_threads(min(4,os.cpu_count()or 1))
    agent=laya.load(str(root),device='cpu',expected_sha256={a['name']:a['sha256']for a in laya_assets.ASSETS})
    if 'head_max_len_train'in agent.cfg:agent.cfg['head_max_len']=agent.cfg['head_max_len_train']
    if ticket==self.generation:self.agent=agent
   except Exception as error:
    if ticket==self.generation:self.error=type(error).__name__+': Laya could not load verified local model. No download or browser action started.'
   finally:self.loading=False
  thread=threading.Thread(target=run,daemon=True);thread.start();return thread
 def prepare(self,snapshot,goal,hosts,now,current_snapshot_id):
  agent=self.agent
  if agent is None:raise ValueError('Load the inbuilt Laya engine first')
  if not self.lock.acquire(blocking=False):raise ValueError('Laya engine is busy')
  try:
   payload=request(snapshot,goal,hosts,now)
   result=agent.predict(payload['state'],payload['questions'])
   return propose(snapshot,goal,hosts,now,normalize(result),current_snapshot_id)
  finally:self.lock.release()
