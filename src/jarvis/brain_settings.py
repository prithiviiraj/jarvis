"""Functional account routing. Secrets never enter settings files or status output."""
import json,threading,time,ssl,urllib.request,urllib.error
from pathlib import Path
from dataclasses import replace
from .provider_pool import Slot,ProviderPool,SLOT_IDS,KINDS
from .personas import ROLES
from .router import BrainRouter,NoRedirect,RouterError,ProviderFailure
from .providers import configured,ENDPOINTS,local_models
def account_models(kind,key):
 """No redirects, bounded list, certificate recovery, and safe errors for every slot."""
 from .groq_models import error_code,APP_UA
 def load(context=None):
  handlers=[urllib.request.ProxyHandler({}),NoRedirect()]
  if context is not None:handlers.append(urllib.request.HTTPSHandler(context=context))
  http=urllib.request.build_opener(*handlers)
  req=urllib.request.Request(ENDPOINTS[kind]+'/models',headers={'Authorization':'Bearer '+key,'Accept':'application/json','User-Agent':APP_UA})
  with http.open(req,timeout=12)as r:
   raw=r.read(262145)
   if len(raw)>262144:raise ValueError('Model list too large')
   data=json.loads(raw).get('data',[])
   if not isinstance(data,list):raise ValueError('Invalid model list')
   return [x['id']for x in data if isinstance(x,dict)and isinstance(x.get('id'),str)and x.get('active',True)is True]
 try:
  try:return load()
  except Exception as exc:
   if not error_code(exc).startswith('TLS_'):raise
   import certifi
   return load(ssl.create_default_context(cafile=certifi.where()))
 except Exception as exc:
  code=error_code(exc)
  hint=' For Gemini HTTP400, the saved key may be invalid or expired.'if kind=='gemini'and code.startswith('HTTP_400')else ''
  raise ValueError('Account model lookup failed ('+code+'). No greeting sent. Check this slot key and provider account.'+hint)from None

class BrainSettings:
 def __init__(self,store=None,path=None):
  self.store=store;self.path=Path(path)if path else None;self.rows={};self.assignments={};self.lock=threading.RLock();self.checks={};self.busy=set();self.consent=set();self.free=set();self.cooldowns={};self.live={'state':'not checked','models':[],'checked_at':None,'scope':'loaded-instance discovery only, not inference'};self.live_busy=False;self.live_last=-1e20;self.local_gate=threading.Lock();self.warmup_cancel=threading.Event()
  if self.path and self.path.is_file():
   try:
    saved=json.loads(self.path.read_text());assignments=saved.get('assignments',{});legacy=''.join(('K','AI'));assignments={('SILA'if n==legacy else n):slot for n,slot in assignments.items()};self.configure(saved.get('slots',[]),assignments,persist=False)
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
   return {'slots':rows,'assignments':dict(self.assignments),'checks':dict(self.checks),'live':self.live_snapshot(),'busy':list(self.busy),'consent_scope':'session only; free plan is user-confirmed, not verified by API'}
 def refresh_live(self,force=False):
  """Bounded asynchronous loopback discovery, never cloud tests or model loading."""
  with self.lock:
   if self.live_busy or(not force and time.monotonic()-self.live_last<10):return
   self.live_busy=True;self.live_last=time.monotonic()
  def work():
   from .providers import local_live_models
   try:
    models=local_live_models(timeout=2)
    result={'state':'loaded'if models else'no loaded model','models':models,'checked_at':time.time(),'scope':'actual loaded instances; not inference or response verification'}
   except Exception as error:
    result={'state':'unavailable','models':[],'checked_at':time.time(),'error':type(error).__name__+': loaded-instance discovery unavailable; no loaded model claimed','scope':'discovery only; older server metadata may be unsupported'}
   with self.lock:self.live=result;self.live_busy=False
  worker=threading.Thread(target=work,daemon=True);worker.start();return worker
 def live_snapshot(self):
  with self.lock:
   state=dict(self.live);state['models']=list(self.live.get('models',[]));state['busy']=self.live_busy
   stamp=state.get('checked_at');state['age_s']=round(time.time()-stamp,1)if stamp else None
   if stamp and time.time()-stamp>15:state['state']='stale'
   profiles={}
   for name in ROLES:
    sid=self.assignments.get(name);slot=self.rows.get(sid)
    if slot and slot.provider!='local':
     check=self.checks.get(sid,{})
     profiles[name]={'route':sid,'provider':slot.provider,'state':'permission required'if sid not in self.consent or sid not in self.free else 'last test '+check.get('state','not checked'),'model':slot.model,'scope':'configured route; no independent background worker; cached test is not live connectivity'}
    else:
     chosen=slot.model if slot else'automatic';models=state['models'];match=[x for x in models if chosen=='automatic'or chosen in(x['id'],x.get('key'))]
     profiles[name]={'route':sid or'local fallback','provider':'local','state':'loaded route'if state['state']=='loaded'and match else state['state']if chosen=='automatic'else'configured model not observed loaded','model':chosen,'scope':'shared loaded local model; not proof of an answer or separate worker'}
   state['profiles']=profiles;return state
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
     ids=account_models(s.provider,key)
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
    ids=account_models(s.provider,key)
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
  return slots+[self.local_candidate(name)]
 def local_candidate(self,name):
  with self.lock:
   primary=self.rows.get(self.assignments.get(name));local=[s for s in self.rows.values()if s.provider=='local']
   if primary and primary.provider=='local':return primary
   if len(local)==1:return local[0]
  return Slot('slot5','local','automatic')
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
  from .intent_routing import local_turn
  image_turn=any(isinstance(row,dict)and isinstance(row.get('content'),list)and any(isinstance(part,dict)and part.get('type')=='image_url'for part in row['content'])for row in messages)
  configured_chat=kw.pop('configured_chat',False)is True
  api_only=kw.pop('api_only',False)is True
  local_only=kw.pop('local_only',False)is True or image_turn or (not configured_chat and local_turn(messages))
  candidates=[self.settings.local_candidate(self.name)]if local_only else self.settings.candidates(self.name)
  if api_only:candidates=[s for s in candidates if s.provider!='local']
  for s in candidates:
   if cancel is not None and cancel.is_set():return
   local=s.provider=='local'
   if local:
    try:
     ids=local_models()
     if s.model!='automatic':
      if s.model not in ids:
       live=self.settings.live_snapshot();matches=[m['id']for m in live.get('models',[])if m.get('key')==s.model and m['id']in ids]if live.get('state')=='loaded'else[]
       if len(matches)==1:s=Slot(s.id,'local',matches[0])
       else:raise ValueError('Assigned local model '+s.model+' is not observed loaded. Loaded choices: '+(', '.join(ids)or'none'))
     elif len(ids)==1:s=Slot(s.id,'local',ids[0])
     elif not ids:raise ValueError('LM Studio returned no loaded chat instance. Check server and model load state.')
     else:raise ValueError('Several local chat instances are loaded: '+', '.join(ids)+'. Assign an exact local model to this profile; none was picked.')
    except Exception as error:
     errors.append('local discovery: '+(str(error)if isinstance(error,(ValueError,RouterError))else type(error).__name__)[:220]);continue
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
      emitted=True;yield {**d,'provider':s.provider,'slot':s.id}
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
  guidance=' Casual replies are local-only by your choice. Start LM Studio and load one chat model; no API fallback was sent.'if local_only else ''
  if any(e.startswith('local') and 'empty' in e for e in errors):guidance=' The loaded LM Studio model returned no usable final text; it may not fit this chat template. Load a proven chat-instruct model (for example spark-x2.5-4b) or test an enabled cloud account.'
  raise RouterError('No configured brain answered. '+('; '.join(errors)[-220:]if errors else'Save and test cloud slots or start LM Studio.')+guidance)
 def ask(self,messages,**kw):
  parts=[];last={}
  for d in self.stream(messages,**kw):parts.append(d['text']);last=d
  return {**last,'text':''.join(parts)}

class SettingsPool:
 def __init__(self,settings):self.settings=settings
 def router(self,name,*a,**kw):return self.settings.router(name)
