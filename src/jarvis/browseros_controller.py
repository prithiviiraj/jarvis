"""Explicit session-only BrowserOS adapter. No installer, account import or autonomous agent."""
import threading
from collections import deque
from .browseros_transport import BrowserOSNavigation,endpoint,PINNED_BROWSER_VERSION
class BrowserOSController:
 def __init__(self,factory=None,history_path=None):
  from .browser_visits import BrowserVisits
  self.visits=BrowserVisits(history_path);self.history_filter=False;self.show_history=False;self.news=None;self.news_error=''
  self.factory=factory or BrowserOSNavigation;self.lock=threading.RLock();self.generation=0;self.client=None;self.pending=None;self.busy=False;self.state='off';self.error='';self.url='';self.requested_url='';self.catalog=[];self.events=deque(maxlen=30);self.operation=0;self.preview=None;self.preview_error='';self.videos=[];self.videos_selectable=False
 def snapshot(self):
  with self.lock:return {'news':dict(self.news)if self.news else None,'news_error':self.news_error,'videos_selectable':self.videos_selectable,'history_visible':self.show_history,'recent':self.visits.list(self.history_filter),'history_error':self.visits.error,'history_scope':'Yesterday in India time; up to20pages completed by this JARVIS BrowserOS adapter, not private browser history'if self.history_filter else'Up to20recent pages from100saved JARVIS-only destinations. Stored locally. No private browser history imported.','videos':[dict(v)for v in self.videos],'preview':dict(self.preview)if self.preview else None,'preview_error':self.preview_error,'requested_url':self.requested_url,'state':self.state,'busy':self.busy,'error':self.error,'url':self.url,'pending':dict(self.pending)if self.pending else None,'version_required':PINNED_BROWSER_VERSION,'tools':list(self.catalog),'scope':'Separate BrowserOS neo. Owned-tab navigation, manual current-page screenshots only. No typing, scripts, account import, sending, payments, downloads or files. Telemetry must be off. Stop ends this MCP session, not unrelated browser tabs.'}
 def drain_events(self):
  with self.lock:events=list(self.events);self.events.clear();return events
 def _work(self,fn,completion=None):
  with self.lock:
   if self.busy:raise ValueError('BrowserOS operation is busy')
   self.busy=True;ticket=self.generation;self.error='';self.operation+=1;operation=str(ticket)+':'+str(self.operation);capture_client=self.client
  def run():
   try:
    result=fn()
    image=None;image_error=''
    with self.lock:
     if ticket!=self.generation:return
    if completion and completion!='browser-failed':
     try:image=capture_client.screenshot()
     except Exception as e:image_error='Current page preview unavailable: '+str(e)[:180]
    with self.lock:
     if ticket==self.generation and completion:
      self.preview=dict(image,captured_at=__import__('time').time())if isinstance(image,dict)and isinstance(image.get('data_url'),str)else None
      self.preview_error=image_error
    with self.lock:
     if ticket!=self.generation:return
     if isinstance(result,dict)and 'url'in result:self.news=None;self.news_error='';self.url=result['url'];self.requested_url=result.get('requested_url','');self.videos=[];self.videos_selectable=False;self.visits.record(self.url)
     self.state='connected'
     if completion:self.events.append({'id':'browseros:'+operation,'kind':completion,'verified':True})
   except Exception as e:
    with self.lock:
     if ticket==self.generation:
      self.state='error';self.error=str(e)[:300]
      if completion:self.events.append({'id':'browseros:'+operation,'kind':'browser-failed','verified':True})
   finally:
    with self.lock:
     if ticket==self.generation:self.busy=False
  t=threading.Thread(target=run,daemon=True);t.start();return t
 def connect(self,value,consent=False,telemetry_off=False):
  value=endpoint(value)
  if consent is not True or telemetry_off is not True:raise ValueError('Review separate BrowserOS connection and verify telemetry is off first')
  with self.lock:
   if self.client is not None or self.state in ('stopping','stop-unverified'):raise ValueError('Verify the previous BrowserOS session stopped before reconnecting')
   self.client=self.factory(value);client=self.client;self.state='connecting'
  def check():
   result=client.connect()
   with self.lock:
    if client is self.client and self.state!='stopping':self.catalog=[t['name']for t in result['tools']if isinstance(t.get('name'),str)]
   return result
  return self._work(check)
 def capture_news(self,expected_url):
  with self.lock:
   if self.busy or self.state!='connected' or expected_url!=self.url:raise ValueError('Wait for the chosen BrowserOS news page first')
   client=self.client;ticket=self.generation;self.news=None;self.news_error=''
  def capture():
   try:row=client.news_capture(expected_url)
   except Exception as error:
    with self.lock:
     if ticket==self.generation:self.news_error=str(error)[:200]
    raise
   from .news_page import validate
   validate(row)
   if not isinstance(row.get('picture'),str)or not row['picture'].startswith('data:image/jpeg;base64,'):raise ValueError('News page image is unverified')
   with self.lock:
    if ticket==self.generation and self.url==expected_url:self.news=dict(row);self.preview={'page':getattr(client,'owned_page',None),'data_url':row['picture'],'captured_at':__import__('time').time()}
   return {}
  return self._work(capture)
 def scroll(self,direction,small=False):
  with self.lock:
   if self.busy or self.state!='connected' or not self.url:raise ValueError('Start BrowserOS and wait for a page first')
   client=self.client
   return self._work(lambda:client.scroll(direction,small),completion='browser-scroll-ready')
 def read_videos(self):
  with self.lock:
   if self.busy or self.state!='connected' or not self.url:raise ValueError('Open YouTube and wait for its page first')
   client=self.client;url=self.url;ticket=self.generation;self.videos=[];self.videos_selectable=False
  def read():
   result=client.youtube_videos(url)
   with self.lock:
    if ticket==self.generation and self.url==url:self.videos=result['videos'];self.videos_selectable=result.get('binding')=='single-result-anchor-v1'
   return {}
  return self._work(read)
 def choose_video(self,number,reviewed_url):
  with self.lock:
   if type(number)is not int or not 1<=number<=len(self.videos)or reviewed_url!=self.url:raise ValueError('Choose a current observed video number')
   if not self.videos_selectable:raise ValueError('Numbered video opening is not ready: current link labels lack verified href bindings. Use an exact public video URL instead.')
   row=self.videos[number-1];client=self.client;current=self.url
   def verify_and_open():
    observed=client.youtube_videos(current)
    if observed.get('binding')!='single-result-anchor-v1':raise ValueError('Current video href bindings are unavailable')
    fresh=observed['videos']
    if number>len(fresh)or fresh[number-1]!=row:raise ValueError('YouTube choices changed. Refresh the list and choose again.')
    return client.navigate(row['url'],True)
   return self._work(verify_and_open,completion='browser-page-ready')
 def refresh_preview(self):
  with self.lock:
   if self.busy or self.state!='connected' or not self.url:raise ValueError('Start BrowserOS and wait for a page first')
   client=self.client;ticket=self.generation
  def capture():
   image=client.screenshot()
   with self.lock:
    if ticket==self.generation:self.preview=dict(image,captured_at=__import__('time').time());self.preview_error=''
   return {}
  return self._work(capture)
 def start(self):
  """The named Start control opens exactly one blank owned tab immediately."""
  with self.lock:
   if self.busy or self.state!='connected' or self.client is None:raise ValueError('Connect BrowserOS and wait for discovery first')
   client=self.client
   if self.url:raise ValueError('BrowserOS already has an owned tab. Use its destination control or Stop.')
   self.pending=None
   return self._work(lambda:client.open_blank(True),completion='browser-tab-ready')
 def navigate(self,url):
  # The owner supplies the exact public URL and clicks Open this destination.
  with self.lock:
   from .browser_control import BrowserControl
   url=BrowserControl.destination(url)
   if self.busy or self.state!='connected' or self.client is None:raise ValueError('Connect BrowserOS and wait for discovery first')
   client=self.client;needs_tab=not self.url;self.pending=None
   def open_exact():
    if needs_tab:client.open_blank(True)
    return client.navigate(url,True)
   return self._work(open_exact,completion='browser-page-ready')
 def prepare(self,action,value=''):
  with self.lock:
   if self.busy or self.state!='connected' or self.client is None:raise ValueError('Connect BrowserOS and wait for discovery first')
   if action=='open':
    from .browser_control import BrowserControl
    value=BrowserControl.destination(value)
   elif action=='open-window':value=''
   else:raise ValueError('BrowserOS supports reviewed open-window and exact public HTTPS navigation only')
   self.pending={'action':action,'value':value,'generation':self.generation,'expected_url':self.url,'scope':'Owned BrowserOS tab only. No forms, credentials, sending, payment or script.'}
   return dict(self.pending)
 def run(self,reviewed,confirm=False):
  with self.lock:
   if confirm is not True or not self.pending or reviewed!=self.pending:raise ValueError('Review the exact current BrowserOS action first')
   review=dict(self.pending);self.pending=None;client=self.client
  return self._work(lambda:client.open_blank(True)if review['action']=='open-window'else client.navigate(review['value'],True),completion='browser-tab-ready'if review['action']=='open-window'else'browser-page-ready')
 def stop(self):
  with self.lock:
   self.generation+=1;ticket=self.generation;client=self.client;self.pending=None;self.busy=False;self.state='stopping';self.catalog=[];self.events.clear();self.news=None;self.news_error='';self.preview=None;self.preview_error='';self.videos=[];self.videos_selectable=False
  def close():
   try:
    if client:client.stop()
    with self.lock:
     if ticket==self.generation:self.state='off';self.url='';self.requested_url='';self.client=None
   except Exception as e:
    with self.lock:
     if ticket==self.generation:self.state='stop-unverified';self.error=str(e)[:300]
  t=threading.Thread(target=close,daemon=True);t.start();return t
