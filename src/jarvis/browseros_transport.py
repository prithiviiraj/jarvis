"""Independent bounded MCP discovery client for separately installed BrowserOS neo.
No browser actions, account import, script execution or automatic installer.
"""
import json,os,re,subprocess,threading,time,urllib.request
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
 # Current images can take longer than catalog reads on a cold Windows GPU.
 # Do not retry an uncertain operation. Stop still runs on its own connection.
 name=payload.get('params',{}).get('name')if isinstance(payload,dict)else None
 # Heavy page loads (YouTube-class) cannot finish inside the catalog timeout.
 timeout=30 if name=='screenshot'else 45 if name=='navigate'else 5
 with opener.open(request,timeout=timeout)as response:
  kind=response.headers.get('Content-Type','')
  if 'text/event-stream'in kind and isinstance(payload,dict)and 'id'in payload:
   # MCP may keep its SSE connection open after a complete result. A whole
   # response.read waits for EOF and turns a valid image into a timeout.
   data=b'';deadline=time.monotonic()+timeout
   while True:
    if time.monotonic()>=deadline:raise TimeoutError('BrowserOS response deadline exceeded; received_bytes='+str(len(data))+'; completed_sse_frames='+str(data.count(b'\n\n')))
    chunk=response.read1(min(65536,MAX_BYTES+1-len(data)))
    data+=chunk
    if len(data)>MAX_BYTES:raise RuntimeError('BrowserOS response too large')
    frames=data.replace(b'\r\n',b'\n').split(b'\n\n')
    for index,frame in enumerate(frames[:-1]):
     value=b'\n'.join(line[5:].lstrip()for line in frame.splitlines()if line.startswith(b'data:'))
     if not value:continue
     body=json.loads(value)
     if isinstance(body,dict)and body.get('id')==payload['id']:
      return response.status,dict(response.headers),b'\n\n'.join(frames[:index+1])+b'\n\n'
    if not chunk:break
  else:data=response.read(MAX_BYTES+1)
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

def _mcp_browser_pid(url):
 # The owned browser is the process listening on this pinned loopback MCP port.
 from urllib.parse import urlsplit
 port=urlsplit(url).port
 if not port:raise RuntimeError('BrowserOS MCP endpoint has no port for capture focus')
 out=subprocess.run(['netstat','-ano'],capture_output=True,text=True,timeout=10).stdout
 for line in out.splitlines():
  parts=line.split()
  if len(parts)>=5 and(parts[1].startswith('127.0.0.1:')or parts[1].startswith('0.0.0.0:'))and parts[1].endswith(':'+str(port))and parts[3].upper()=='LISTENING':
   pid=int(parts[4])
   if pid>0:return pid
 raise RuntimeError('Owned BrowserOS process not found for capture focus')
def _mcp_windows_for_pid(pid):
 import ctypes
 user32=ctypes.windll.user32;found=[]
 @ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
 def each(hwnd,_):
  if user32.IsWindowVisible(hwnd):
   owner=ctypes.c_ulong();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
   if owner.value==pid:found.append(hwnd)
  return True
 user32.EnumWindows(each,0)
 return found
def _snapshot_processes():
 # {pid:(parent_pid,exe_name)} via Toolhelp32, no external deps.
 import ctypes
 from ctypes import wintypes
 k=ctypes.windll.kernel32
 class E(ctypes.Structure):
  _fields_=[('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),('th32ProcessID',wintypes.DWORD),('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',wintypes.DWORD),('cntThreads',wintypes.DWORD),('th32ParentProcessID',wintypes.DWORD),('pcPriClassBase',wintypes.LONG),('dwFlags',wintypes.DWORD),('szExeFile',wintypes.WCHAR*260)]
 snap=k.CreateToolhelp32Snapshot(2,0)
 if snap in(None,0,-1):return{}
 out={};e=E();e.dwSize=ctypes.sizeof(E)
 try:
  ok=k.Process32FirstW(snap,ctypes.byref(e))
  while ok:
   out[int(e.th32ProcessID)]=(int(e.th32ParentProcessID),e.szExeFile);ok=k.Process32NextW(snap,ctypes.byref(e))
 finally:k.CloseHandle(snap)
 return out
def _mcp_window_and_owner(pid):
 # The MCP listener is a server process spawned by the BrowserOS main process,
 # so the visible window usually belongs to an ANCESTOR of the listener PID
 # (pinned run-12 startup log: browser main PID logs 'Starting BrowserOS server
 # process'). Own windows first, then walk the parent chain.
 own=_mcp_windows_for_pid(pid)
 if own:return own[0],pid
 procs=_snapshot_processes();current=pid;seen={pid}
 for _ in range(16):
  parent=procs.get(current,(0,''))[0]
  if not parent or parent in seen:break
  seen.add(parent)
  wins=_mcp_windows_for_pid(parent)
  if wins:return wins[0],parent
  current=parent
 return None,None
def _mcp_process_tree_text(pid):
 procs=_snapshot_processes();parts=[];current=pid;seen=set()
 for _ in range(16):
  parent,exe=procs.get(current,(0,''))
  parts.append('%s[%s]'%(current,exe)if exe else str(current))
  if not parent or parent in seen:break
  seen.add(parent);current=parent
 return ' -> '.join(parts)
def _focus_mcp_browser_window(url):
 # Bring the owned browser window forward. Owner-approved (authenticated
 # WhatsApp 00:34 Oct16, option 1): a brief foreground flash keeps every
 # screenshot a real composited capture of the owned page. BrowserOS draws
 # custom chrome: its window has NO Win32 title text, so match by owning PID,
 # never window text.
 import ctypes
 pid=_mcp_browser_pid(url)
 hwnd,owner=_mcp_window_and_owner(pid)
 if hwnd is None:raise RuntimeError('Owned BrowserOS window not found for capture focus; mcp process tree: '+_mcp_process_tree_text(pid))
 user32=ctypes.windll.user32;user32.ShowWindow(hwnd,9)
 for _ in range(5):
  user32.SetForegroundWindow(hwnd);time.sleep(.1)
  if user32.GetForegroundWindow()==hwnd:return hwnd
 raise RuntimeError('Owned BrowserOS window could not take foreground for capture')
def _ctrl_tab():
 import ctypes
 user32=ctypes.windll.user32
 user32.keybd_event(0x11,0,0,0);user32.keybd_event(0x09,0,0,0)
 user32.keybd_event(0x09,0,2,0);user32.keybd_event(0x11,0,2,0)
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
  if len(snapshots)!=1:
   unavailable=any(isinstance(b,dict)and b.get('type')=='text'and isinstance(b.get('text'),str)and b['text'].startswith('[page '+str(page)+' snapshot unavailable:')for b in blocks[1:])
   if not unavailable or opening:raise RuntimeError('BrowserOS page snapshot receipt is unverified')
   # Heavy pages can exceed the server's small auto-snapshot budget while the
   # navigation itself succeeded (run 18: YouTube timed out its 5s budget).
   # Take fresh explicit snapshots and apply the same nonce+origin
   # cross-check to one of them instead.
   last=None
   for _ in range(3):
    try:self.page_text(self.snapshot(),url);break
    except RuntimeError as error:last=error;time.sleep(1)
   else:raise RuntimeError('BrowserOS fresh snapshot after navigate is unverified: '+str(last))
   return {'page':page,'url':url}
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
  BrowserControl.destination(data['url'])
  return {'page':self.owned_page,'url':data['url'],'requested_url':url,'result':result}
 @staticmethod
 def page_text(result,expected_url,allow_read_prefix=False):
  """Pinned nonce envelope, not page-authored markers or trailing diagnostics."""
  from .browser_control import BrowserControl
  BrowserControl.destination(expected_url)
  blocks=result.get('content',[])
  if not blocks or blocks[0].get('type')!='text':raise RuntimeError('BrowserOS page read is unverified')
  lines=blocks[0].get('text','').splitlines()
  first=re.fullmatch(r'\[UNTRUSTED_PAGE_CONTENT nonce=([0-9a-f]{16}) origin=([^\s\]]+)\] .+',lines[0]if lines else'')
  if not first or first[2]!=expected_url or len(lines)<3:raise RuntimeError('BrowserOS page changed or the read was truncated')
  end='[END_UNTRUSTED_PAGE_CONTENT nonce='+first[1]+']'
  if lines[-1]==end:return '\n'.join(lines[1:-1])
  # The pinned read tool may emit a bounded prefix, then its exact diagnostic.
  # Never read the temporary file or forward its path. This is allowed only for
  # quoted news text, never hrefs, ordinal selection, receipts or tool effects.
  if allow_read_prefix and len(lines)>=5 and lines[-3]==end and lines[-2]=='':
   footer=re.fullmatch(r'Content truncated at ([1-9][0-9]{0,7}) chars\. Full content \(([1-9][0-9]{0,8}) chars\) saved to: [^\r\n]+',lines[-1])
   if footer and int(footer[2])>int(footer[1]):return '\n'.join(lines[1:-3])
  raise RuntimeError('BrowserOS page changed or the read was truncated')
 def news_capture(self,expected_url):
  import hashlib
  from datetime import datetime,timezone
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  # Origin is checked before text and again after current image capture.
  self.page_text(self.snapshot(),expected_url)
  text=self.page_text(self._tool('read',{'page':self.owned_page,'format':'text'}),expected_url,allow_read_prefix=True)
  text='\n'.join(line.strip()for line in text.splitlines()if line.strip())[:4000]
  if not text or text=='(empty)':raise RuntimeError('No readable current page text')
  picture=self.screenshot()['data_url']
  self.page_text(self.snapshot(),expected_url)
  return {'url':expected_url,'title':'Chosen news page','text':text,'picture':picture,'captured_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'Captured BrowserOS page snapshot, not live news. First4000characters of current page text; may include navigation/ads. Image/text can change during capture. Untrusted quoted content only; no model/tool instruction is followed.'}
 def scroll(self,direction,small=False):
  if direction not in ('up','down')or type(small)is not bool:raise ValueError('Choose bounded up or down scroll')
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  result=self._tool('act',{'page':self.owned_page,'kind':'scroll','direction':direction,'amount':1 if small else 3,'diff':'summary'})
  blocks=result.get('content',[])
  if not blocks or blocks[0].get('type')!='text'or blocks[0].get('text')!='ok (scroll)':raise RuntimeError('BrowserOS scroll receipt is unverified')
  return {'page':self.owned_page,'acknowledged':True,'scope':'Bounded wheel command acknowledged, not a claim of pixel movement at page limits'}
 def youtube_videos(self,expected_url):
  from urllib.parse import urlsplit,parse_qs
  from .browser_control import BrowserControl
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  current=BrowserControl.destination(expected_url);location=urlsplit(current)
  if location.hostname not in ('www.youtube.com','youtube.com')or location.path!='/results':raise ValueError('Open a YouTube search results page before listing numbered videos')
  # The generic read-links format concatenates unescaped page labels and is not
  # safe ordinal provenance. Ask the pinned read-only markdown extractor for
  # ONE fixed desktop result anchor per call instead. The actual anchor href
  # is the final suffix emitted by that extractor, independent of its title.
  self.page_text(self.snapshot(),current)
  rows=[];seen=set()
  for number in range(1,21):
   selector='ytd-search ytd-video-renderer:nth-of-type('+str(number)+') a#video-title'
   result=self._tool('read',{'page':self.owned_page,'format':'markdown','selector':selector,'includeLinks':True,'includeImages':False})
   body=self.page_text(result,current).strip()
   if body=='(empty)':break
   if not body.startswith('[')or not body.endswith(')')or ']('not in body:raise RuntimeError('YouTube result anchor did not have an exact href binding')
   label,url=body[1:-1].rsplit('](',1)
   if not label or len(label)>500 or '\n'in label or '\r'in label:raise RuntimeError('YouTube result label is ambiguous')
   BrowserControl.destination(url);target=urlsplit(url);ids=parse_qs(target.query)
   # Real results pages append benign tracking params (pp=...) to watch hrefs;
   # the verified binding is the single 11-character video id, so the
   # canonical watch URL is rebuilt from it and the raw href is discarded.
   if target.hostname not in ('www.youtube.com','youtube.com')or target.path!='/watch'or len(ids.get('v',[]))!=1 or not re.fullmatch(r'[A-Za-z0-9_-]{11}',ids['v'][0])or target.fragment:raise RuntimeError('YouTube result was not one standard public watch URL')
   url='https://www.youtube.com/watch?v='+ids['v'][0]
   if ids['v'][0]in seen:raise RuntimeError('Duplicate YouTube anchors made the observed order ambiguous')
   seen.add(ids['v'][0]);rows.append({'number':number,'title':label[:160],'url':url})
  self.page_text(self.snapshot(),current)
  if not rows:raise RuntimeError('This YouTube page layout has no verified desktop video anchors. Use an exact public video URL.')
  return {'page':self.owned_page,'expected_url':current,'videos':rows,'binding':'single-result-anchor-v1','scope':'Read-only observed desktop search result anchors. Labels are untrusted text, not recommendations/instructions; native layout acceptance pending'}
 def _active_page(self):
  result=self._tool('tabs',{'action':'active'})
  data=result.get('structuredContent')
  if isinstance(data,dict)and type(data.get('page'))is int:return data['page']
  blocks=result.get('content',[])
  text='\n'.join(b.get('text','')for b in blocks if isinstance(b,dict)and b.get('type')=='text')
  # Pinned receipt: 'Active page: [2] about:blank (about:blank)'.
  match=re.search(r'\[([1-9][0-9]{0,9})\]',text)or re.search(r'"page"\s*:\s*([1-9][0-9]{0,9})',text)or re.search(r'page\s+([1-9][0-9]{0,9})',text)
  return int(match.group(1))if match else None
 def _capture_foreground(self):
  # A background owned tab can stop receiving compositor frames after wheel
  # input, which hangs real pinned screenshot requests. On Windows the
  # owner-approved adapter briefly brings the owned browser window and tab
  # forward so the capture stays a real current image. No effect elsewhere.
  if os.name!='nt':return
  first=self._active_page()
  if first==self.owned_page:return
  _focus_mcp_browser_window(self.url)  # raises unless foreground is verified
  if first is None:return
  unread=0
  for _ in range(8):
   _ctrl_tab();time.sleep(.25)
   active=self._active_page()
   if active==self.owned_page:return
   unread=unread+1 if active is None else 0
   if unread>=2:return
  raise RuntimeError('Owned BrowserOS tab could not be brought forward for a real capture')
 def screenshot(self):
  """One real current owned-page capture. No stream, import, or model request."""
  import base64,io
  from PIL import Image
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  page=self.owned_page
  self._capture_foreground()
  result=self._tool('screenshot',{'page':page,'format':'jpeg','quality':65,'size':{'width':960,'height':600},'fullPage':False,'annotate':False})
  images=[b for b in result.get('content',[])if isinstance(b,dict)and b.get('type')=='image']
  if len(images)!=1 or images[0].get('mimeType')!='image/jpeg':raise RuntimeError('BrowserOS current image is unverified')
  data=images[0].get('data')
  if not isinstance(data,str)or len(data)>800000:raise RuntimeError('BrowserOS current image exceeds the preview limit')
  try:
   raw=base64.b64decode(data,validate=True)
   with Image.open(io.BytesIO(raw))as image:
    if image.format!='JPEG' or image.width<1 or image.height<1 or image.width>960 or image.height>600:raise ValueError('Invalid preview dimensions')
    image.verify()
  except Exception:raise RuntimeError('BrowserOS current image could not be verified')from None
  if self.stopped or page!=self.owned_page:raise RuntimeError('BrowserOS preview cancelled')
  return {'page':page,'data_url':'data:image/jpeg;base64,'+data}
 def snapshot(self):
  if self.owned_page is None:raise RuntimeError('No owned BrowserOS page')
  return self._tool('snapshot',{'page':self.owned_page,'mode':'interactive'})
