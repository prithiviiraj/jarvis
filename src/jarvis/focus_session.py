"""Session-only local focus timer. No app/camera monitoring, model or speech starts."""
import hashlib,json,threading,time
class FocusSession:
 def __init__(self,clock=time.monotonic):self.clock=clock;self.lock=threading.RLock();self.pending=None;self.goal='';self.duration=0;self.started=None;self.elapsed=0;self.state='off';self.history=[];self.cancelled=False
 def prepare(self,goal,minutes):
  if not isinstance(goal,str)or not 1<=len(goal.strip())<=300 or any(ord(c)<32 for c in goal):raise ValueError('Choose one plain focus goal up to300characters')
  if type(minutes)is not int or not 5<=minutes<=120:raise ValueError('Choose5to120minutes')
  with self.lock:
   self.update()
   if self.state in ('running','paused'):raise ValueError('Stop or finish the current focus session first')
   payload={'goal':goal.strip(),'minutes':minutes,'scope':'Local timer and visible check-in only. No sensors, API/model request, speech, notifications, app control or background persistence.'}
   self.pending={'payload':payload,'sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()};self.state='review';return json.loads(json.dumps(self.pending))
 def start(self,reviewed,confirm=False):
  with self.lock:
   if confirm is not True or not self.pending or reviewed!=self.pending or self.state!='review':raise ValueError('Review exact focus goal and duration')
   p=self.pending['payload'];self.goal=p['goal'];self.duration=p['minutes']*60;self.started=self.clock();self.elapsed=0;self.pending=None;self.state='running';self.cancelled=False
 def update(self):
  if self.state=='running'and self.started is not None and self.elapsed+self.clock()-self.started>=self.duration:self.elapsed=self.duration;self.started=None;self.state='check-in'
 def pause(self):
  with self.lock:
   self.update()
   if self.state!='running':raise ValueError('No running focus session')
   self.elapsed+=self.clock()-self.started;self.started=None;self.state='paused'
 def resume(self,confirm=False):
  with self.lock:
   if self.state!='paused'or confirm is not True:raise ValueError('Choose resume current goal')
   self.started=self.clock();self.state='running'
 def finish(self,done=False):
  with self.lock:
   self.update()
   if self.state not in ('running','paused','check-in'):raise ValueError('No focus session to finish')
   if type(done)is not bool:raise ValueError('Choose whether goal was done')
   self.history.append({'goal':self.goal,'minutes':self.duration//60,'done':done});self.history=self.history[-10:];self.started=None;self.elapsed=0;self.goal='';self.state='off'
 def stop(self):
  with self.lock:self.pending=None;self.started=None;self.elapsed=0;self.goal='';self.duration=0;self.state='off';self.cancelled=True
 def snapshot(self):
  with self.lock:
   self.update();elapsed=self.elapsed+(max(0,self.clock()-self.started)if self.started is not None else 0);remaining=max(0,int(self.duration-elapsed))
   return {'state':self.state,'pending':self.pending,'goal':self.goal,'remaining_seconds':remaining,'minutes':self.duration//60,'history':list(self.history),'message':'Focus block finished. Did you finish '+self.goal+'?'if self.state=='check-in'else'Focus paused'if self.state=='paused'else'Timer running; no automatic monitoring or speech'if self.state=='running'else'Focus off','scope':'Session-only monotonic timer. Goal is owner text, not observed productivity. Closing/Stop clears session; no accountability claim from sensors.'}
