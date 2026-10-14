"""Explicit session-only BrowserOS adapter. No installer, account import or autonomous agent."""
import threading
from .browseros_transport import BrowserOSNavigation,endpoint,PINNED_BROWSER_VERSION
class BrowserOSController:
 def __init__(self,factory=None):
  self.factory=factory or BrowserOSNavigation;self.lock=threading.RLock();self.generation=0;self.client=None;self.pending=None;self.busy=False;self.state='off';self.error='';self.url='';self.catalog=[]
 def snapshot(self):
  with self.lock:return {'state':self.state,'busy':self.busy,'error':self.error,'url':self.url,'pending':dict(self.pending)if self.pending else None,'version_required':PINNED_BROWSER_VERSION,'tools':list(self.catalog),'scope':'Separate BrowserOS neo. Reviewed owned-tab navigation only. No typing, scripts, account import, sending, payments, downloads or files. Telemetry must be off. Stop ends this MCP session, not unrelated browser tabs.'}
 def _work(self,fn):
  with self.lock:
   if self.busy:raise ValueError('BrowserOS operation is busy')
   self.busy=True;ticket=self.generation;self.error=''
  def run():
   try:
    result=fn()
    with self.lock:
     if ticket!=self.generation:return
     if isinstance(result,dict)and 'url'in result:self.url=result['url']
     self.state='connected'
   except Exception as e:
    with self.lock:
     if ticket==self.generation:self.state='error';self.error=str(e)[:300]
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
  return self._work(lambda:client.open_blank(True)if review['action']=='open-window'else client.navigate(review['value'],True))
 def stop(self):
  with self.lock:
   self.generation+=1;ticket=self.generation;client=self.client;self.pending=None;self.busy=False;self.state='stopping';self.catalog=[]
  def close():
   try:
    if client:client.stop()
    with self.lock:
     if ticket==self.generation:self.state='off';self.url='';self.client=None
   except Exception as e:
    with self.lock:
     if ticket==self.generation:self.state='stop-unverified';self.error=str(e)[:300]
  t=threading.Thread(target=close,daemon=True);t.start();return t
