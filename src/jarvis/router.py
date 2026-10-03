"""Reasoning-provider router. Cloud is opt-in; no tool calls or key files."""
from dataclasses import dataclass,replace
from .chat_payload import payload,reply_metadata
import json
import time
import threading
import urllib.error
import urllib.request
from urllib.parse import urlsplit

class RouterError(RuntimeError):pass
class ProviderFailure(RouterError):
    def __init__(self, code, retryable=True):
        self.code=code;self.retryable=retryable
        super().__init__('Provider unavailable ('+code+').')

@dataclass(frozen=True)
class Provider:
    name:str
    url:str
    model:str
    cloud:bool=False
    timeout:float=8.0
    requires_free_plan:bool=False
    allow_20b_fallback:bool=False
    def __post_init__(self):
        u=urlsplit(self.url)
        if not self.name or not self.model or u.username or u.password or u.query or u.fragment:
            raise ValueError('Invalid provider settings.')
        if self.cloud:
            if u.scheme!='https' or not u.hostname:raise ValueError('Cloud provider requires HTTPS.')
        elif u.scheme!='http' or u.hostname!='127.0.0.1' or not u.port:
            raise ValueError('Local provider must use 127.0.0.1.')
        if not 1 <= self.timeout <= 30:raise ValueError('Timeout must be 1-30 seconds.')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class HttpTransport:
    def __init__(self):self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def complete(self,provider,messages,key=None):
        headers={'Content-Type':'application/json','User-Agent':'JARVIS-experimental/0.1 (+https://github.com/prithiviiraj/jarvis)'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(provider.url.rstrip('/')+'/chat/completions',headers=headers,
          data=json.dumps(payload(provider.model,messages)).encode())
        try:
            with self.http.open(req,timeout=provider.timeout) as r:
                raw=r.read(1048577)
                if len(raw)>1048576:raise ProviderFailure('oversize',False)
                j=json.loads(raw)
                answer=j['choices'][0]['message']['content']
                if not isinstance(answer,str) or not answer.strip():raise ProviderFailure('empty-token-limit' if reply_metadata(j)['finish_category']=='length' else 'empty')
                return answer.strip()
        except urllib.error.HTTPError as e:
            raise ProviderFailure('http-'+str(e.code),e.code in (408,429,500,502,503,504)) from None
        except (urllib.error.URLError,TimeoutError,OSError):raise ProviderFailure('connection') from None
        except (ValueError,KeyError,IndexError,TypeError):raise ProviderFailure('malformed') from None

class BrainRouter:
    def __init__(self,providers,transport=None,key_store=None,clock=time.monotonic,break_seconds=60):
        if not providers or len({p.name for p in providers})!=len(providers):raise ValueError('Unique providers required.')
        self.providers=list(providers);self.transport=transport or HttpTransport();self.key_store=key_store
        self.clock=clock;self.break_seconds=break_seconds;self.disabled_until={};self.lock=threading.RLock()
    def reorder(self,names):
        if len(names)!=len(self.providers) or set(names)!={p.name for p in self.providers}:raise ValueError('Order must include every provider once.')
        with self.lock:
            byname={p.name:p for p in self.providers};self.providers=[byname[n] for n in names]
    def ask(self,messages,cloud_consent=False,preferred=None,contains_image=False,cloud_image_consent=False,verified_free_providers=()):
        if not isinstance(messages,list) or not messages:raise RouterError('A conversation is required.')
        ordered=list(self.providers)
        if preferred:
            if preferred not in {p.name for p in ordered}:raise RouterError('Preferred provider not configured.')
            ordered.sort(key=lambda p:p.name!=preferred)
        errors=[]
        for p in ordered:
            if p.requires_free_plan and p.name not in verified_free_providers:continue
            if p.cloud and (not cloud_consent or (contains_image and not cloud_image_consent)):continue
            if self.disabled_until.get(p.name,0)>self.clock():continue
            if p.cloud:
                try:key=self.key_store.get(p.name) if self.key_store else None
                except Exception:errors.append((p.name,'key-store-unavailable'));continue
                if not key:errors.append((p.name,'no-key'));continue
            else:key=None
            try:
                text=self.transport.complete(p,messages,key)
                return {'text':text,'provider':p.name,'model':p.model,'cloud':p.cloud,'fallbacks':errors}
            except ProviderFailure as exc:
                errors.append((p.name,exc.code))
                self.disabled_until[p.name]=self.clock()+self.break_seconds
                if not exc.retryable:break
        raise RouterError('No enabled brain answered'+(' ('+', '.join(name+':'+code for name,code in errors)+')' if errors else '')+'. Check your local server or enabled provider settings.')

    def stream(self,messages,cloud_consent=False,preferred=None,cancel=None,stream_transport=None,verified_free_providers=()):
        """Fail over only before any text has escaped; never mix provider answers."""
        from .streaming import StreamTransport
        if not isinstance(messages,list) or not messages:raise RouterError('A conversation is required.')
        transport=stream_transport or StreamTransport()
        with self.lock:ordered=list(self.providers)
        if preferred:
            if preferred not in {p.name for p in ordered}:raise RouterError('Preferred provider not configured.')
            ordered.sort(key=lambda p:p.name!=preferred)
        # Same-provider smaller-model fallback only after a transient pre-text failure.
        pending_fallback=False
        expanded=[]
        for item in ordered:
            expanded.append((item,False))
            if item.name=='groq' and item.model=='openai/gpt-oss-120b' and item.allow_20b_fallback:
                expanded.append((replace(item,model='openai/gpt-oss-20b'),True))
        for p,is_fallback in expanded:
            if is_fallback and not pending_fallback:continue
            if cancel is not None and cancel.is_set():return
            if p.requires_free_plan and p.name not in verified_free_providers:continue
            if p.cloud and not cloud_consent:continue
            with self.lock:
                if self.disabled_until.get(p.name,0)>self.clock():continue
            key=None
            if p.cloud:
                try:key=self.key_store.get(p.name) if self.key_store else None
                except Exception:continue
                if not key:continue
            emitted=False
            try:
                for text in transport.stream(p,messages,key,cancel):
                    if cancel is not None and cancel.is_set():return
                    if text:
                        emitted=True
                        yield {'text':text,'provider':p.name,'model':p.model,'cloud':p.cloud}
                if emitted:return
                if cancel is not None and cancel.is_set():return
                raise ProviderFailure('empty')
            except ProviderFailure as exc:
                pending_fallback=(not emitted and not is_fallback and p.name=='groq' and p.model=='openai/gpt-oss-120b' and exc.retryable and exc.code in ('http-429','http-408','http-500','http-502','http-503','http-504','connection','stream-timeout'))
                if not pending_fallback:
                    with self.lock:self.disabled_until[p.name]=self.clock()+self.break_seconds
                if emitted:raise RouterError('The answer stopped mid-sentence. Please try again.') from None
                if not exc.retryable:break
        raise RouterError('No enabled brain answered. Check your local server or enabled provider settings.')
