"""Bounded OpenAI-style SSE parsing. No tools or side effects, text deltas only."""
import json,time,urllib.request,urllib.error
from .chat_payload import payload
from .router import NoRedirect,ProviderFailure,local_http

def text_deltas(response,cancel=None,max_bytes=1048576,deadline=None):
    size=0;count=0
    while True:
        if cancel is not None and cancel.is_set():return
        if deadline is not None and time.monotonic()>deadline:raise ProviderFailure('stream-timeout')
        line=response.readline(16385)
        if not line:break
        size+=len(line)
        if size>max_bytes or len(line)>16384:raise ProviderFailure('oversize',False)
        try:line=line.decode('utf-8').strip()
        except UnicodeDecodeError:raise ProviderFailure('malformed',False) from None
        if not line or line.startswith(':') or not line.startswith('data:'):continue
        data=line[5:].strip()
        if data=='[DONE]':return
        try:
            event=json.loads(data)
            if 'error' in event:raise ProviderFailure('stream-error')
            choices=event.get('choices',[])
            if not choices:continue # usage events
            if choices[0].get('finish_reason')=='length':raise ProviderFailure('completion-token-limit',False)
            delta=choices[0].get('delta',{})
            # Ignore tool/function calls, role metadata and all non-text data.
            text=delta.get('content')
            if text is None:continue
            if not isinstance(text,str):raise ValueError()
        except (ValueError,TypeError,AttributeError,IndexError):raise ProviderFailure('malformed',False) from None
        if text:
            count+=len(text)
            if count>12000:raise ProviderFailure('oversize',False)
            yield text

class StreamTransport:
    def __init__(self):self.http=local_http();self.cloud_http=None
    def opener(self,provider):
        if not provider.cloud:return self.http
        if self.cloud_http is None:self.cloud_http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        return self.cloud_http
    def stream(self,provider,messages,key=None,cancel=None):
        headers={'Content-Type':'application/json','Accept':'text/event-stream','User-Agent':'JARVIS-experimental/0.1 (+https://github.com/prithiviiraj/jarvis)'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(provider.url.rstrip('/')+'/chat/completions',headers=headers,data=json.dumps(payload(provider.model,messages,True)).encode())
        try:
            with self.opener(provider).open(req,timeout=provider.timeout) as response:
                if 'text/event-stream' not in response.headers.get('Content-Type',''):raise ProviderFailure('not-streaming')
                yield from text_deltas(response,cancel,deadline=time.monotonic()+30)
        except urllib.error.HTTPError as e:raise ProviderFailure('http-'+str(e.code),e.code in (408,429,500,502,503,504)) from None
        except (urllib.error.URLError,TimeoutError,OSError):raise ProviderFailure('connection') from None

def sentences(chunks,max_chars=220):
    """Yield bounded readable clauses. Never execute output as instructions."""
    pending=''
    for chunk in chunks:
        pending+=chunk
        while pending:
            boundary=next((i+1 for i,c in enumerate(pending) if c in '.!?\n' and (i==len(pending)-1 or pending[i+1].isspace())),None)
            if boundary is None and len(pending)>=max_chars:
                boundary=pending.rfind(' ',0,max_chars)
                if boundary<1:boundary=max_chars
            if boundary is None:break
            part=pending[:boundary].strip();pending=pending[boundary:]
            if part:yield part
    if pending.strip():yield pending.strip()
