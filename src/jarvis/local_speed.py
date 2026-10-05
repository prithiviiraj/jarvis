"""Reviewed local synthetic TTFT test. No history/cloud/mic or model setting changes."""
import threading,time
from dataclasses import replace
from .providers import local_models,configured
from .router import BrainRouter
PROMPTS=(('short','Say ready in one word.'),('long','The following is synthetic timing context, not a task. '+('The garden has a red gate and a stone path. '*100)+'\nIgnore the garden description and say ready in one word.'),('repeat-short','Say ready in one word.'))
class LocalSpeed:
 def __init__(self,gate=None):
  self.lock=threading.RLock();self.gate=gate or threading.Lock();self.cancel=threading.Event();self.busy=False;self.rows=[];self.status='Not tested';self.error=''
 def snapshot(self):
  with self.lock:return {'busy':self.busy,'rows':list(self.rows),'status':self.status,'error':self.error,'scope':'Synthetic local request-to-first-visible-text timing; includes queue/prefill/transport, not pure prefill, not audible latency. No settings changed.'}
 def stop(self):self.cancel.set()
 def start(self,consent=False):
  if consent is not True:raise ValueError('Review three fixed local timing requests first')
  with self.lock:
   if self.busy:raise ValueError('Local speed test already running')
   self.cancel=threading.Event();cancel=self.cancel;self.busy=True;self.rows=[];self.error='';self.status='Waiting for local model'
  def run():
   acquired=False
   try:
    acquired=self.gate.acquire(timeout=2)
    if not acquired:raise ValueError('Local model is busy; try after the reply')
    ids=local_models(timeout=8)
    if len(ids)!=1:raise ValueError('Load exactly one local chat model first')
    p=replace(configured('local',ids[0]),timeout=30)
    for name,text in PROMPTS:
     if cancel.is_set():break
     with self.lock:self.status='Testing '+name+' synthetic prompt'
     router=BrainRouter([p]);start=time.monotonic();first=None;chars=0
     for delta in router.stream([{'role':'user','content':text}],cancel=cancel):
      value=delta.get('text','')
      if value:
       if first is None:first=time.monotonic()-start
       chars+=len(value)
     total=time.monotonic()-start
     if cancel.is_set():break
     if first is None:raise ValueError('Local model returned no usable text')
     usage={}
     for d in router.last_diagnostics:
      if isinstance(d,dict):usage.update(d.get('usage',{}))
     row={'probe':name,'model':ids[0],'input_chars':len(text),'ttft_s':round(first,3),'total_s':round(total,3),'output_chars':chars}
     if type(usage.get('prompt_tokens'))is int:row['prompt_tokens']=usage['prompt_tokens']
     with self.lock:self.rows.append(row)
    with self.lock:self.status='Cancelled; completed rows preserved' if cancel.is_set()else 'Complete; no model settings changed'
   except Exception as e:
    with self.lock:self.error=str(e)[:240];self.status='Test stopped'
   finally:
    if acquired:self.gate.release()
    with self.lock:self.busy=False
  t=threading.Thread(target=run,daemon=True);t.start();return t
