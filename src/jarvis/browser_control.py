"""Deterministic local browser voice commands. Page text never becomes instructions.
Navigation uses an isolated automation profile. No send/pay/delete/type automation.
"""
from urllib.parse import urlsplit,urlencode
import ipaddress
class BrowserControl:
 def __init__(self,page):self.page=page
 @staticmethod
 def destination(url):
  if not isinstance(url,str)or len(url)>2048:raise ValueError('Invalid browser destination')
  try:
   p=urlsplit(url);port=p.port
   if p.scheme!='https'or not p.hostname or p.username or p.password or port not in (None,443):raise ValueError()
   host=p.hostname.lower()
   if host in ('localhost','localhost.localdomain')or host.endswith(('.local','.internal','.localhost'))or '.'not in host:raise ValueError()
   try:
    ip=ipaddress.ip_address(host)
    if not ip.is_global:raise ValueError()
   except ValueError:
    if ':'in host or all(x.isdigit()or x=='.'for x in host):raise ValueError()
   return url
  except ValueError:raise ValueError('Use a public HTTPS site, not local or private addresses')
 def execute(self,command,value='',confirmed=False):
  if command=='search':
   if not isinstance(value,str)or not value.strip()or len(value)>300:raise ValueError('Enter a short search')
   # Search terms leave the machine; review exact text before navigation.
   if confirmed is not True:raise ValueError('Review search terms before opening browser')
   self.page.goto('https://www.google.com/search?'+urlencode({'q':value}),wait_until='domcontentloaded',timeout=15000)
  elif command=='open':
   url=self.destination(value)
   if confirmed is not True:raise ValueError('Review exact destination first')
   self.page.goto(url,wait_until='domcontentloaded',timeout=15000)
  elif command in ('scroll-down','scroll-up'):
   self.page.mouse.wheel(0,600 if command=='scroll-down'else-600)
  else:raise ValueError('Available: open site, search web, scroll up/down. Sending, buying and form submission are not enabled.')
  return {'url':self.page.url,'title':self.page.title()[:160]}

def parse_voice(text):
 import re
 if not isinstance(text,str):return None
 text=re.sub(r'^\s*(?:hey\s+)?(?:jarvis|nova|kai|lyra|dex)[, ]*','',text,flags=re.I).strip()
 if text.lower().rstrip('.!')=='browser read links':return {'command':'read-links','value':''}
 match=re.fullmatch(r'browser (?:choose|select) link ([1-9]|1[0-9]|20)[.!]?',text,re.I)
 if match:return {'command':'select-link','value':match.group(1)}
 for phrase,command in [('browser scroll down','scroll-down'),('browser scroll up','scroll-up')]:
  if text.lower().rstrip('.!')==phrase:return {'command':command,'value':''}
 if text.lower().startswith('browser youtube search for '):
  query=text[len('browser youtube search for '):].strip()
  if not query or len(query)>200:raise ValueError('Enter a short YouTube search')
  return {'command':'open','value':'https://www.youtube.com/results?'+urlencode({'search_query':query})}
 for prefix,command in [('browser search for ','search'),('browser open ','open')]:
  if text.lower().startswith(prefix):
   value=text[len(prefix):].strip()
   if command=='open':
    value=value.rstrip(' .!')
    if not value.startswith('https://'):value='https://'+value
    BrowserControl.destination(value)
   elif not value or len(value)>300:raise ValueError('Enter a short browser search')
   return {'command':command,'value':value}
 return None

class BrowserSession:
 """All Playwright operations occur on one worker. Owner's ordinary profile untouched."""
 def __init__(self,root):
  import threading,queue
  self.root=str(root);self.jobs=queue.Queue(maxsize=3);self.lock=threading.RLock();self.state={'state':'off','url':'','title':'','error':'','links':[]};self.cancel=threading.Event()
  self.thread=threading.Thread(target=self.run,daemon=False);self.thread.start()
 def snapshot(self):
  with self.lock:return dict(self.state)
 def submit(self,command,value='',confirmed=False,expected_url=None):
  if self.cancel.is_set():raise ValueError('Browser stopping; wait until closed before starting another session')
  if confirmed is not True:raise ValueError('Review browser command first')
  self.jobs.put_nowait((command,value,expected_url))
  with self.lock:self.state['state']='working';self.state['error']=''
 def close(self):
  self.cancel.set()
  with self.lock:self.state['state']='stopping'
  return self.thread
 def run(self):
  import queue
  context=None;p=None
  try:
   while not self.cancel.is_set():
    try:command,value,expected_url=self.jobs.get(timeout=.2)
    except queue.Empty:continue
    try:
     if context is None:
      from playwright.sync_api import sync_playwright
      p=sync_playwright().start()
      context=p.chromium.launch_persistent_context(self.root,channel='msedge',headless=False,accept_downloads=False,service_workers='block')
      context.route('**/*',self.route)
     page=context.pages[0]if context.pages else context.new_page()
     if expected_url is not None:
      if page.url!=expected_url:raise ValueError('Browser page changed; read links again')
      from .browser_links import links
      fresh=links(page)
      if value not in {r['url']for r in fresh['links']}:raise ValueError('Selected link changed; read links again')
     if command=='read-links':
      from .browser_links import links
      snapshot=links(page);result={'url':page.url,'title':page.title()[:160],'links':snapshot['links']}
     else:
      result=BrowserControl(page).execute(command,value,confirmed=True)
      result['links']=[]
     with self.lock:self.state.update(state='ready',error='',**result)
    except Exception:
     with self.lock:self.state.update(state='error',error='Browser control failed. Microsoft Edge and bundled automation runtime are required. No task completion is claimed.')
  finally:
   if context:
    try:context.close()
    except Exception:pass
   if p:p.stop()
   with self.lock:self.state['state']='off'
 @staticmethod
 def route(route):
  # No non-read requests. Check every network destination incl redirects/resources.
  try:
   BrowserControl.destination(route.request.url)
   import socket
   host=urlsplit(route.request.url).hostname
   addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
   if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):raise ValueError()
   if route.request.method not in ('GET','HEAD'):raise ValueError()
   route.continue_()
  except (ValueError,OSError):route.abort()
