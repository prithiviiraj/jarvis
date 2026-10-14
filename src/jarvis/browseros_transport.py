"""Independent bounded MCP discovery client for separately installed BrowserOS neo.
No browser actions, account import, script execution or automatic installer.
"""
import json,re,threading,urllib.request
from urllib.parse import urlsplit
PINNED_BROWSER_VERSION='0.51.1.2'
PROTOCOL='2025-06-18'
MAX_BYTES=1024*1024

def endpoint(value):
 if not isinstance(value,str):raise ValueError('BrowserOS endpoint is required')
 try:p=urlsplit(value);port=p.port
 except ValueError:raise ValueError('Invalid BrowserOS endpoint')from None
 if p.scheme!='http' or p.hostname!='127.0.0.1' or not port or p.username or p.password or p.path!='/mcp' or p.query or p.fragment:
  raise ValueError('Use the verified local BrowserOS URL: http://127.0.0.1:PORT/mcp')
 return value

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise RuntimeError('BrowserOS endpoint redirects are not allowed')

def http(method,url,headers,payload):
 request=urllib.request.Request(url,data=json.dumps(payload).encode()if payload is not None else None,headers=headers,method=method)
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 with opener.open(request,timeout=5)as response:
  data=response.read(MAX_BYTES+1)
  if len(data)>MAX_BYTES:raise RuntimeError('BrowserOS response too large')
  return response.status,dict(response.headers),data

def rpc_body(headers,raw,request_id):
 kind=next((v for k,v in headers.items()if k.lower()=='content-type'),'')
 if 'text/event-stream'in kind:
  candidates=[]
  for frame in raw.decode('utf-8').replace('\r\n','\n').split('\n\n'):
   data='\n'.join(line[5:].lstrip()for line in frame.splitlines()if line.startswith('data:'))
   if data:candidates.append(json.loads(data))
 else:candidates=[json.loads(raw)]
 for body in candidates:
  if isinstance(body,dict)and body.get('id')==request_id:
   if body.get('jsonrpc')!='2.0' or 'error'in body:raise RuntimeError('BrowserOS RPC failed')
   return body.get('result')
 raise RuntimeError('BrowserOS response did not match request')

class BrowserOSDiscovery:
 def __init__(self,url,transport=None):
  self.url=endpoint(url);self.transport=transport or http;self.session=None;self.counter=0;self.lock=threading.RLock();self.stopped=False;self.generation=0
 def headers(self):
  h={'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':PROTOCOL}
  if self.session:h['mcp-session-id']=self.session
  return h
 def request(self,method,params):
  if method not in ('initialize','tools/list'):raise ValueError('Browser actions are disabled in discovery')
  return self._rpc(method,params)
 def _rpc(self,method,params):
  with self.lock:
   if self.stopped:raise RuntimeError('BrowserOS discovery was stopped')
   self.counter+=1;n=self.counter;generation=self.generation;headers=self.headers()
  status,h,raw=self.transport('POST',self.url,headers,{'jsonrpc':'2.0','id':n,'method':method,'params':params})
  with self.lock:
   if self.stopped or generation!=self.generation:raise RuntimeError('BrowserOS request cancelled; result discarded')
   if status!=200:raise RuntimeError('BrowserOS endpoint rejected discovery')
   sid=next((v for k,v in h.items()if k.lower()=='mcp-session-id'),None)
   if sid:
    if not isinstance(sid,str)or len(sid)>200 or any(ord(c)<33 or ord(c)>126 for c in sid):raise RuntimeError('Invalid BrowserOS session identifier')
    if self.session and self.session!=sid:raise RuntimeError('BrowserOS session changed unexpectedly')
    self.session=sid
   return rpc_body(h,raw,n)
 def connect(self):
  result=self.request('initialize',{'protocolVersion':PROTOCOL,'capabilities':{},'clientInfo':{'name':'jarvis','version':'0.1'}})
  if not isinstance(result,dict)or result.get('protocolVersion')!=PROTOCOL:raise RuntimeError('BrowserOS did not negotiate structured-output protocol')
  if result.get('serverInfo',{}).get('name')!='browseros-neo':raise RuntimeError('Endpoint is not BrowserOS neo')
  if not self.session:raise RuntimeError('BrowserOS did not establish an isolated transport session')
  status,_,_=self.transport('POST',self.url,self.headers(),{'jsonrpc':'2.0','method':'notifications/initialized'})
  if status not in (200,202,204):raise RuntimeError('BrowserOS initialization failed')
  catalog=self.request('tools/list',{})
  if not isinstance(catalog,dict)or not isinstance(catalog.get('tools'),list):raise RuntimeError('BrowserOS tool discovery failed')
  # Tool instructions are untrusted data. Return names/schema only, do not execute.
  return {'server':result['serverInfo'],'tools':[{'name':t.get('name'),'inputSchema':t.get('inputSchema')}for t in catalog['tools']if isinstance(t,dict)],'browser_version_required':PINNED_BROWSER_VERSION,'actions_enabled':False}
 def stop(self):
  with self.lock:
   self.stopped=True;self.generation+=1;headers=self.headers();session=self.session
  if not session:return {'stopped':True,'session_closed':True}
  status,_,_=self.transport('DELETE',self.url,headers,None)
  if status not in (200,202,204):raise RuntimeError('BrowserOS session close is unverified')
  with self.lock:self.session=None
  return {'stopped':True,'session_closed':True}

class BrowserOSNavigation(BrowserOSDiscovery):
 """Only owned new blank tab, reviewed HTTPS navigation and snapshot. No general tool API."""
 def __init__(self,url,transport=None):super().__init__(url,transport);self.owned_page=None
 def _tool(self,name,args):
  result=self._rpc('tools/call',{'name':name,'arguments':args})
  if not isinstance(result,dict)or result.get('isError'):raise RuntimeError('BrowserOS operation failed; no success claimed')
  return result
 def _page_result(self,result,opening=False):
  data=result.get('structuredContent')
  if isinstance(data,dict):return data
  # Pinned neo intentionally strips structured fields for granular tools.
  # Decode only its exact first status block and matching snapshot marker,
  # never page text, tool instructions, or arbitrary trailing content.
  blocks=result.get('content',[])
  if not blocks or not isinstance(blocks[0],dict)or blocks[0].get('type')!='text':raise RuntimeError('BrowserOS result shape is unverified')
  first=blocks[0].get('text','')
  if opening:
   match=re.fullmatch(r'opened page ([1-9][0-9]{0,9})',first)
   if not match:raise RuntimeError('BrowserOS owned page receipt is unverified')
   page=int(match.group(1));url='about:blank'
  else:
   match=re.fullmatch(r'navigated \(url\) -> (https://[^\s]+)',first)
   if not match:raise RuntimeError('BrowserOS destination receipt is unverified')
   page=self.owned_page;url=match.group(1)
  marker='[Page '+str(page)+' snapshot]\n'
  snapshots=[b.get('text','')for b in blocks[1:]if isinstance(b,dict)and b.get('type')=='text'and isinstance(b.get('text'),str)and b['text'].startswith(marker)]
  if len(snapshots)!=1:raise RuntimeError('BrowserOS page snapshot receipt is unverified')
  origin=re.match(r'\[UNTRUSTED_PAGE_CONTENT nonce=[0-9a-f]+ origin=([^\s\]]+)\]',snapshots[0][len(marker):])
  if not origin or origin.group(1)!=url:raise RuntimeError('BrowserOS snapshot destination disagrees with receipt')
  return {'page':page,'url':url}
 def open_blank(self,confirmed=False):
  if confirmed is not True:raise ValueError('Review opening the BrowserOS tab first')
  if self.owned_page is not None:raise ValueError('An owned BrowserOS tab already exists')
  result=self._tool('tabs',{'action':'new','url':'about:blank'})
  data=self._page_result(result,True);page=data.get('page')
  if type(page)is not int or page<1:raise RuntimeError('BrowserOS did not return an owned page id')
  with self.lock:
   if self.stopped:raise RuntimeError('BrowserOS tab opening was cancelled')
   self.owned_page=page
  return {'page':page,'url':'about:blank','result':result}
 def navigate(self,url,confirmed=False):
  from .browser_control import BrowserControl
  url=BrowserControl.destination(url)
  if confirmed is not True:raise ValueError('Review exact BrowserOS destination first')
  if self.owned_page is None:raise RuntimeError('Open an isolated owned BrowserOS tab first')
  result=self._tool('navigate',{'page':self.owned_page,'action':'url','url':url})
  data=self._page_result(result)
  if data.get('page')!=self.owned_page or not isinstance(data.get('url'),str):raise RuntimeError('BrowserOS navigation result is unverified')
  return {'page':self.owned_page,'url':data['url'],'requested_url':url,'result':result}
 def snapshot(self):
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  return self._tool('snapshot',{'page':self.owned_page,'mode':'interactive'})
