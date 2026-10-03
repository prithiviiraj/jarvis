"""Narrow local stdio bridge for modern UI. No arbitrary shell/files/URLs or cloud routes."""
import sys,json,time,queue,threading
from .workspace_voice import WorkspaceVoice,build_text_router,build_proactive_speaker,VOICES
from .local_awareness import LocalContext,CameraWorker,foreground_app
from .proactive import ProactiveJudge
class Bridge:
 def __init__(self,voice=None):
  self.voice=voice or WorkspaceVoice();self.context=LocalContext();self.camera=CameraWorker(self.context)
  self.judge=ProactiveJudge(self.context,build_text_router,self.voice.notify,build_proactive_speaker)
  self.titles=False;self.last_app=0;self.closed=False;self.messages=[];self.status='off';self.lock=threading.RLock()
 def poll(self):
  if self.context.apps and time.monotonic()-self.last_app>=1:
   self.last_app=time.monotonic()
   try:self.context.app_event(foreground_app(self.titles))
   except Exception:self.context.app_event(None)
  busy=self.voice.busy or self.voice.runtime is not None;self.judge.conversation_busy=busy
  if busy and self.judge.busy:self.judge.stop()
  self.judge.poll(busy)
 def stop(self):
  self.judge.stop();self.camera.stop();self.context.clear();self.titles=False;self.voice.pause();self.voice.memory.clear();self.messages=[];self.status='off'
  if not self.camera.stopped():self.context.camera_state('stopping')
 def execute(self,request):
  if not isinstance(request,dict):raise ValueError('Invalid command')
  cmd=request.get('command');allowed={'status','chat','select','pause','close'} # Sensor commands await visible native controls/indicator migration.
  if cmd not in allowed:raise ValueError('Unknown command')
  if cmd=='chat':
   text=request.get('text');self.voice.send_text(text,auto_pick=True);self.messages.append({'name':'You','text':text[:2000]})
  elif cmd=='select':self.voice.select(request.get('name'))
  elif cmd=='pause':self.stop()
  elif cmd=='camera-on':
   if request.get('consent') is not True:raise ValueError('Camera consent required')
   self.camera.start(True)
  elif cmd=='camera-off':self.judge.stop();self.camera.stop();self.context.presence='unknown';self.context.events.clear()
  elif cmd=='apps':
   if type(request.get('enabled')) is not bool or type(request.get('titles',False)) is not bool:raise ValueError('Invalid app consent')
   self.judge.stop();self.titles=request.get('titles',False) and request['enabled'];self.context.set_apps(request['enabled']);self.context.events.clear()
  elif cmd=='judgment':
   self.judge.stop();self.judge.gaming=request.get('gaming') is True
   if request.get('enabled') is True:self.judge.enable(request.get('context_consent') is True,request.get('audio') is True)
  elif cmd=='close':self.stop();self.judge.close();self.voice.close();self.closed=True
  self.poll()
  for _ in range(80):
   try:kind,value=self.voice.events.get_nowait()
   except queue.Empty:break
   if kind in ('state','status','error','proactive-status'):self.status=str(value)[:220]
   elif kind in ('answer','proactive-answer'):self.messages.append({'name':value.get('profile','JARVIS'),'text':value['text'][:4000],'provider':value.get('provider','local')})
  self.messages=self.messages[-50:]
  return {'selected':self.voice.name,'status':self.status,'busy':self.voice.busy,'messages':list(self.messages),'awareness':self.context.snapshot(),'judgment':{'enabled':self.judge.enabled,'audio':self.judge.audio,'gaming':self.judge.gaming}}
 def close(self):self.stop();self.judge.close();self.voice.close()
def main():
 bridge=Bridge()
 try:
  for line in sys.stdin:
   if len(line)>10000:result={'ok':False,'error':'Request too large'}
   else:
    try:result={'ok':True,'data':bridge.execute(json.loads(line))}
    except Exception as exc:result={'ok':False,'error':str(exc)[:250]}
   print(json.dumps(result,ensure_ascii=True),flush=True)
   if bridge.closed:break
 finally:bridge.close()
if __name__=='__main__':main()
