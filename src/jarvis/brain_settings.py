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
  self.store=store;self.path=Path(path)if path else None;self.rows={};self.assignments={};self.lock=threading.RLock();self.checks={};self.busy=set();self.consent=set();self.free=set();self.cooldowns={};self.local_gate=threading.Lock();self.warmup_cancel=threading.Event()
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
  if not isinstance(key,str)or not key.strip():raise ValueError('API key required')
  self.keys().set(kind+'/'+sid,key.strip())
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
     greeted=None
     if s.model=='automatic':
      if s.provider=='groq':
       from .groq_models import PREFERRED
       choices=[m for m in PREFERRED if m in ids]
      elif s.provider=='gemini':choices=sorted([m for m in ids if 'flash' in m.lower() and not any(w in m.lower()for w in ('preview','image','tts','live','audio','embedding','omni','veo'))],reverse=True)
      else:choices=[m for m in ('nvidia/nemotron-3.5-lightning-30b-a3b','meta/llama-3.3-70b-instruct','meta/llama-3.1-8b-instruct')if m in ids]
      if not choices:raise ValueError('No approved automatic chat model listed. Select an exact model ID')
      last_error=None;attempts=[]
      # Each listed candidate must answer the fixed public greeting; auth/quota errors stop immediately.
      for candidate in choices:
       started=time.monotonic()
       router=BrainRouter([replace(configured(s.provider,candidate),name=s.id,requires_free_plan=True,timeout=30)],key_store=_Keys(self,{sid:s}))
       try:greeted=router.ask([{'role':'user','content':'Say hello in one short sentence.'}],cloud_consent=True,verified_free_providers=(sid,));s=replace(s,model=candidate);break
       except Exception as e:
        if 'http-429' in str(e):raise ValueError('Automatic selection stopped at '+candidate+': rate limit or quota reached (HTTP 429). Wait and check this provider account limits; reset time is unknown. No paid fallback. The fetched list stays available for manual selection.')
        if any(w in str(e)for w in ('http-401','http-403')):raise ValueError('Automatic selection stopped at '+candidate+': provider rejected this key or access. Recheck the saved key.')
        last_error=e;attempts.append(candidate+' -> '+str(e)[:70])
      if greeted is None:raise ValueError('No approved automatic chat model answered the fixed greeting. '+('; '.join(attempts[:5]) if attempts else ', '.join(choices[:5]))+'. Pick an exact model from the fetched list and Save & test, or wait if quota was hit.')
      with self.lock:self.rows[sid]=s
     if s.provider=='gemini'and any(w in s.model.lower()for w in ('omni','veo','image','tts','audio','embedding','live')):raise ValueError('Selected Gemini model is not supported text chat. Clear Model ID for Automatic or choose a listed text Flash model.')
     if s.model not in ids:
      with self.lock:self.checks[sid]={'state':'failed','models':ids[:100],'error':'Choose an exact listed model ID and save again'}
      raise ValueError('Selected model not listed. Available IDs shown below')
     if greeted is None:
      started=time.monotonic();router=BrainRouter([replace(configured(s.provider,s.model),name=s.id,requires_free_plan=True,timeout=30)],key_store=_Keys(self,{sid:s}))
      greeted=router.ask([{'role':'user','content':'Say hello in one short sentence.'}],cloud_consent=True,verified_free_providers=(sid,))
     result={'state':'ready','model':s.model,'models':ids[:100],'seconds':round(time.monotonic()-started,3),'reply':greeted['text'][:120],'scope':'real text greeting; not audible voice latency or billing verification'}
   except Exception as e:
    # Never include response bodies, request headers or secrets in errors.
    code='HTTP_'+str(e.code)if isinstance(e,urllib.error.HTTPError)else str(e)if isinstance(e,(ValueError,RouterError))else type(e).__name__
    if code=='HTTP_429' or ('http-429'in code.lower() and not code.startswith('Automatic selection stopped')):code='HTTP429: rate limit or quota reached. Wait and check this provider account limits; reset time is unknown. No paid fallback.'
    elif isinstance(e,urllib.error.HTTPError)and e.code==400:code='HTTP400: the provider rejected this request before testing. For Gemini this usually means the saved API key is invalid, expired, or pasted with extra spaces. Copy a fresh key from the provider console (Google AI Studio for Gemini), Save key securely, then test again.'
    result={'state':'failed','error':code[:500],**({'models':ids[:100]}if 'ids' in locals()else{})}
   with self.lock:self.checks[sid]=result;self.busy.discard(sid)
   notify('status','Connection '+sid+': '+result['state'])
  t=threading.Thread(target=work,daemon=True);t.start();return t
 def list_models(self,sid,notify=lambda *a:None):
  """Fetch the account model list only; no test reply is sent."""
  with self.lock:
   if sid in self.busy:return
   self.busy.add(sid)
  def work():
   try:
    s=self.rows.get(sid)
    if sid=='local' or s is None:raise ValueError('Save this enabled cloud slot first')
    if s.id not in self.consent or s.id not in self.free:raise ValueError('Confirm share-context consent and a free/no-billing account for this session')
    key=self.keys().get(s.key_target)
    if not key:raise ValueError('Save this slot key first')
    http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    req=urllib.request.Request(ENDPOINTS[s.provider]+'/models',headers={'Authorization':'Bearer '+key,'Accept':'application/json'})
    with http.open(req,timeout=12)as r:
     raw=r.read(262145)
     if len(raw)>262144:raise ValueError('Model list too large')
     ids=[x['id']for x in json.loads(raw).get('data',[])if isinstance(x,dict)and isinstance(x.get('id'),str)]
    if not ids:raise ValueError('Provider returned an empty model list')
    result={'state':'models-listed','models':ids[:100],'scope':'model list only; no test reply sent. Listing does not confirm free quota or that a model answers.'}
   except Exception as e:
    code='HTTP_'+str(e.code)if isinstance(e,urllib.error.HTTPError)else str(e)if isinstance(e,(ValueError,RouterError))else type(e).__name__
    if code=='HTTP_429' or ('http-429'in code.lower() and not code.startswith('Automatic selection stopped')):code='HTTP429: rate limit or quota reached. Wait and check this provider account limits; reset time is unknown. No paid fallback.'
    elif isinstance(e,urllib.error.HTTPError)and e.code==400:code='HTTP400: the provider rejected this request. For Gemini this usually means the saved API key is invalid, expired, or pasted with extra spaces. Copy a fresh key from the provider console (Google AI Studio for Gemini), Save key securely, then retry.'
    result={'state':'failed','error':code[:220]}
   with self.lock:
    previous=self.checks.get(sid,{})
    if result.get('state')=='models-listed' and previous.get('state')=='ready':self.checks[sid]={**previous,'models':result['models']}
    else:self.checks[sid]=result
    self.busy.discard(sid)
   notify('status','Model list '+sid+': '+self.checks[sid].get('state','failed'))
  t=threading.Thread(target=work,daemon=True);t.start();return t
 def prewarm(self,consent=False,notify=lambda *a:None):
  """Fixed local greeting only. No cloud, history, keys, or implicit launch call."""
  if consent is not True:raise ValueError('Allow a fixed local LM Studio warmup first')
  with self.lock:
   if 'local-warmup'in self.busy:return
   self.warmup_cancel=threading.Event();cancel=self.warmup_cancel
   self.busy.add('local-warmup');self.checks['local-warmup']={'state':'waiting','scope':'fixed local greeting only; no conversation or cloud'}
  def work():
   acquired=False
   try:
    acquired=self.local_gate.acquire(timeout=2)
    if not acquired:raise ValueError('Local model is busy. Try warmup after the current reply')
    models=local_models(timeout=8)
    if len(models)!=1:raise ValueError('Load exactly one chat model in LM Studio')
    started=time.monotonic()
    router=BrainRouter([replace(configured('local',models[0]),timeout=20)])
    parts=[]
    for delta in router.stream([{'role':'user','content':'Say ready in one word.'}],cloud_consent=False,cancel=cancel):
     if cancel.is_set():break
     parts.append(delta.get('text',''))
    if cancel.is_set():raise ValueError('Local warmup cancelled')
    if not ''.join(parts).strip():raise ValueError('Local warmup returned no text')
    result={'state':'ready','model':models[0],'seconds':round(time.monotonic()-started,3),'scope':'fixed local inference time, not voice latency; no conversation or cloud'}
   except Exception as error:
    detail=str(error)if isinstance(error,(ValueError,RouterError))else type(error).__name__
    result={'state':'failed','error':detail[:220],'scope':'local-only warmup; no cloud fallback'}
   finally:
    if acquired:self.local_gate.release()
   if cancel.is_set():result={'state':'cancelled','scope':'local warmup stopped; no cloud fallback'}
   with self.lock:self.checks['local-warmup']=result;self.busy.discard('local-warmup')
   notify('status','Local warmup: '+result['state'])
  worker=threading.Thread(target=work,daemon=True);worker.start();return worker
 def stop_warmup(self):self.warmup_cancel.set()
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
    self.last_diagnostics=router.last_diagnostics;errors.append(('local('+s.model+')' if local else p.name)+':'+str(e))
    if emitted:raise
    # Shared cooldown protects all personas using a rate-limited slot.
    if not local and any(c in str(e)for c in ('http-429','http-401','http-403')):
     with self.settings.lock:self.settings.cooldowns[s.id]=time.monotonic()+300
  guidance=''
  if any(e.startswith('local') and 'empty' in e for e in errors):guidance=' The loaded LM Studio model returned no usable final text; it may not fit this chat template. Load a proven chat-instruct model (for example spark-x2.5-4b) or test an enabled cloud account.'
  raise RouterError('No configured brain answered. '+('; '.join(errors)[-220:]if errors else'Save and test cloud slots or start LM Studio.')+guidance)
 def ask(self,messages,**kw):
  parts=[];last={}
  for d in self.stream(messages,**kw):parts.append(d['text']);last=d
  return {**last,'text':''.join(parts)}

class SettingsPool:
 def __init__(self,settings):self.settings=settings
 def router(self,name,*a,**kw):return self.settings.router(name)
