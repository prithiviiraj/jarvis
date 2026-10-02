"""Reasoning-provider router. Cloud is opt-in; no tool calls or key files."""
from dataclasses import dataclass
import json
import time
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
        headers={'Content-Type':'application/json'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(provider.url.rstrip('/')+'/chat/completions',headers=headers,
          data=json.dumps({'model':provider.model,'messages':messages,'stream':False,'max_tokens':300}).encode())
        try:
            with self.http.open(req,timeout=provider.timeout) as r:
                raw=r.read(1048577)
                if len(raw)>1048576:raise ProviderFailure('oversize',False)
                j=json.loads(raw)
                answer=j['choices'][0]['message']['content']
                if not isinstance(answer,str) or not answer.strip():raise ProviderFailure('empty')
                return answer.strip()
        except urllib.error.HTTPError as e:
            raise ProviderFailure('http-'+str(e.code),e.code in (408,429,500,502,503,504)) from None
        except (urllib.error.URLError,TimeoutError,OSError):raise ProviderFailure('connection') from None
        except (ValueError,KeyError,IndexError,TypeError):raise ProviderFailure('malformed') from None

class BrainRouter:
    def __init__(self,providers,transport=None,key_store=None,clock=time.monotonic,break_seconds=60):
        if not providers or len({p.name for p in providers})!=len(providers):raise ValueError('Unique providers required.')
        self.providers=list(providers);self.transport=transport or HttpTransport();self.key_store=key_store
        self.clock=clock;self.break_seconds=break_seconds;self.disabled_until={}
    def reorder(self,names):
        if len(names)!=len(self.providers) or set(names)!={p.name for p in self.providers}:raise ValueError('Order must include every provider once.')
        byname={p.name:p for p in self.providers};self.providers=[byname[n] for n in names]
    def ask(self,messages,cloud_consent=False,preferred=None,contains_image=False,cloud_image_consent=False):
        if not isinstance(messages,list) or not messages:raise RouterError('A conversation is required.')
        ordered=list(self.providers)
        if preferred:
            if preferred not in {p.name for p in ordered}:raise RouterError('Preferred provider not configured.')
            ordered.sort(key=lambda p:p.name!=preferred)
        errors=[]
        for p in ordered:
            if p.cloud and (not cloud_consent or (contains_image and not cloud_image_consent)):continue
            if self.disabled_until.get(p.name,0)>self.clock():continue
            if p.cloud:
                key=self.key_store.get(p.name) if self.key_store else None
                if not key:errors.append((p.name,'no-key'));continue
            else:key=None
            try:
                text=self.transport.complete(p,messages,key)
                return {'text':text,'provider':p.name,'model':p.model,'cloud':p.cloud,'fallbacks':errors}
            except ProviderFailure as exc:
                errors.append((p.name,exc.code))
                self.disabled_until[p.name]=self.clock()+self.break_seconds
        raise RouterError('No enabled brain answered. Check your local server or enabled provider settings.')
