"""Narrow local stdio bridge for modern UI. No arbitrary shell/files/URLs or cloud routes."""
import sys,json,time,queue,threading
from .workspace_voice import WorkspaceVoice,build_text_router,build_proactive_speaker,VOICES
from .local_awareness import LocalContext,CameraWorker,foreground_app
from .proactive import ProactiveJudge
from .voice_setup import VoiceSetup
class Bridge:
 def __init__(self,voice=None,brains=None):
  from .brain_settings import BrainSettings,SettingsPool
  from .paths import data_root
  self.brains=brains or BrainSettings(path=data_root()/'brain-routes.json')
  self.voice=voice or WorkspaceVoice();self.setup=VoiceSetup();self.context=LocalContext();self.camera=CameraWorker(self.context)
  if voice is None:
   self.voice.text_factory=lambda:self.brains.router(self.voice.reply_actor)
   self.voice.pool_config=(SettingsPool(self.brains),(),())
  self.judge=ProactiveJudge(self.context,build_text_router,self.voice.notify,build_proactive_speaker)
  self.titles=False;self.last_app=0;self.closed=False;self.messages=[];self.status='off';self.error='';self.response_diagnostics=[];self.caption={'active':False,'name':'','text':''};self.lock=threading.RLock()
 def poll(self):
  if self.context.apps and time.monotonic()-self.last_app>=1:
   self.last_app=time.monotonic()
   try:self.context.app_event(foreground_app(self.titles))
   except Exception:self.context.app_event(None)
  busy=self.voice.busy or self.voice.runtime is not None;self.judge.conversation_busy=busy
  if busy and self.judge.busy:self.judge.stop()
  self.judge.poll(busy)
 def stop(self):
  self.setup.stop();self.judge.stop();self.camera.stop();self.context.clear();self.titles=False;self.voice.pause();self.voice.memory.clear();self.messages=[];self.status='off';self.error='';self.response_diagnostics=[];self.caption={'active':False,'name':'','text':''}
  if not self.camera.stopped():self.context.camera_state('stopping')
 def execute(self,request):
  if not isinstance(request,dict):raise ValueError('Invalid command')
  if any(key in request for key in ('cloud','cloud_consent','provider','api_key','model','path','url')):raise ValueError('Use scoped account settings; arbitrary destinations are unavailable')
  cmd=request.get('command');allowed={'status','chat','select','pause','close','camera-on','camera-off','apps','judgment','voice-on','voice-off','voice-setup','voice-check','voice-cancel','brain-save','key-save','key-delete','brain-check','team-round'}
  if cmd not in allowed:raise ValueError('Unknown command')
  if cmd=='brain-save':
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice and wait for the current reply before changing routes')
   self.brains.configure(request.get('slots'),request.get('assignments'));self.status='Account routes saved. Session consent is required after each launch.'
  elif cmd=='key-save':self.brains.set_key(request.get('slot'),request.get('kind'),request.get('secret'));self.status='Key saved in Windows Credential Manager; key is never returned.'
  elif cmd=='key-delete':self.brains.delete_key(request.get('slot'),request.get('kind'));self.status='Stored key removed.'
  elif cmd=='brain-check':self.brains.check(request.get('slot','local'),self.voice.notify)
  elif cmd=='team-round':self.voice.parallel_round(request.get('text'),self.brains,request.get('audio') is True)
  elif cmd=='chat':
   self.error='';self.response_diagnostics=[];text=request.get('text');self.voice.send_text(text,auto_pick=True)
  elif cmd=='select':self.judge.stop();self.voice.select(request.get('name'))
  elif cmd=='pause':self.stop()
  elif cmd=='voice-setup':self.setup.start(consent=request.get('consent') is True)
  elif cmd=='voice-check':self.setup.start(check=True)
  elif cmd=='voice-cancel':self.setup.stop()
  elif cmd=='voice-on':
   if request.get('consent') is not True:raise ValueError('Microphone consent required')
   self.judge.stop()
   if request.get('reasoning_off')is True:self.voice.start(consent=True,cloud=False,reasoning_off=True)
   else:self.voice.start(consent=True,cloud=False)
  elif cmd=='voice-off':self.voice.pause()
  elif cmd=='camera-on':
   if request.get('consent') is not True:raise ValueError('Camera consent required')
   self.camera.start(True)
  elif cmd=='camera-off':self.judge.stop();self.camera.stop();self.context.presence='unknown';self.context.events.clear()
  elif cmd=='apps':
   if type(request.get('enabled')) is not bool or type(request.get('titles',False)) is not bool:raise ValueError('Invalid app consent')
   self.judge.stop();self.titles=request.get('titles',False) and request['enabled'];self.context.set_apps(request['enabled']);self.context.events.clear()
  elif cmd=='judgment':
   if type(request.get('enabled')) is not bool or type(request.get('audio',False)) is not bool or type(request.get('gaming',False)) is not bool:raise ValueError('Invalid judgment options')
   if request['enabled'] and request.get('context_consent') is not True:raise ValueError('Local persona context consent required')
   self.judge.stop();self.judge.gaming=request.get('gaming',False)
   if request['enabled']:self.judge.enable(True,request.get('audio',False))
  elif cmd=='close':self.setup.stop();self.stop();self.judge.close();self.voice.close();self.closed=True
  self.poll()
  for _ in range(80):
   try:kind,value=self.voice.events.get_nowait()
   except queue.Empty:break
   if kind=='speech-caption':
    if value.get('active') and cmd not in ('pause','close','voice-off'):
     at=value.get('at',0);duration=min(120,max(0,value.get('duration_s',0)));age=time.monotonic()-at
     if 0<=age<=duration+.3:self.caption={**value,'expires':at+duration+.3}
    else:self.caption={'active':False,'name':'','text':''}
   elif kind=='response-diagnostics':self.response_diagnostics=value[-2:]
   elif kind=='error':self.error=str(value)[:300]
   elif kind=='voice-actor':self.voice.reply_actor=str(value)
   elif kind in ('state','status','proactive-status'):self.status=str(value)[:220]
   elif kind=='transcript':self.messages.append({'name':'You','text':str(value)[:2000]})
   elif kind in ('answer','proactive-answer'):
    row={'name':value.get('profile',self.voice.name),'text':value['text'][:4000],'provider':value.get('provider','local')}
    if 'stream_id' in value:row['stream_id']=value['stream_id']
    if self.messages and self.messages[-1]['name']==row['name'] and (self.voice.runtime is not None or ('stream_id' in row and self.messages[-1].get('stream_id')==row['stream_id'])):self.messages[-1]=row
    else:self.messages.append(row)
  self.messages=self.messages[-50:]
  # Runtime activity, not decorative preview. Reserved visemes can be added by an audio clock.
  voice_state=self.status.lower();actor='JARVIS' if self.judge.busy else self.voice.reply_actor if self.voice.busy else self.voice.runtime.persona if self.voice.runtime is not None else self.voice.name
  active=self.voice.busy or (self.voice.runtime is not None and self.voice.runtime.busy) or self.judge.busy
  speaking=active and ('speaking' in voice_state or 'team-leader speech' in voice_state)
  state='speaking' if speaking else 'thinking' if active else 'idle'
  if self.caption.get('active')and time.monotonic()>self.caption.get('expires',0):self.caption={'active':False,'name':'','text':''}
  return {'brains':self.brains.snapshot(),'caption':self.caption,'response_diagnostics':self.response_diagnostics,'expression':{'persona':actor,'state':state,'source':'live-runtime','viseme':None},'selected':self.voice.name,'status':self.status,'error':self.error,'busy':self.voice.busy,'voice_active':self.voice.runtime is not None and self.voice.runtime.enabled,'voice_setup':self.setup.snapshot(),'voice_loading':self.voice.busy and self.status=='loading voice','messages':list(self.messages),'awareness':self.context.snapshot(),'judgment':{'enabled':self.judge.enabled,'audio':self.judge.audio,'gaming':self.judge.gaming,'waiting_reason':self.judge.waiting_reason(self.voice.busy or self.voice.runtime is not None)}}
 def close(self):self.setup.stop();self.stop();self.judge.close();self.voice.close()
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
