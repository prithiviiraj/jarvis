"""Async desktop session. Owner review is required for every observed window/step plan."""
import threading
from .desktop_engine import DesktopEngine,WindowsAdapter
class DesktopController:
 def __init__(self,adapter=None):self.adapter=adapter;self.engine=DesktopEngine(adapter)if adapter else None;self.windows=[];self.worker=None;self.error='';self.status='Desktop input off'
 def ensure(self):
  if self.engine is None:self.adapter=WindowsAdapter();self.engine=DesktopEngine(self.adapter)
  return self.engine
 def discover(self,consent=False):
  if consent is not True:raise ValueError('Allow local window names first')
  engine=self.ensure();self.windows=self.adapter.windows();self.status='Observed local windows; no input';return self.windows
 def prepare(self,target,steps,scope):
  if target not in self.windows:raise ValueError('Select an observed window from the current list')
  self.error='';row=self.ensure().prepare(target,steps,scope);self.status='Review exact desktop task within120seconds; nothing executing';return row
 def run(self,reviewed,confirm=False,effect_approved=False):
  engine=self.ensure()
  if self.worker and self.worker.is_alive():raise ValueError('Current desktop task is still stopping/running')
  # Validate synchronously so a rejected plan does not appear submitted.
  if engine.state!='review'or not engine.pending or reviewed!=engine.pending or confirm is not True or effect_approved is not True:raise ValueError('Review exact desktop plan before execution')
  self.status='Running reviewed desktop input';self.error=''
  def work():
   try:engine.run(reviewed,confirm,effect_approved);self.status=engine.result
   except Exception as e:self.error=str(e)[:200];self.status='Desktop task stopped before next input'
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start();return self.worker
 def stop(self):
  if self.engine:self.engine.stop()
  self.status='Stopped. Submitted input is not undone.'
 def snapshot(self):return {'windows':self.windows,'task':self.engine.snapshot()if self.engine else {'state':'off','pending':None,'completed_steps':0,'result':''},'busy':bool(self.worker and self.worker.is_alive()),'status':self.status,'error':self.error,'scope':'Local selected-window input. No autonomous send/publish/pay/credentials; review every plan.'}
 def close(self):
  self.stop()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(timeout=2)
