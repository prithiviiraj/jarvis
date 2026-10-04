"""Functional account routing. Secrets never enter settings files or status output."""
import json,threading,time,urllib.request,urllib.error
from pathlib import Path
from dataclasses import replace
from .provider_pool import Slot,ProviderPool,SLOT_IDS,KINDS
from .personas import ROLES
from .router import BrainRouter,NoRedirect,RouterError,ProviderFailure
from .providers import configured,ENDPOINTS,local_models
class BrainSettings:
 def __init__(self,store=None,path=None):
  self.store=store;self.path=Path(path)if path else None;self.rows={};self.assignments={};self.lock=threading.RLock();self.checks={};self.busy=set();self.consent=set();self.free=set();self.cooldowns={};self.local_gate=threading.Lock()
  if self.path and self.path.is_file():
   try:
    saved=json.loads(self.path.read_text());self.configure(saved.get('slots',[]),saved.get('assignments',{}),persist=False)
   except Exception:self.rows={};self.assignments={}
 def keys(self):
  if self.store is None:
   from .security import WindowsCredentials
   self.store=WindowsCredentials()
  return self.store
 def configure(self,rows,assignments,persist=True):
  if not isinstance(rows,list)or len(rows)>5 or not isinstance(assignments,dict):raise ValueError('At most five account slots required')
  slots=[];consent=set();free=set()
  for r in rows:
   if not isinstance(r,dict)or set(r)-{'id','provider','model','enabled','consent','free','label'}:raise ValueError('Invalid account settings')
   if r.get('enabled')is not True:continue
   kind=r.get('provider');model=r.get('model','').strip()
   if not model:model='automatic'
   slot=Slot(r.get('id'),kind,model,r.get('label',''));slots.append(slot)
   if r.get('consent')is True:consent.add(slot.id)
   if r.get('free')is True:free.add(slot.id)
  ids={s.id for s in slots}
  if len(ids)!=len(slots)or any(n not in ROLES or i not in ids for n,i in assignments.items()):raise ValueError('Assignments must select enabled slots')
  with self.lock:self.rows={s.id:s for s in slots};self.assignments=dict(assignments);self.consent=consent;self.free=free;self.cooldowns={}
  if persist and self.path:
   self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'slots':[{'id':s.id,'provider':s.provider,'model':s.model,'enabled':True,'label':s.label}for s in slots],'assignments':assignments},indent=2));tmp.replace(self.path)
 def set_key(self,sid,kind,key):
  if sid not in SLOT_IDS or kind not in KINDS or kind=='local':raise ValueError('Unknown cloud account')
  self.keys().set(kind+'/'+sid,key)
 def delete_key(self,sid,kind):
  if sid not in SLOT_IDS or kind not in KINDS or kind=='local':raise ValueError('Unknown cloud account')
  self.keys().delete(kind+'/'+sid)
 def snapshot(self):
  with self.lock:
   rows=[]
   for s in self.rows.values():
    present=False
    if s.provider!='local':
     try:present=self.keys().status(s.key_target).get('present',False)
     except Exception:pass
    rows.append({'id':s.id,'provider':s.provider,'model':s.model,'label':s.label,'enabled':True,'consent':s.id in self.consent,'free':s.id in self.free,'key_present':present,'cooldown_s':max(0,round(self.cooldowns.get(s.id,0)-time.monotonic()))})
   return {'slots':rows,'assignments':dict(self.assignments),'checks':dict(self.checks),'busy':list(self.busy),'consent_scope':'session only; free plan is user-confirmed, not verified by API'}
 def check(self,sid='local',notify=lambda *a:None):
  with self.lock:
   if sid in self.busy:return
   self.busy.add(sid);self.checks[sid]={'state':'checking'}
  def work():
   try:
    if sid=='local':
     models=local_models(timeout=8)
     if len(models)!=1:raise ValueError('Load exactly one chat model in LM Studio')
     result={'state':'ready','model':models[0],'scope':'loaded model discovery, not inference test'}
    else:
     s=self.rows.get(sid)
     if s is None:raise ValueError('Save this enabled slot first')
     if s.id not in self.consent or s.id not in self.free:raise ValueError('Confirm share-context consent and a free/no-billing account for this session')
     key=self.keys().get(s.key_target)
     if not key:raise ValueError('Save this slot key first')
     http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
     req=urllib.request.Request(ENDPOINTS[s.provider]+'/models',headers={'Authorization':'Bearer '+key,'Accept':'application/json'})
     with http.open(req,timeout=12)as r:
      raw=r.read(262145)
      if len(raw)>262144:raise ValueError('Model list too large')
      ids=[x['id']for x in json.loads(raw).get('data',[])if isinstance(x,dict)and isinstance(x.get('id'),str)]
     if s.model=='automatic':
      if s.provider=='groq':
       from .groq_models import PREFERRED
       choices=[m for m in PREFERRED if m in ids]
      elif s.provider=='gemini':choices=sorted([m for m in ids if 'flash' in m.lower() and not any(w in m.lower()for w in ('preview','image','tts','live','audio','embedding'))],reverse=True)
      else:choices=[m for m in ('meta/llama-3.3-70b-instruct','meta/llama-3.1-8b-instruct')if m in ids]
      if not choices:raise ValueError('No approved automatic chat model listed. Select an exact model ID')
      s=replace(s,model=choices[0])
      with self.lock:self.rows[sid]=s
     if s.model not in ids:
      with self.lock:self.checks[sid]={'state':'failed','models':ids[:100],'error':'Choose an exact listed model ID and save again'}
      raise ValueError('Selected model not listed. Available IDs shown below')
     started=time.monotonic();router=BrainRouter([replace(configured(s.provider,s.model),name=s.id,requires_free_plan=True,timeout=30)],key_store=_Keys(self,{sid:s}))
     answer=router.ask([{'role':'user','content':'Say hello in one short sentence.'}],cloud_consent=True,verified_free_providers=(sid,))
     result={'state':'ready','model':s.model,'models':ids[:100],'seconds':round(time.monotonic()-started,3),'reply':answer['text'][:120],'scope':'real text greeting; not audible voice latency or billing verification'}
   except Exception as e:
    # Never include response bodies, request headers or secrets in errors.
    code='HTTP_'+str(e.code)if isinstance(e,urllib.error.HTTPError)else str(e)if isinstance(e,(ValueError,RouterError))else type(e).__name__
    result={'state':'failed','error':code[:220],**({'models':ids[:100]}if 'ids' in locals()else{})}
   with self.lock:self.checks[sid]=result;self.busy.discard(sid)
   notify('status','Connection '+sid+': '+result['state'])
  t=threading.Thread(target=work,daemon=True);t.start();return t
 def router(self,name):return RoutedBrain(self,name)
 def candidates(self,name):
  with self.lock:
   primary=self.assignments.get(name);cloud=[s for s in self.rows.values()if s.provider!='local' and s.id in self.consent and s.id in self.free and s.model!='automatic' and self.cooldowns.get(s.id,0)<=time.monotonic()]
   cloud.sort(key=lambda s:s.id!=primary)
   slots=list(cloud)
  # Local always last, and no parallel local inference.
  return slots+[Slot('slot5','local','automatic')]
class _Keys:
 def __init__(self,settings,slots):self.settings=settings;self.slots=slots
 def get(self,name):return self.settings.keys().get(self.slots[name].key_target)
class RoutedBrain:
 def __init__(self,settings,name):self.settings=settings;self.name=name;self.last_diagnostics=[];self.last_warnings=[];self.reasoning_off=False
 def select_persona(self,name):
  if name not in ROLES:raise ValueError('Unknown persona')
  self.name=name
 def stream(self,messages,cloud_consent=False,cancel=None,**kw):
  errors=[]
  for s in self.settings.candidates(self.name):
   if cancel is not None and cancel.is_set():return
   local=s.provider=='local'
   if local:
    try:
     ids=local_models()
     if len(ids)!=1:continue
     s=Slot(s.id,'local',ids[0])
    except Exception:continue
   p=replace(configured(s.provider,s.model),name='local'if local else s.id,timeout=30,requires_free_plan=not local)
   router=BrainRouter([p],key_store=None if local else _Keys(self.settings,{s.id:s}))
   options={}
   if local and 'spark-x2.5' in s.model.lower():
    from .lmstudio_rest import SparkRecoveryTransport,NativeSparkTransport
    options['stream_transport']=NativeSparkTransport()if self.reasoning_off else SparkRecoveryTransport()
   emitted=False
   try:
    if local:
     while not self.settings.local_gate.acquire(timeout=.1):
      if cancel is not None and cancel.is_set():return
    try:
     for d in router.stream(messages,cloud_consent=not local,verified_free_providers=()if local else(s.id,),cancel=cancel,**options):
      emitted=True;yield d
    finally:
     if local:self.settings.local_gate.release()
    self.last_diagnostics=router.last_diagnostics;self.last_warnings=router.last_warnings
    if emitted:return
   except RouterError as e:
    self.last_diagnostics=router.last_diagnostics;errors.append(p.name+':'+str(e))
    if emitted:raise
    # Shared cooldown protects all personas using a rate-limited slot.
    if not local and any(c in str(e)for c in ('http-429','http-401','http-403')):
     with self.settings.lock:self.settings.cooldowns[s.id]=time.monotonic()+300
  raise RouterError('No configured brain answered. '+('; '.join(errors)[-220:]if errors else'Save and test cloud slots or start LM Studio.'))
 def ask(self,messages,**kw):
  parts=[];last={}
  for d in self.stream(messages,**kw):parts.append(d['text']);last=d
  return {**last,'text':''.join(parts)}

class SettingsPool:
 def __init__(self,settings):self.settings=settings
 def router(self,name,*a,**kw):return self.settings.router(name)
