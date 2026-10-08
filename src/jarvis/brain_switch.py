"""Exact reviewed session-only local brain switch, no cloud or implicit model loading."""
import copy,hashlib,json,re,threading,time
from .providers import local_live_models,configured
from .router import BrainRouter
class BrainSwitch:
 def __init__(self,settings,discover=local_live_models,probe=None,clock=time.monotonic):self.clock=clock;self.review_deadline=0;self.settings=settings;self.discover=discover;self.probe=probe or self._probe;self.pending=None;self.verified={};self.generation=0;self.worker=None;self.launching=False;self.status='No local switch verified';self.error='';self.lock=threading.RLock()
 def _probe(self,model,cancel):return BrainRouter([configured('local',model)]).ask([{'role':'user','content':'Say ready in one word.'}],cloud_consent=False,cancel=cancel)
 def prepare(self,persona,slot,model):
  from .personas import ROLES
  with self.lock,self.settings.lock:
   if self.launching or (self.worker and self.worker.is_alive()):raise ValueError('Current brain verification still stopping/running')
   row=self.settings.rows.get(slot)
   if persona not in ROLES or row is None or row.provider!='local':raise ValueError('Choose an existing enabled local slot and persona')
   if any(n!=persona and sid==slot for n,sid in self.settings.assignments.items()):raise ValueError('Local slot is shared with another persona; choose a dedicated slot first')
   if model not in [m['id']for m in self.discover()]:raise ValueError('Choose an actually loaded local model instance')
   payload={'persona':persona,'slot':slot,'model':model,'previous_model':row.model,'assignments':dict(self.settings.assignments),'unassigned_local_fallback':True,'scope':'Fixed local greeting verification, then session-only exact local route. This local slot is also the fallback for unassigned personas. No cloud fallback, model load, speech or saved settings change. Stop cancels pending verification; it does not undo an applied switch.'}
   self.pending={'payload':payload,'sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()};self.review_deadline=self.clock()+120;self.status='Review exact local brain switch (120seconds)';self.error='';return copy.deepcopy(self.pending)
 def apply(self,reviewed,confirm=False):
  with self.lock:
   if self.clock()>=self.review_deadline or confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review exact local brain switch')
   p=copy.deepcopy(self.pending['payload']);self.launching=True;self.generation+=1;ticket=self.generation;self.pending=None;self.cancel=threading.Event();cancel=self.cancel;self.status='Verifying fixed local greeting, route unchanged'
  def work():
   acquired=False
   try:
    acquired=self.settings.local_gate.acquire(timeout=2)
    if not acquired:raise ValueError('Local model busy; route unchanged')
    if cancel.is_set():return
    if p['model']not in [m['id']for m in self.discover()]:raise ValueError('Model no longer loaded; route unchanged')
    result=self.probe(p['model'],cancel)
    if not isinstance(result,dict)or not str(result.get('text','')).strip()or result.get('model')!=p['model']:raise ValueError('Exact model greeting not verified; route unchanged')
    if p['model']not in [m['id']for m in self.discover()]:raise ValueError('Model unloaded during greeting; route unchanged')
    with self.lock,self.settings.lock:
     if ticket!=self.generation or cancel.is_set():return
     row=self.settings.rows.get(p['slot'])
     if row is None or row.provider!='local'or row.model!=p['previous_model']or self.settings.assignments!=p['assignments']:raise ValueError('Routes changed during verification; review again')
     from .provider_pool import Slot
     self.settings.rows[p['slot']]=Slot(row.id,'local',p['model'],row.label);self.settings.assignments[p['persona']]=row.id;self.settings.pinned_local[p['persona']]=row.id
     self.verified[p['persona']]={'model':p['model'],'slot':row.id,'skin':'local-'+str(int(hashlib.sha256(p['model'].encode()).hexdigest()[:4],16)%360),'scope':'Exact local fixed greeting verified; session-only route, not hardware speech or sustained latency'};self.status='Verified local route switched for '+p['persona']
   except Exception as e:
    with self.lock:
     if ticket==self.generation:self.error=str(e)[:180]if isinstance(e,ValueError)else type(e).__name__;self.status='Local switch not completed; route unchanged'
   finally:
    if acquired:self.settings.local_gate.release()
  with self.lock:
   if ticket!=self.generation or cancel.is_set():self.launching=False;return
   self.worker=threading.Thread(target=work,daemon=True)
   try:self.worker.start()
   finally:self.launching=False
 def stop(self):
  with self.lock:self.generation+=1;self.pending=None;getattr(self,'cancel',threading.Event()).set();self.status='Pending switch stopped; applied route is not undone'
 def clear(self):self.stop();self.verified={}
 def snapshot(self):
  with self.lock:
   if not self.verified:return {'pending':copy.deepcopy(self.pending)if self.clock()<self.review_deadline else None,'verified':{},'busy':self.launching or bool(self.worker and self.worker.is_alive()),'status':self.status,'error':self.error}
  with self.lock,self.settings.lock:
   verified={n:r for n,r in self.verified.items()if self.settings.assignments.get(n)==r['slot'] and self.settings.pinned_local.get(n)==r['slot'] and self.settings.rows.get(r['slot']) and self.settings.rows[r['slot']].provider=='local' and self.settings.rows[r['slot']].model==r['model']}
   return {'pending':copy.deepcopy(self.pending)if self.clock()<self.review_deadline else None,'verified':copy.deepcopy(verified),'busy':self.launching or bool(self.worker and self.worker.is_alive()),'status':self.status,'error':self.error}
def spoken_request(text):
 if not isinstance(text,str):return None
 m=re.fullmatch(r'\s*(?:(?:hey\s+)?jarvis[,.:]?\s+)?switch (?:your |my )?brain to ([A-Za-z0-9_./-]{1,200})[.!]?\s*',text,re.I)
 return m.group(1)if m else None
