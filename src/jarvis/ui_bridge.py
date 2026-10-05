"""Narrow local stdio bridge for modern UI. No arbitrary shell/files/URLs or cloud routes."""
import sys,json,time,queue,threading
from .workspace_voice import WorkspaceVoice,build_text_router,build_proactive_speaker,VOICES
from .local_awareness import LocalContext,CameraWorker,foreground_app
from .proactive import ProactiveJudge
from .voice_setup import VoiceSetup
from .vision import LocalVision
class Bridge:
 def __init__(self,voice=None,brains=None,history=None):
  from .brain_settings import BrainSettings,SettingsPool
  from .paths import data_root
  self.brains=brains or BrainSettings(path=data_root()/'brain-routes.json')
  self.voice=voice or WorkspaceVoice();self.voice_preferences=None
  if voice is None:
   from .voice_preferences import VoicePreferences
   self.voice_preferences=VoicePreferences(data_root()/'voice-preferences.json');self.voice.tts_engine=self.voice_preferences.load()
  from .laya_assets import LayaSetup
  from .laya_engine import LayaEngine
  self.laya_setup=LayaSetup();self.laya_engine=LayaEngine()
  self.setup=VoiceSetup();self.context=LocalContext();self.camera=CameraWorker(self.context);self.vision=LocalVision(frame_source=self.camera.latest_jpeg);self.voice.vision=self.vision
  if voice is None:
   self.voice.text_factory=lambda:self.brains.router(self.voice.reply_actor)
   self.voice.pool_config=(SettingsPool(self.brains),(),())
  self.judge=ProactiveJudge(self.context,build_text_router,self.voice.notify,lambda:build_proactive_speaker(getattr(self.voice,'tts_engine','kokoro')))
  self.titles=False;self.last_app=0;self.closed=False;self.messages=[];self.status='off';self.error='';self.response_diagnostics=[];self.voice_metrics={};self.caption={'active':False,'name':'','text':''};self.lock=threading.RLock()
  self.reo_log=[];self.reo_seq=0;self.reo_submitted=False;self.laya_enabled=False;self.laya_generation=0;self.barge_in=False;self.laya_state={'busy':False,'status':'Off - inbuilt Laya model not loaded','error':''};self.browser=None;self.browser_enabled=False;self.browser_pending=None;self.vault=None;self.vault_results=[];self.vault_search={};self.vault_note='';self.history=history;self.history_error='';self.chat_id=None;self.archive_dirty=False;self.archive_saved_at=0
  if self.history is None and voice is None:
   try:
    from .chat_history import ChatHistory
    self.history=ChatHistory(data_root()/'chat-history.sqlite')
   except Exception:self.history_error='Local chat storage unavailable. Existing archive preserved; this session is not saved.'
  if self.history:
   previous=self.history.list();self.chat_id=previous[0]['id']if previous else self.history.new()
   if previous:
    try:self.messages=self.history.load(self.chat_id);self.voice.memory.restore(self.messages)
    except Exception:self.history_error='Saved conversation could not be restored. Original archive preserved.';self.chat_id=self.history.new()
 def poll(self):
  if self.reo_submitted and self.browser:
   state=self.browser.snapshot()
   if state.get('state') in ('ready','error','stopping'):
    self.reo_submitted=False;self.reo_event('completed' if state.get('state')=='ready' else 'stopped','Browser reports '+state.get('state','unknown')+': '+str(state.get('url',''))[:200]+'. This verifies browser state, not the whole user goal.')
  if self.context.apps and time.monotonic()-self.last_app>=1:
   self.last_app=time.monotonic()
   try:self.context.app_event(foreground_app(self.titles))
   except Exception:self.context.app_event(None)
  busy=self.voice.busy or self.voice.runtime is not None;self.judge.conversation_busy=busy
  if busy and self.judge.busy:self.judge.stop()
  self.judge.poll(busy)
  if self.voice.runtime is not None:self.voice.runtime.action_handler=self.voice_action
 def reo_event(self,state,text):
  with self.lock:
   self.reo_seq+=1;self.reo_log.append({'id':self.reo_seq,'state':state,'text':str(text)[:400]});self.reo_log=self.reo_log[-30:]
 def reo_action(self,text):
  from .reo_commands import parse
  goal=parse(text)
  if goal is None:return False
  self.reo_event('received','Reo goal: '+goal)
  if not self.laya_enabled or not self.browser_enabled:
   self.reo_event('blocked','Enable Reo + Laya and browser commands in Settings > Tools. Nothing executed.');self.browser_pending=None;return True
  from .browser_control import parse_voice
  direct=goal if goal.lower().startswith('browser ')else 'browser '+goal
  try:
   proposal=parse_voice(direct)
   if proposal is not None:
    self.execute({'command':'browser-preview','text':direct})
    self.reo_event('review','Browser command prepared. Review the exact command in Settings > Tools; nothing executed.')
   else:
    if self.laya_engine.agent is None:raise ValueError('Load inbuilt Laya first')
    self.start_laya(goal)
  except (ValueError,RuntimeError,queue.Full)as error:
   self.browser_pending=None;self.reo_event('blocked',str(error)+'. Nothing executed.')
  return True
 def voice_action(self,text):
  if self.reo_action(text):return True
  from .vault_voice import parse_voice as parse_vault
  try:vault_request=parse_vault(text)
  except ValueError as error:
   self.voice.notify('error',str(error));return True
  if vault_request:
   try:
    self.execute(vault_request)
    self.voice.notify('status','Local vault results ready in Settings > Memory. Nothing sent to a chat API.')
   except (ValueError,OSError,UnicodeError) as error:
    self.voice.notify('error','Local vault command failed. Check the connected vault and exact Markdown note path in Settings > Memory.')
   return True
  import re
  browser_explicit=bool(re.match(r'^\s*(?:(?:hey|hi|hello)\s+)?(?:(?:jarvis|nova|kai|lyra|dex)[, :]+)?browser\s+(?:open|search|scroll|read|choose|select|youtube|click|type|send|pay|buy|upload|delete)\b',text,re.I))
  if not self.browser_enabled:
   if browser_explicit:
    self.browser_pending=None;self.voice.notify('error','Browser control is OFF. Enable it in Settings > Tools; nothing opened or sent to a model.');return True
   return False
  from .browser_control import parse_voice
  try:proposal=parse_voice(text)
  except ValueError:
   self.browser_pending=None
   self.voice.notify('error','Browser destination rejected. Use a public HTTPS site.');return True
  if not proposal:
   if browser_explicit:
    self.browser_pending=None;self.voice.notify('error','Unsupported browser command. Use reviewed open/search/scroll or observed link numbers; nothing opened or sent to a model.');return True
   return False
  if proposal['command']in ('read-links','select-link'):
   try:
    self.execute({'command':'browser-links'}if proposal['command']=='read-links'else {'command':'browser-select','link_id':proposal['value']})
    self.voice.notify('status','Reading browser links locally.'if proposal['command']=='read-links'else'Link selected. Review its exact URL in Settings > Tools.')
   except (ValueError,RuntimeError,queue.Full):
    self.browser_pending=None;self.voice.notify('error','Open a reviewed site and read its available links first.')
   return True
  try:
   with self.lock:self.laya_generation+=1;self.laya_state['busy']=False;self.browser_pending=self.bind_browser_page(proposal)
  except ValueError as error:
   self.browser_pending=None;self.voice.notify('error',str(error));return True
  self.voice.notify('status','Browser command ready. Review the exact command in Settings > Tools. Nothing opened yet.')
  return True
 def bind_browser_page(self,proposal):
  if proposal['command']not in ('scroll-down','scroll-up'):return proposal
  if not self.browser or self.browser.cancel.is_set():raise ValueError('Open a reviewed browser page before scrolling')
  state=self.browser.snapshot()
  if state.get('state')!='ready' or not state.get('url'):raise ValueError('Wait for the browser page to finish loading before scrolling')
  from .browser_control import BrowserControl
  return dict(proposal,expected_url=BrowserControl.destination(state['url']))
 def stop_laya(self):
  self.laya_engine.stop();self.laya_setup.stop()
  self.laya_enabled=False;self.laya_generation+=1;self.laya_state={'busy':False,'status':'Off - no proposals requested','error':''}
 def start_laya(self,goal):
  if not self.laya_enabled or not self.browser_enabled or not self.browser or self.browser.cancel.is_set():raise ValueError('Enable Reo + Laya and open a reviewed browser page first')
  if not isinstance(goal,str)or not goal.strip()or len(goal)>1000:raise ValueError('Enter a short browser goal')
  if self.laya_state['busy']:raise ValueError('Laya proposal already running')
  from .laya_browser import fingerprint,prepare
  state=self.browser.snapshot();browser=self.browser;identity=fingerprint(state)
  if state.get('state')!='ready':raise ValueError('Wait for the page then read current links')
  self.browser_pending=None;self.laya_generation+=1;ticket=self.laya_generation;self.laya_state={'busy':True,'status':'Asking local Laya, no action executing','error':''};self.reo_event('thinking','Laya is deciding one step locally. No action executing.')
  def run():
   try:
    proposal,status=prepare(state,goal,client=self.laya_engine)
    with self.lock:
     if ticket!=self.laya_generation or not self.laya_enabled or not self.browser_enabled or self.browser is not browser or browser.cancel.is_set():return
     current=browser.snapshot()
     if current.get('state')!='ready' or fingerprint(current)!=identity:raise ValueError('Browser page or offered links changed; read links and ask again')
     self.browser_pending=proposal;self.laya_state={'busy':False,'status':status,'error':''};self.reo_event('review'if proposal else 'no-action',status)
   except Exception as error:
    with self.lock:
     if ticket==self.laya_generation:self.reo_event('blocked','Proposal unavailable or page changed; nothing executed.');self.browser_pending=None;self.laya_state={'busy':False,'status':'No proposal accepted; nothing executed','error':type(error).__name__+'. Check the inbuilt Laya model setup/load and current page; no external server or automatic fallback.'}
  threading.Thread(target=run,daemon=True).start()
 def stop(self):
  self.stop_laya()
  self.brains.stop_warmup()
  self.browser_enabled=False;self.browser_pending=None;
  if self.browser:self.browser.close()
  self.setup.stop();self.judge.stop();self.camera.stop();self.context.clear();self.titles=False;self.voice.pause();self.status='off';self.error='';self.response_diagnostics=[];self.voice_metrics={};self.caption={'active':False,'name':'','text':''}
  if not self.camera.stopped():self.context.camera_state('stopping')
 def execute(self,request):
  if not isinstance(request,dict):raise ValueError('Invalid command')
  if any(key in request for key in ('cloud','cloud_consent','provider','api_key','model','path','url')):raise ValueError('Use scoped account settings; arbitrary destinations are unavailable')
  cmd=request.get('command');allowed={'status','chat','select','pause','close','camera-on','camera-off','apps','judgment','voice-on','voice-off','voice-setup','voice-check','voice-cancel','brain-save','key-save','key-delete','brain-check','brain-models','brain-warmup','team-round','history-list','history-open','history-new','history-delete','history-clear','vault-connect','vault-disconnect','vault-search','vault-read','vault-create','vault-preview','browser-mode','browser-preview','browser-run','browser-stop','voice-engine','voice-endpoint','browser-links','browser-select','laya-setup','laya-check','laya-load','laya-cancel','laya-mode','laya-propose','laya-stop','camera-vision'}
  if cmd not in allowed:raise ValueError('Unknown command')
  if cmd in ('laya-setup','laya-check'):
   self.laya_setup.start(consent=request.get('consent')is True,check=cmd=='laya-check')
  elif cmd=='laya-load':self.laya_engine.load(consent=request.get('consent')is True)
  elif cmd=='laya-cancel':self.stop_laya();self.browser_pending=None
  elif cmd=='laya-mode':
   if request.get('consent')is not True:raise ValueError('Review local Laya disclosure first')
   self.laya_generation+=1;self.laya_enabled=True;self.laya_state={'busy':False,'status':'Enabled this session - load the inbuilt Laya engine; exact review still required','error':''}
  elif cmd=='laya-propose':self.start_laya(request.get('goal'))
  elif cmd=='laya-stop':self.stop_laya();self.browser_pending=None
  elif cmd.startswith('browser-'):
   self.laya_generation+=1
   if self.laya_state['busy']:self.laya_state={'busy':False,'status':'Proposal superseded by a browser command; nothing executed','error':''}
   if cmd=='browser-stop':
    self.stop_laya()
    self.browser_enabled=False;self.browser_pending=None
    if self.browser:self.browser.close()
   elif cmd=='browser-mode':
    if request.get('consent') is not True:raise ValueError('Allow isolated browser control first')
    self.browser_enabled=True
   elif cmd=='browser-preview':
    if not self.browser_enabled:raise ValueError('Enable browser mode first')
    from .browser_control import parse_voice
    self.browser_pending=None
    parsed=parse_voice(request.get('text'));self.browser_pending=self.bind_browser_page(parsed)if parsed else None
    if not self.browser_pending:raise ValueError('Use browser open example.com, browser search for something, or browser scroll down/up')
    if self.browser_pending['command']in ('read-links','select-link'):
     proposal=self.browser_pending;self.browser_pending=None
     return self.execute({'command':'browser-links'}if proposal['command']=='read-links'else{'command':'browser-select','link_id':proposal['value']})
   elif cmd=='browser-links':
    if not self.browser_enabled or not self.browser:raise ValueError('Open a reviewed browser site first')
    self.browser.submit('read-links',confirmed=True)
   elif cmd=='browser-select':
    self.browser_pending=None
    if not self.browser_enabled or not self.browser or self.browser.cancel.is_set():raise ValueError('Browser control is off or stopping')
    if self.browser.snapshot().get('state')!='ready':raise ValueError('Wait for the browser page to finish loading')
    if not self.browser:raise ValueError('No controlled browser page')
    from .browser_links import prepare_select
    state=self.browser.snapshot()
    self.browser_pending=prepare_select({'page_url':state.get('url'),'links':state.get('links',[])},str(request.get('link_id')),state.get('url'))
    self.browser_pending.pop('label',None)
    self.browser_pending['expected_url']=state.get('url')
   elif cmd=='browser-run':
    if not self.browser_enabled or not self.browser_pending:raise ValueError('No browser command to review')
    if request.get('confirm') is not True or request.get('reviewed')!=self.browser_pending:raise ValueError('Browser command changed; review it again')
    if self.browser and self.browser.cancel.is_set():
     if self.browser.thread.is_alive():raise ValueError('Browser is stopping; wait before restarting')
     self.browser=None
    if not self.browser:
     from .browser_control import BrowserSession
     from .paths import data_root
     self.browser=BrowserSession(data_root()/'browser-profile')
    self.reo_event('submitted','Reviewed '+self.browser_pending['command']+' command submitted to browser. Completion not yet verified.');self.browser.submit(**self.browser_pending,confirmed=True);self.reo_submitted=True;self.browser_pending=None
   self.error=''
  elif cmd.startswith('vault-'):
   if cmd=='vault-preview':
    from .vault_voice import parse_voice as parse_vault
    proposal=parse_vault(request.get('text'))
    if not proposal:raise ValueError('Use obsidian search words or obsidian read Exact/Note.md')
    return self.execute(proposal)
   if cmd=='vault-connect':
    if request.get('consent') is not True:raise ValueError('Allow local vault access first')
    from .obsidian import Vault
    self.vault=Vault(request.get('vault_folder',''));self.vault_results=[];self.vault_search={};self.vault_note=''
   elif cmd=='vault-disconnect':self.vault=None;self.vault_results=[];self.vault_search={};self.vault_note=''
   else:
    if not self.vault:raise ValueError('Connect a local vault first')
    if cmd=='vault-search':
     self.vault_results=[];self.vault_search={}
     self.vault_search=self.vault.search_details(request.get('query'));self.vault_results=self.vault_search['results']
    elif cmd=='vault-read':self.vault_note=self.vault.read(request.get('note_name'))
    elif cmd=='vault-create':
     reviewed={'vault_folder':str(self.vault.root),'note_name':request.get('note_name'),'note_text':request.get('note_text')}
     if request.get('reviewed')!=reviewed:raise ValueError('Vault or note changed; review the exact destination and text again')
     self.vault.create(request.get('note_name'),request.get('note_text'),request.get('confirm')is True);self.vault_note='Note created locally. Nothing sent to an API.'
   self.error=''
  elif cmd.startswith('history-'):
   if not self.history:raise ValueError(self.history_error or 'History unavailable')
   if cmd!='history-list' and (self.voice.busy or self.voice.runtime is not None):raise ValueError('Stop voice and wait for the current turn before changing chats')
   self.save_history(force=True)
   if cmd=='history-open':
    rows=self.history.load(request.get('chat_id'));self.messages=rows;self.chat_id=request['chat_id'];self.voice.memory.restore(rows)
   elif cmd=='history-new':self.messages=[];self.voice.memory.clear();self.chat_id=self.history.new()
   elif cmd=='history-delete':
    if request.get('confirm')is not True:raise ValueError('Confirm delete this chat')
    self.history.delete(request.get('chat_id'))
    if request.get('chat_id')==self.chat_id:self.messages=[];self.voice.memory.clear();self.chat_id=self.history.new()
   elif cmd=='history-clear':
    if request.get('confirm')is not True:raise ValueError('Confirm delete all chat history')
    self.history.clear();self.messages=[];self.voice.memory.clear();self.chat_id=self.history.new()
   self.archive_dirty=False;self.error=''
  elif cmd=='brain-save':
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice and wait for the current reply before changing routes')
   self.brains.configure(request.get('slots'),request.get('assignments'));self.status='Account routes saved. Session consent is required after each launch.'
  elif cmd=='key-save':self.brains.set_key(request.get('slot'),request.get('kind'),request.get('secret'));self.status='Key saved in Windows Credential Manager; key is never returned.'
  elif cmd=='key-delete':self.brains.delete_key(request.get('slot'),request.get('kind'));self.status='Stored key removed.'
  elif cmd=='brain-warmup':
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice and wait for the current reply before local warmup')
   self.brains.prewarm(consent=request.get('consent')is True,notify=self.voice.notify)
  elif cmd=='brain-check':self.brains.check(request.get('slot','local'),self.voice.notify)
  elif cmd=='brain-models':self.brains.list_models(request.get('slot'),self.voice.notify)
  elif cmd=='team-round':self.voice.parallel_round(request.get('text'),self.brains,request.get('audio') is True)
  elif cmd=='chat':
   self.error='';self.response_diagnostics=[];text=request.get('text')
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice and wait for the current turn before typed chat')
   if self.reo_action(text):self.messages.append({'name':'You','text':str(text)[:2000]});self.archive_dirty=True
   else:self.voice.send_text(text,auto_pick=True)
  elif cmd=='select':self.judge.stop();self.voice.select(request.get('name'))
  elif cmd=='pause':self.stop()
  elif cmd=='voice-endpoint':
   from .audio import ENDPOINT_FRAMES
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice before changing listening pause')
   if request.get('mode')not in ENDPOINT_FRAMES:raise ValueError('Choose a listening pause preset')
   self.voice.endpoint_mode=request['mode']
  elif cmd=='voice-engine':
   if self.voice.busy or self.voice.runtime is not None or self.setup.busy:raise ValueError('Stop voice and wait for model setup before changing speech engine')
   if request.get('engine')not in ('kokoro','kitten'):raise ValueError('Unknown speech engine')
   if self.voice_preferences:self.voice_preferences.save(request['engine'])
   self.judge.close();self.voice.tts_engine=request['engine'];self.setup.select(request['engine'])
  elif cmd=='voice-setup':
   engine=getattr(self.voice,'tts_engine','kokoro')
   if request.get('reviewed_engine')!=engine:raise ValueError('Speech engine changed; review the download again')
   self.setup.start(consent=request.get('consent') is True,engine=engine)
  elif cmd=='voice-check':self.setup.start(check=True,engine=getattr(self.voice,'tts_engine','kokoro'))
  elif cmd=='voice-cancel':self.setup.stop()
  elif cmd=='voice-on':
   if request.get('consent') is not True:raise ValueError('Microphone consent required')
   self.judge.stop()
   self.barge_in=request.get('barge_in')is True
   if request.get('reasoning_off')is True:self.voice.start(consent=True,cloud=False,reasoning_off=True,barge_in=self.barge_in)
   else:self.voice.start(consent=True,cloud=False,barge_in=self.barge_in)
  elif cmd=='voice-off':self.voice.pause();self.barge_in=False
  elif cmd=='camera-on':
   if request.get('consent') is not True:raise ValueError('Camera consent required')
   self.camera.start(True)
  elif cmd=='camera-off':self.vision.disable();self.judge.stop();self.camera.stop();self.context.presence='unknown';self.context.events.clear()
  elif cmd=='camera-vision':
   if request.get('enabled') is False:self.vision.disable()
   else:
    if request.get('consent') is not True:raise ValueError('Camera vision consent required')
    if self.context.camera!='on':raise ValueError('Allow the local camera first; vision shares the current camera frame with the local model only.')
    self.vision.enable(consent=True)
  elif cmd=='apps':
   if type(request.get('enabled')) is not bool or type(request.get('titles',False)) is not bool:raise ValueError('Invalid app consent')
   self.judge.stop();self.titles=request.get('titles',False) and request['enabled'];self.context.set_apps(request['enabled']);self.context.events.clear()
  elif cmd=='judgment':
   if type(request.get('enabled')) is not bool or type(request.get('audio',False)) is not bool or type(request.get('gaming',False)) is not bool:raise ValueError('Invalid judgment options')
   if request['enabled'] and request.get('context_consent') is not True:raise ValueError('Local persona context consent required')
   self.judge.stop();self.judge.gaming=request.get('gaming',False)
   if request['enabled']:self.judge.enable(True,request.get('audio',False))
  elif cmd=='close':self.save_history(force=True);self.setup.stop();self.stop();self.judge.close();self.voice.close();self.closed=True
  self.poll()
  for _ in range(80):
   try:kind,value=self.voice.events.get_nowait()
   except queue.Empty:break
   if kind=='speech-caption':
    if value.get('active') and cmd not in ('pause','close','voice-off'):
     at=value.get('at',0);duration=min(120,max(0,value.get('duration_s',0)));age=time.monotonic()-at
     if 0<=age<=duration+.3:self.caption={**value,'expires':at+duration+.3}
    else:self.caption={'active':False,'name':'','text':''}
   elif kind=='metrics'and cmd not in ('pause','close','voice-off'):self.voice_metrics={k:v for k,v in value.items()if k in ('stt_s','first_text_s','first_clause_s','first_output_write_s','turn_s','scope')and(isinstance(v,(int,float))and not isinstance(v,bool)and 0<=v<3600 or k=='scope'and isinstance(v,str))}
   elif kind=='response-diagnostics':self.response_diagnostics=value[-2:]
   elif kind=='error':self.error=str(value)[:300]
   elif kind=='voice-actor':self.voice.reply_actor=str(value)
   elif kind in ('state','status','proactive-status'):self.status=str(value)[:220]
   elif kind=='transcript':self.messages.append({'name':'You','text':str(value)[:2000]});self.archive_dirty=True
   elif kind in ('answer','proactive-answer'):
    self.archive_dirty=True
    row={'name':value.get('profile',self.voice.name),'text':value['text'][:4000],'provider':value.get('provider','local')}
    if 'stream_id' in value:row['stream_id']=value['stream_id']
    if self.messages and self.messages[-1]['name']==row['name'] and (self.voice.runtime is not None or ('stream_id' in row and self.messages[-1].get('stream_id')==row['stream_id'])):self.messages[-1]=row
    else:self.messages.append(row)
  self.messages=self.messages[-200:]
  self.save_history()
  # Runtime activity, not decorative preview. Reserved visemes can be added by an audio clock.
  voice_state=self.status.lower();actor='JARVIS' if self.judge.busy else self.voice.reply_actor if self.voice.busy else self.voice.runtime.persona if self.voice.runtime is not None else self.voice.name
  active=self.voice.busy or (self.voice.runtime is not None and self.voice.runtime.busy) or self.judge.busy
  speaking=active and ('speaking' in voice_state or 'team-leader speech' in voice_state)
  state='speaking' if speaking else 'thinking' if active else 'idle'
  if self.caption.get('active')and time.monotonic()>self.caption.get('expires',0):self.caption={'active':False,'name':'','text':''}
  return {'reo_log':list(self.reo_log),'laya':dict(self.laya_state,enabled=self.laya_enabled,setup=self.laya_setup.snapshot(),engine=self.laya_engine.snapshot()),'browser':{'enabled':self.browser_enabled,'pending':self.browser_pending,'status':self.browser.snapshot()if self.browser else {'state':'off'}},'vault':{'connected':self.vault is not None,'folder':str(self.vault.root)if self.vault else'','results':self.vault_results,'search':self.vault_search,'note':self.vault_note},'history':self.history.list()if self.history else[],'chat_id':self.chat_id,'history_error':self.history_error,'history_limits':'Local plain-text storage, up to 50 chats and 200 messages per chat; oldest chats removed at the limit. Only selected chat recent context goes to APIs when you allow it. Delete does not remove external backups.','brains':self.brains.snapshot(),'caption':self.caption,'voice_metrics':self.voice_metrics,'response_diagnostics':self.response_diagnostics,'expression':{'persona':actor,'state':state,'source':'live-runtime','viseme':None},'endpoint_mode':self.voice.endpoint_mode if isinstance(getattr(self.voice,'endpoint_mode',None),str)else'balanced','tts_engine':getattr(self.voice,'tts_engine','kokoro'),'selected':self.voice.name,'status':self.status,'error':self.error,'busy':self.voice.busy,'voice_active':self.voice.runtime is not None and self.voice.runtime.enabled,'barge_in':self.barge_in,'voice_setup':self.setup.snapshot(),'voice_loading':self.voice.busy and self.status=='loading voice','messages':list(self.messages),'awareness':{**self.context.snapshot(),'vision':'on' if self.vision.enabled else 'off'},'judgment':{'enabled':self.judge.enabled,'audio':self.judge.audio,'gaming':self.judge.gaming,'waiting_reason':self.judge.waiting_reason(self.voice.busy or self.voice.runtime is not None)}}
 def save_history(self,force=False):
  if not self.history or not self.archive_dirty:return
  if not force and self.voice.busy and time.monotonic()-self.archive_saved_at<1:return
  try:self.history.save(self.chat_id,self.messages);self.archive_dirty=False;self.archive_saved_at=time.monotonic()
  except Exception:self.history_error='Chat could not be saved. Current session remains available; original archive preserved.'
 def close(self):self.save_history(force=True);self.setup.stop();self.stop();self.judge.close();self.voice.close()
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
