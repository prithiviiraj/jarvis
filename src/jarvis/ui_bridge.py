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
  from .agent_registry import AgentRegistry
  self.agents=AgentRegistry(data_root()/'custom-agents.json');self.agents.apply()
  from .obsidian_vault import Vault
  self.obsidian=Vault(data_root()/'obsidian-connect.json')
  from .local_calendar import LocalCalendar
  self.calendar=LocalCalendar(self.obsidian);self.calendar_open_pending=False;self.calendar_draft=None
  self.brains=brains or BrainSettings(path=data_root()/'brain-routes.json')
  self.voice=voice or WorkspaceVoice();self.voice_preferences=None
  if voice is None:
   from .voice_preferences import VoicePreferences
   self.voice_preferences=VoicePreferences(data_root()/'voice-preferences.json');self.voice.tts_engine=self.voice_preferences.load()
  from .laya_assets import LayaSetup
  from .laya_engine import LayaEngine
  self.laya_setup=LayaSetup();self.laya_engine=LayaEngine()
  from .local_speed import LocalSpeed
  self.local_speed=LocalSpeed(self.brains.local_gate)
  self.setup=VoiceSetup();self.context=LocalContext();self.camera=CameraWorker(self.context);self.vision=LocalVision(frame_source=self.camera.latest_jpeg);self.voice.vision=self.vision;self.voice.agent_nodes=self.obsidian
  if voice is None:
   self.voice.text_factory=lambda:self.brains.router(self.voice.reply_actor)
   self.voice.pool_config=(SettingsPool(self.brains),(),())
  from .idle_companion import IdleCompanion
  from .experimental.smart_turn import TurnSetup
  self.turn_setup=TurnSetup()
  from .experimental.static_vault_search import SearchSetup,VaultSearch
  self.search_setup=SearchSetup();self.semantic_search=VaultSearch(self.search_setup)
  self.idle=IdleCompanion(self.voice,self.brains,self.voice.notify)
  self.judge=ProactiveJudge(self.context,build_text_router,self.voice.notify,lambda:build_proactive_speaker(getattr(self.voice,'tts_engine','kokoro')))
  from .game_companion import GameCompanion
  self.game=GameCompanion(self.voice.notify);self.game_windows=[]
  from .news_conductor import NewsConductor
  self.news=NewsConductor()
  from .news_speech import NewsSpeech
  self.news_speech=NewsSpeech(lambda:build_proactive_speaker(getattr(self.voice,'tts_engine','kokoro')))
  from .game_speech import GameSpeech
  self.game_speech=GameSpeech(self.game,lambda:build_proactive_speaker(getattr(self.voice,'tts_engine','kokoro')),self.voice.notify)
  from .tiny_specialists import Specialists
  from .reviewed_evolution import Proposal
  from .teammate_awareness import TeammateAwareness
  self.teammate_awareness=TeammateAwareness(self.teammate_state);self.voice.teammate_awareness=self.teammate_awareness
  self.evolution=Proposal();self.evolution_busy=False;self.evolution_cancel=threading.Event();self.evolution_result='';self.evolution_error=''
  self.specialists=Specialists(gate=self.brains.local_gate);self.specialist_models=[];self.specialist_result=None
  self.titles=False;self.last_app=0;self.closed=False;self.messages=[];self.status='off';self.error='';self.warning='';self.response_diagnostics=[];self.voice_metrics={};self.dialogue_metrics=[];self.caption={'active':False,'name':'','text':''};self.lock=threading.RLock()
  self.plan_pending=None;self.desktop_enabled=False;self.desktop_pending=None;self.desktop_result={};self.control_generation=0;self.control_busy=False;self.reo_log=[];self.reo_seq=0;self.reo_submitted=False;self.laya_enabled=False;self.laya_generation=0;self.barge_in=False;self.laya_state={'busy':False,'status':'Off - inbuilt Laya model not loaded','error':''};self.browser=None;self.browser_enabled=False;self.browser_pending=None;self.vault=None;self.vault_results=[];self.vault_search={};self.vault_note='';self.history=history;self.history_error='';self.chat_id=None;self.archive_dirty=False;self.archive_saved_at=0
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
  if self.browser:
   state=self.browser.snapshot()
   try:self.news.observe(state)
   except ValueError:self.news.cancel()
   if self.news_speech.busy and (state.get('state')!='ready' or state.get('url')!=self.news.observed_url):self.news_speech.stop()
   captured=state.get('news_text')
   if self.news.requested and state.get('state')=='ready' and state.get('url')==self.news.observed_url and captured and captured.get('url')==self.news.observed_url and captured!=self.news.text_preview:
    try:self.news.accept_text(captured)
    except ValueError:self.news.text_preview=None;self.news.status='Page text changed; capture and review again'
   if self.reo_submitted and state.get('state') in ('ready','error','stopping'):
    self.reo_submitted=False;self.reo_event('completed' if state.get('state')=='ready' else 'stopped','Browser reports '+state.get('state','unknown')+': '+str(state.get('url',''))[:200]+'. '+(state.get('error','')or'This verifies browser state, not the whole user goal.'))
  if self.context.apps and time.monotonic()-self.last_app>=1:
   self.last_app=time.monotonic()
   try:self.context.app_event(foreground_app(self.titles))
   except Exception:self.context.app_event(None)
  self.game.poll(self.voice.busy or self.voice.runtime is not None)
  busy=self.voice.busy or self.voice.runtime is not None;self.judge.conversation_busy=busy
  if busy and self.judge.busy:self.judge.stop()
  if not self.judge.busy and not self.judge.gaming:self.idle.poll()
  if not self.idle.busy:self.judge.poll(self.voice.busy or self.voice.runtime is not None)
  if self.voice.runtime is not None:self.voice.runtime.action_handler=self.voice_action
  self.obsidian.sync(self.messages,self.agents.snapshot(),{'tts_engine':self.voice.tts_engine,'turn_mode':self.voice.turn_mode,'endpoint_mode':self.voice.endpoint_mode,'selected':self.voice.name},self.chat_id)
 def reo_event(self,state,text):
  with self.lock:
   self.reo_seq+=1;self.reo_log.append({'id':self.reo_seq,'state':state,'text':str(text)[:400]});self.reo_log=self.reo_log[-30:]
 def reo_action(self,text):
  from .reo_commands import parse
  from .action_intent import goal as shared_goal
  goal=shared_goal(text)
  if goal is None:return False
  self.reo_event('received','Shared action goal: '+goal)
  if not self.laya_enabled or not self.browser_enabled:
   self.reo_event('blocked','Enable shared Laya and browser commands in Settings > Tools. Nothing executed.');self.browser_pending=None;return True
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
 @staticmethod
 def stop_intent(text):
  import re
  return isinstance(text,str)and bool(re.fullmatch(r'\s*(?:(?:jarvis|nova|kai|lyra|dex)[,.:]?\s+)?(?:stop|stop talking|stop team conversation|quiet|be quiet|cancel conversation)[.!?]*\s*',text,re.I))
 def teammate_query(self,text):
  import re
  if not self.teammate_awareness.enabled or not isinstance(text,str):return False
  m=re.fullmatch(r'\s*(DEX|KAI)[,.:]?\s+(?:what(?: are you doing| is your status| did you install| code did you install| app am I using)|status)[?!.]*\s*',text,re.I)
  if not m:return False
  name=m.group(1).upper();state=self.teammate_state();row=state['teammates'][name]
  if 'app'in text.lower():
   sensors=state['permitted_local_sensors'];app=sensors['foreground'];answer='App monitoring is off; I do not know your current app.'if not sensors['app_monitor']else'Foreground app is '+str(app.get('process'))if app else'Foreground app is unknown.'
  elif 'install'in text.lower():answer='No code is installed by the proposal tool. Source/tests are proposal text only, not executed.'
  else:answer=('Reply in progress.'if row['reply_in_progress']else'No reply in progress.')+' No independent background work. '+('Last actual reply: '+row['recent_actual_reply']if row['recent_actual_reply']else'No actual recent reply recorded.')
  self.messages.append({'name':name,'text':answer,'provider':'verified-app-state','cloud':False});self.archive_dirty=True;return True
 def calendar_action(self,text):
  import re
  if not isinstance(text,str):return False
  if not (re.search(r'\b(?:tomorrow|today|calendar|appointment)\b',text,re.I)and re.search(r'\b(?:go|open|plan|appointment|calendar|meeting)\b',text,re.I)):return False
  if not self.obsidian.enabled:raise ValueError('Create Brain of Brain local calendar first')
  from .calendar_handoff import draft
  self.calendar_draft=draft(text)
  self.calendar_open_pending=True;self.reo_event('review','Review local calendar area open. Fill exact title/date/start/end/timezone/place before saving; relative words are not an event.');return True
 def planning_action(self,text):
  import re
  if not isinstance(text,str)or not re.fullmatch(r"\s*(?:jarvis[,.:]?\s+)?(?:what(?:'s| is)\s+(?:the |my )?plan(?:s)?(?: for)? today|open (?:the )?(?:planning area|today plan))[?.!]*\s*",text,re.I):return False
  self.execute({'command':'plan-preview'});self.reo_event('review','Review opening Today plan in Obsidian. No note changed.');return True
 def desktop_action(self,text):
  from .desktop_actions import prepare
  proposal=prepare(text)
  if proposal is None:return False
  self.desktop_pending=None
  if not self.desktop_enabled:self.reo_event('blocked','Windows app launch is OFF. Review permission in Settings > Tools. Nothing opened.');return True
  self.desktop_pending=proposal;self.reo_event('review','Review exact '+proposal['label']+' launch in Settings > Tools. Nothing opened.');return True
 def shared_action(self,text):
  from .action_intent import parse
  try:proposal=parse(text)
  except ValueError as error:self.reo_event('blocked',str(error)+'. Nothing executed.');return True
  if proposal is None:return False
  self.reo_event('received','Shared browser action: '+str(text))
  if not self.browser_enabled:
   self.browser_pending=None;self.reo_event('blocked','Browser control is OFF. Enable it in Settings > Tools; nothing executed.');return True
  try:
   with self.lock:self.laya_generation+=1;self.laya_state['busy']=False;self.browser_pending=self.bind_browser_page(proposal)
   self.reo_event('review','Exact browser command prepared for review. Nothing executed.')
  except ValueError as error:self.browser_pending=None;self.reo_event('blocked',str(error)+'. Nothing executed.')
  return True
 def voice_action(self,text):
  if self.stop_intent(text):self.news_speech.stop();self.game.stop();self.idle.stop();self.interrupt_conversation();return True
  if self.teammate_query(text):return True
  if self.news.request(text):return True
  if self.planning_action(text):return True
  if self.calendar_action(text):return True
  if self.desktop_action(text):return True
  if self.shared_action(text):return True
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
  if proposal['command']not in ('scroll-down','scroll-up','scroll-down-small','scroll-up-small'):return proposal
  if not self.browser or self.browser.cancel.is_set():raise ValueError('Open a reviewed browser page before scrolling')
  state=self.browser.snapshot()
  if state.get('state')!='ready' or not state.get('url'):raise ValueError('Wait for the browser page to finish loading before scrolling')
  from .browser_control import BrowserControl
  return dict(proposal,expected_url=BrowserControl.destination(state['url']))
 def enable_control(self,consent=False):
  if consent is not True:raise ValueError('Review browser control setup and local model use first')
  if self.control_busy or self.laya_setup.busy or self.laya_engine.loading:raise ValueError('Browser setup already running')
  self.interrupt_conversation();self.control_generation+=1;ticket=self.control_generation;self.control_busy=True
  self.browser_enabled=False;self.laya_enabled=False;self.browser_pending=None
  self.laya_state={'busy':False,'status':'Preparing browser control: verifying model assets','error':''}
  self.reo_event('setup','Verifying local Laya assets; no browser action or microphone starts.')
  def current():return not self.closed and ticket==self.control_generation
  def run():
   try:
    worker=self.laya_setup.start(check=True);worker.join()
    if not current():return
    if not self.laya_setup.ready:
     self.laya_state['status']='Downloading missing verified Laya assets'
     worker=self.laya_setup.start(consent=True);worker.join()
    if not current():return
    if not self.laya_setup.ready:raise RuntimeError(self.laya_setup.error or 'Model assets unavailable')
    self.laya_state['status']='Loading verified local CPU Laya model'
    worker=self.laya_engine.load(consent=True);worker.join()
    if not current():return
    if self.laya_engine.agent is None:raise RuntimeError(self.laya_engine.error or 'Engine unavailable')
    self.browser_enabled=True;self.laya_enabled=True
    self.laya_state={'busy':False,'status':'Browser control ready. Turn Mic ON and ask Jarvis; every action still needs exact Confirm.','error':''}
    self.reo_event('ready','Browser control ready; no browser window or microphone started. Ask Jarvis by voice after Mic ON; Confirm each exact action.')
   except Exception as error:
    if current():
     self.browser_enabled=False;self.laya_enabled=False;self.laya_state={'busy':False,'status':'Browser setup stopped; nothing executed','error':str(error)[:240]};self.reo_event('blocked','Browser setup failed: '+str(error)[:240])
   finally:
    if current():self.control_busy=False
  thread=threading.Thread(target=run,daemon=True);thread.start();return thread
 def stop_laya(self):
  self.control_generation+=1;self.control_busy=False
  self.laya_engine.stop();self.laya_setup.stop();self.search_setup.stop();self.semantic_search.stop()
  self.laya_enabled=False;self.laya_generation+=1;self.laya_state={'busy':False,'status':'Off - no proposals requested','error':''}
 def start_laya(self,goal):
  if not self.laya_enabled or not self.browser_enabled or not self.browser or self.browser.cancel.is_set():raise ValueError('Enable shared Laya and open a reviewed browser page first')
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
 def teammate_state(self):
  sensors=self.context.snapshot();recent=self.voice.memory.snapshot();recent=recent if isinstance(recent,list)else[];states={}
  for name in ('DEX','KAI'):
   replies=[answer for actor,user,answer in recent if actor==name]
   states[name]={'role':'coder'if name=='DEX'else'researcher','reply_in_progress':self.voice.busy and self.voice.reply_actor==name,'recent_actual_reply':replies[-1][:1200]if replies else None,'independent_background_work':False}
  if hasattr(self,'evolution'):states['DEX']['code_proposal']={'busy':self.evolution_busy,'status':self.evolution.status,'installed':False,'tests_executed':False}
  return {'teammates':states,'permitted_local_sensors':{k:sensors[k]for k in ('camera','presence','app_monitor','foreground')},'game':{'enabled':self.game.enabled,'status':self.game.status},'scope':'Actual app state only. No independent autonomous jobs or awareness when sensor permission is off. No raw camera frame or credentials.'}
 def stop(self):
  self.news_speech.stop();self.news.cancel();self.calendar.cancel();self.calendar_open_pending=False;self.calendar_draft=None;self.plan_pending=None;self.obsidian.nodes_connected=False;self.teammate_awareness.stop();self.evolution_cancel.set();self.evolution.cancel();self.game_speech.stop();self.game.stop();self.specialists.stop()
  self.idle.stop();self.turn_setup.stop()
  self.stop_laya()
  self.local_speed.stop();self.brains.stop_warmup()
  self.desktop_enabled=False;self.desktop_pending=None;self.browser_enabled=False;self.browser_pending=None;
  if self.browser:self.browser.close()
  self.search_setup.stop();self.semantic_search.stop();self.setup.stop();self.judge.stop();self.camera.stop();self.context.clear();self.titles=False;self.voice.pause();self.status='off';self.error='';self.response_diagnostics=[];self.voice_metrics={};self.caption={'active':False,'name':'','text':''}
  if not self.camera.stopped():self.context.camera_state('stopping')
 def interrupt_conversation(self):
  self.news_speech.stop()
  """User changes supersede current reply/mic, without global sensor/tool shutdown."""
  self.game_speech.stop();self.game.stop();self.voice.pause();self.barge_in=False
  while True:
   try:self.voice.events.get_nowait()
   except __import__('queue').Empty:break
  self.status='Current reply and Mic stopped for your change. Camera and app permissions unchanged.'
  self.error='';self.caption={'active':False,'text':'','name':'JARVIS'}
 def execute(self,request):
  if not isinstance(request,dict):raise ValueError('Invalid command')
  if any(key in request for key in ('cloud','cloud_consent','provider','api_key','model','path','url')):raise ValueError('Use scoped account settings; arbitrary destinations are unavailable')
  cmd=request.get('command');allowed={'news-speak','news-stop','news-text','news-preview','news-open','news-cancel','canvas-open-preview','canvas-open','calendar-preview','calendar-save','calendar-cancel','calendar-open-preview','calendar-open','plan-preview','plan-open','plan-cancel','agent-nodes','teammate-awareness','evolution-generate','evolution-cancel','evolution-export','specialist-models','specialist-configure','specialist-run','specialist-stop','game-windows','game-enable','game-stop','obsidian-open','obsidian-create','obsidian-sync','obsidian-disable','desktop-mode','desktop-preview','desktop-run','desktop-cancel','status','conversation-interrupt','chat','select','pause','close','camera-on','camera-off','apps','judgment','voice-on','voice-off','voice-setup','voice-check','voice-cancel','brain-save','key-save','key-delete','brain-check','brain-models','brain-warmup','local-speed','local-speed-stop','team-round','team-dialogue','agent-create','turn-check','turn-setup','turn-cancel','turn-mode','idle-mode','idle-activity','history-list','history-open','history-new','history-delete','history-clear','embedding-check','embedding-setup','embedding-stop','vault-semantic','vault-semantic-stop','vault-connect','vault-disconnect','vault-search','vault-read','vault-create','vault-preview','browser-enable','browser-mode','browser-preview','browser-run','browser-stop','voice-engine','voice-endpoint','browser-links','browser-select','laya-setup','laya-check','laya-load','laya-cancel','laya-mode','laya-propose','laya-stop','camera-vision'}
  if cmd not in allowed:raise ValueError('Unknown command')
  if cmd in ('chat','voice-on','team-dialogue','team-round','history-new','history-open'):self.warning=''
  if cmd=='team-dialogue':self.dialogue_metrics=[]
  if cmd in ('chat','select','team-dialogue','team-round','voice-on','voice-engine','history-new','history-open'):
   # User conversation takes priority even when background game speech already started.
   self.game_speech.stop()
  if cmd not in ('status','idle-mode'):self.idle.activity()
  scoped_changes={'conversation-interrupt','brain-save','voice-engine','voice-endpoint','turn-mode','team-dialogue','team-round','history-new','history-open','history-delete','history-clear'}
  if cmd in scoped_changes and (self.voice.busy or self.voice.runtime is not None):self.interrupt_conversation()

  if cmd in ('chat','select','team-dialogue','team-round','voice-on','history-new','history-open'):self.news_speech.stop()
  if cmd in ('chat','select','team-dialogue','team-round','voice-on','history-new','history-open'):self.voice.pause()if getattr(self.voice,'dialogue_origin','user')=='idle'and self.voice.busy else None
  if cmd=='conversation-interrupt':self.interrupt_conversation()
  elif cmd=='obsidian-create':
   self.obsidian.create(request.get('reviewed_name'),request.get('confirm')is True)
   self.obsidian.sync(self.messages,self.agents.snapshot(),{'tts_engine':self.voice.tts_engine,'turn_mode':self.voice.turn_mode,'endpoint_mode':self.voice.endpoint_mode,'selected':self.voice.name},self.chat_id,force=True)
  elif cmd=='obsidian-open':self.obsidian.open()
  elif cmd=='obsidian-sync':self.obsidian.sync(self.messages,self.agents.snapshot(),{'tts_engine':self.voice.tts_engine,'turn_mode':self.voice.turn_mode,'endpoint_mode':self.voice.endpoint_mode,'selected':self.voice.name},self.chat_id,force=True)
  elif cmd=='obsidian-disable':self.obsidian.disable()
  elif cmd=='desktop-mode':
   if type(request.get('enabled'))is not bool:raise ValueError('Invalid app permission')
   if request['enabled']and request.get('consent')is not True:raise ValueError('Review Windows app launch permission')
   self.desktop_enabled=request['enabled'];self.desktop_pending=None
  elif cmd=='desktop-preview':
   if not self.desktop_action(request.get('text')):raise ValueError('Use open Notepad, Calculator or Paint')
  elif cmd=='desktop-cancel':self.desktop_pending=None
  elif cmd=='desktop-run':
   if not self.desktop_enabled or self.desktop_pending is None:raise ValueError('No app launch pending')
   from .desktop_actions import launch
   pending=self.desktop_pending
   if request.get('confirm')is not True or request.get('reviewed')!=pending:raise ValueError('App launch changed; review it again')
   result=launch(pending,request.get('reviewed'),request.get('confirm')is True)
   self.desktop_pending=None;self.desktop_result=result;self.reo_event('submitted',result['app']+': '+result['status'])
  elif cmd in ('laya-setup','laya-check'):
   self.laya_setup.start(consent=request.get('consent')is True,check=cmd=='laya-check')
  elif cmd=='laya-load':
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop Mic and current reply before loading Laya CPU model; restart Mic after loading completes')
   self.laya_engine.load(consent=request.get('consent')is True)
  elif cmd=='laya-cancel':self.stop_laya();self.browser_pending=None
  elif cmd=='laya-mode':
   if request.get('consent')is not True:raise ValueError('Review local Laya disclosure first')
   self.laya_generation+=1;self.laya_enabled=True;self.laya_state={'busy':False,'status':'Enabled this session - load the inbuilt Laya engine; exact review still required','error':''}
  elif cmd=='laya-propose':self.start_laya(request.get('goal'))
  elif cmd=='laya-stop':self.stop_laya();self.browser_pending=None
  elif cmd=='browser-enable':self.enable_control(request.get('consent')is True)
  elif cmd.startswith('browser-'):
   self.laya_generation+=1
   if self.laya_state['busy']:self.laya_state={'busy':False,'status':'Proposal superseded by a browser command; nothing executed','error':''}
   if cmd=='browser-stop':
    self.news_speech.stop();self.news.cancel()
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
  elif cmd in ('embedding-check','embedding-setup'):self.search_setup.start(consent=request.get('consent')is True,check=cmd=='embedding-check')
  elif cmd=='embedding-stop':self.search_setup.stop();self.semantic_search.stop()
  elif cmd.startswith('vault-'):
   if cmd=='vault-preview':
    from .vault_voice import parse_voice as parse_vault
    proposal=parse_vault(request.get('text'))
    if not proposal:raise ValueError('Use obsidian search words or obsidian read Exact/Note.md')
    return self.execute(proposal)
   if cmd=='vault-semantic-stop':self.semantic_search.stop()
   elif cmd=='vault-connect':
    if request.get('consent') is not True:raise ValueError('Allow local vault access first')
    from .obsidian import Vault
    self.semantic_search.stop();self.vault=Vault(request.get('vault_folder',''));self.vault_results=[];self.vault_search={};self.vault_note=''
   elif cmd=='vault-disconnect':self.semantic_search.stop();self.vault=None;self.vault_results=[];self.vault_search={};self.vault_note=''
   else:
    if not self.vault:raise ValueError('Connect a local vault first')
    if cmd=='vault-semantic':
     if request.get('reviewed')!={'vault_folder':str(self.vault.root),'query':request.get('query')}:raise ValueError('Vault or query changed; review again')
     self.semantic_search.start(self.vault,request.get('query'),consent=request.get('consent')is True)
    elif cmd=='vault-search':
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
  elif cmd=='local-speed':
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice and wait for the reply before timing local inference')
   self.local_speed.start(consent=request.get('consent')is True)
  elif cmd=='local-speed-stop':self.local_speed.stop()
  elif cmd=='brain-check':self.brains.check(request.get('slot','local'),self.voice.notify)
  elif cmd=='brain-models':self.brains.list_models(request.get('slot'),self.voice.notify)
  elif cmd in ('turn-check','turn-setup'):self.turn_setup.start(consent=request.get('consent')is True,check=cmd=='turn-check')
  elif cmd=='turn-cancel':self.turn_setup.stop()
  elif cmd=='turn-mode':
   if self.voice.busy or self.voice.runtime is not None or self.turn_setup.busy:raise ValueError('Stop voice and setup before changing turn detection')
   if request.get('mode')not in ('vad','smart'):raise ValueError('Choose VAD or Smart Turn')
   if request['mode']=='smart':
    from .experimental.smart_turn import ready
    from .paths import data_root
    if request.get('consent')is not True or not ready(data_root()/'models'/'smart-turn.onnx'):raise ValueError('Review and verify Smart Turn first')
   self.voice.turn_mode=request['mode']
  elif cmd=='idle-activity':self.idle.activity()
  elif cmd=='news-speak':
   if not self.news.requested or not self.browser_enabled or not self.news.text_preview or not self.browser or self.browser.snapshot().get('state')!='ready':raise ValueError('Review captured news text on the current page first')
   if not self.setup.snapshot().get('ready'):raise ValueError('Install and verify local voice separately first')
   self.news_speech.play(self.news.text_preview,request.get('reviewed'),lambda:self.browser.snapshot().get('url')if self.browser and self.browser.snapshot().get('state')=='ready'else'',request.get('confirm')is True,self.voice.busy or self.voice.runtime is not None or self.game_speech.busy)
  elif cmd=='news-stop':self.news_speech.stop()
  elif cmd=='news-text':
   if not self.browser_enabled or not self.browser or not self.news.observed_url:raise ValueError('Open the reviewed news page first')
   if request.get('confirm')is not True or request.get('observed_url')!=self.news.observed_url:raise ValueError('Review exact observed page before capture')
   self.browser.submit('news-text',confirmed=True,expected_url=self.news.observed_url)
  elif cmd=='news-preview':self.news_speech.stop();self.news.preview(request.get('source_url'))
  elif cmd=='news-cancel':self.news_speech.stop();self.news.cancel()
  elif cmd=='news-open':
   if not self.browser_enabled or not self.browser:raise ValueError('Enable reviewed browser control first')
   proposal=self.news.confirm(request.get('reviewed'),request.get('confirm')is True)
   self.browser.submit('open',proposal['value'],confirmed=True)
  elif cmd=='canvas-open-preview':self.plan_pending={'note':'Brain of Brain.canvas','label':'Open visual multi-area Obsidian map','scope':'Visual open only, no external actions'}
  elif cmd=='canvas-open':
   if request.get('confirm')is not True or not self.plan_pending or request.get('reviewed')!=self.plan_pending or self.plan_pending['note']!='Brain of Brain.canvas':raise ValueError('Review exact canvas open')
   self.obsidian.open('Brain of Brain.canvas');self.plan_pending=None
  elif cmd=='calendar-preview':self.calendar.preview(request.get('event'))
  elif cmd=='calendar-save':self.calendar.save(request.get('reviewed'),request.get('confirm')is True);self.calendar_draft=None
  elif cmd=='calendar-cancel':self.calendar.cancel();self.calendar_open_pending=False;self.calendar_draft=None
  elif cmd=='calendar-open-preview':self.calendar_open_pending=True
  elif cmd=='calendar-open':
   if request.get('confirm')is not True or not self.calendar_open_pending:raise ValueError('Review local Obsidian calendar open')
   self.obsidian.open('Calendar/Home.md');self.calendar_open_pending=False
  elif cmd=='plan-preview':
   if not self.obsidian.enabled:raise ValueError('Create managed Brain of Brain vault first')
   self.plan_pending={'note':'Planning/Today.md','label':'Open Brain of Brain Today plan in Obsidian','scope':'Visual open only, no plan edits, tools or microphone'}
  elif cmd=='plan-open':
   if request.get('confirm')is not True or not self.plan_pending or request.get('reviewed')!=self.plan_pending:raise ValueError('Review exact planning-area visual open')
   if self.plan_pending['note']!='Planning/Today.md':raise ValueError('Only Today plan allowed')
   self.obsidian.open('Planning/Today.md');self.plan_pending=None
  elif cmd=='plan-cancel':self.plan_pending=None
  elif cmd=='agent-nodes':
   if request.get('enabled')is True:self.obsidian.connect_nodes(request.get('consent')is True)
   elif request.get('enabled')is False:self.obsidian.nodes_connected=False
   else:raise ValueError('Invalid agent node mode')
  elif cmd=='teammate-awareness':
   if request.get('enabled')is True:self.teammate_awareness.enable(request.get('consent')is True)
   elif request.get('enabled')is False:self.teammate_awareness.stop()
   else:raise ValueError('Invalid teammate awareness mode')
  elif cmd=='evolution-generate':
   if request.get('consent')is not True or self.evolution_busy:raise ValueError('Review local code proposal request; wait for current request')
   goal=request.get('goal')
   if not isinstance(goal,str)or not goal.strip()or len(goal)>1000:raise ValueError('Short goal required')
   self.evolution.cancel();self.evolution_cancel=threading.Event();cancel=self.evolution_cancel;self.evolution_busy=True;self.evolution_error='';self.evolution_result='';self.evolution.status='Local proposal thinking; nothing executing'
   def generate():
    try:self.evolution.generate(goal,self.brains.router('DEX'),cancel)
    except Exception as error:
     if not cancel.is_set():self.evolution_error=str(error)[:220];self.evolution.status='No valid proposal accepted; source unchanged'
    finally:self.evolution_busy=False
   threading.Thread(target=generate,daemon=True).start()
  elif cmd=='evolution-cancel':self.evolution_cancel.set();self.evolution.cancel();self.evolution_result=''
  elif cmd=='evolution-export':
   text=self.evolution.export_reviewed(request.get('reviewed'),request.get('confirm')is True)
   if not self.obsidian.enabled:raise ValueError('Create and review Brain of Brain vault first')
   p=self.obsidian.safe('Proposals/'+request['reviewed']['sha256']+'.md');p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_text(encoding='utf-8')!=text:raise ValueError('Edited proposal preserved; no overwrite')
   p.write_text(text,encoding='utf-8');self.evolution_result=str(p)
  elif cmd=='specialist-models':self.specialist_models=self.specialists.metadata()
  elif cmd=='specialist-configure':self.specialists.configure(request.get('assignments'),request.get('reviewed'),request.get('consent')is True)
  elif cmd=='specialist-run':self.specialist_result=self.specialists.run(request.get('task'),request.get('text'))
  elif cmd=='specialist-stop':self.specialists.stop()
  elif cmd=='game-windows':
   from .game_companion import windows
   self.game_windows=windows()
  elif cmd=='game-enable':
   from .game_companion import windows,LocalGameModel
   target=request.get('target');self.game_windows=windows()
   if target not in self.game_windows:raise ValueError('Selected window is unavailable; list windows again')
   if type(request.get('audio',False))is not bool:raise ValueError('Review game speech permission')
   if request.get('audio')is True and not self.setup.snapshot().get('ready'):raise ValueError('Set up and verify local speech assets before game audio')
   self.game_speech.stop()
   self.game.enable(target,request.get('reviewed'),LocalGameModel(request.get('vision_model'),gate=self.brains.local_gate),request.get('consent')is True,request.get('audio',False),request.get('export',False))
   self.idle.gaming=True;self.judge.gaming=True;self.idle.activity()
  elif cmd=='game-stop':
   self.game_speech.stop();self.game.stop();self.idle.gaming=False;self.judge.gaming=False
  elif cmd=='idle-mode':
   if type(request.get('enabled'))is not bool or type(request.get('audio',False))is not bool:raise ValueError('Invalid idle options')
   self.idle.stop()
   if request['enabled']:self.idle.enable(request.get('consent')is True,request.get('audio',False),request.get('strong',False))
  elif cmd=='agent-create':
   if self.voice.busy or self.voice.runtime is not None or self.judge.busy:raise ValueError('Stop voice and current work before creating an agent')
   row=self.agents.create(request.get('agent'),request.get('reviewed'),request.get('confirm')is True);self.agents.apply();self.voice.notify('status',row['name']+' joined the team. No microphone, model or tool started.')
  elif cmd=='team-dialogue':self.voice.dialogue(request.get('text'),self.brains,request.get('audio')is True,request.get('rounds',2))
  elif cmd=='team-round':self.voice.parallel_round(request.get('text'),self.brains,request.get('audio') is True)
  elif cmd=='chat':
   self.error='';self.warning='';self.response_diagnostics=[];text=request.get('text')
   if self.stop_intent(text):self.idle.stop();self.interrupt_conversation();return self.execute({'command':'status'})
   from .action_intent import parse as parse_action,goal as parse_goal
   from .desktop_actions import prepare
   action=bool(prepare(text)or parse_action(text)or parse_goal(text))
   if not isinstance(text,str)or not text.strip()or len(text)>2000:raise ValueError('Enter a message up to2000characters')
   if not action and (self.voice.busy or self.voice.runtime is not None):self.interrupt_conversation()
   if self.news.request(text)or self.teammate_query(text)or self.planning_action(text)or self.calendar_action(text)or self.desktop_action(text)or self.shared_action(text)or self.reo_action(text):self.messages.append({'name':'You','text':str(text)[:2000]});self.archive_dirty=True
   else:
    from .team_discussion import requested
    if requested(text):self.voice.dialogue(text,self.brains,request.get('audio')is True)
    else:self.voice.send_text(text,auto_pick=True)
  elif cmd=='select':
   self.judge.stop();self.voice.select(request.get('name'));self.voice.notify('status',self.voice.name+' selected. Mic OFF; press Talk to '+self.voice.name+' to start voice. Typed messages are text-only.')
  elif cmd=='pause':self.stop()
  elif cmd=='voice-endpoint':
   from .audio import ENDPOINT_FRAMES
   if self.voice.busy or self.voice.runtime is not None:raise ValueError('Stop voice before changing listening pause')
   if request.get('mode')not in ENDPOINT_FRAMES:raise ValueError('Choose a listening pause preset')
   self.voice.endpoint_mode=request['mode']
  elif cmd=='voice-engine':
   if self.voice.busy or self.voice.runtime is not None or self.setup.busy:raise ValueError('Stop voice and wait for model setup before changing speech engine')
   if request.get('engine')not in ('kokoro','kitten','pocket'):raise ValueError('Unknown speech engine')
   if self.voice_preferences:self.voice_preferences.save(request['engine'])
   self.game_speech.close();self.judge.close();self.voice.tts_engine=request['engine'];self.setup.select(request['engine'])
  elif cmd=='voice-setup':
   engine=getattr(self.voice,'tts_engine','kokoro')
   if request.get('reviewed_engine')!=engine:raise ValueError('Speech engine changed; review the download again')
   self.setup.start(consent=request.get('consent') is True,engine=engine)
  elif cmd=='voice-check':self.setup.start(check=True,engine=getattr(self.voice,'tts_engine','kokoro'))
  elif cmd=='voice-cancel':self.setup.stop()
  elif cmd=='voice-on':
   if request.get('consent') is not True:raise ValueError('Microphone consent required')
   if self.laya_engine.loading:raise ValueError('Wait for Laya CPU loading to finish before starting Mic')
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
   self.judge.stop();self.judge.gaming=request.get('gaming',False);self.idle.gaming=self.judge.gaming
   if request['enabled']:self.judge.enable(True,request.get('audio',False))
  elif cmd=='close':self.save_history(force=True);self.setup.stop();self.stop();self.judge.close();self.game_speech.close();self.news_speech.close();self.voice.close();self.closed=True
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
   elif kind=='dialogue-metrics'and isinstance(value,dict)and isinstance(value.get('profile'),str):
    metrics={k:(v if isinstance(v,(int,float))and not isinstance(v,bool)and 0<=v<3600 else None)for k,v in value.items()if k in ('first_text_s','generation_s','turn_s')}
    if metrics.get('turn_s')is not None:self.dialogue_metrics=(self.dialogue_metrics+[dict(metrics,profile=value['profile'][:40],audio=value.get('audio')is True,scope='Software turn timings; prefetched text may already be queued. Not audible latency.')])[-12:]
   elif kind=='response-diagnostics':self.response_diagnostics=value[-2:]
   elif kind=='error':
    if str(value).startswith('Reply reached the completion limit'):self.warning=str(value)[:300]
    else:self.error=str(value)[:300]
   elif kind=='voice-actor':self.voice.reply_actor=str(value)
   elif kind in ('state','status','proactive-status'):self.status=str(value)[:220]
   elif kind=='transcript':self.warning='';self.messages.append({'name':'You','text':str(value)[:2000]});self.archive_dirty=True
   elif kind=='game-comment':
    if value.get('generation')!=self.game.generation or not self.game.enabled:continue
    self.game_speech.play(value,self.voice.busy or self.voice.runtime is not None or self.judge.busy or self.idle.busy)
    self.messages.append({'name':'JARVIS','text':'Recent game frame: '+value['observed']+'\n'+value['comment'],'provider':'local','model':getattr(self.game.model,'model','local vision'),'cloud':False});self.archive_dirty=True
   elif kind in ('answer','proactive-answer'):
    self.archive_dirty=True
    row={'name':value.get('profile',self.voice.name),'text':value['text'][:4000],**{k:value[k]for k in ('provider','model','cloud','slot')if k in value}}
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
  return {'news':{**self.news.snapshot(),'speech':self.news_speech.snapshot()},'calendar':{**self.calendar.snapshot(),'open_pending':self.calendar_open_pending,'draft':self.calendar_draft},'planning':{'pending':self.plan_pending},'teammate_awareness':{'enabled':self.teammate_awareness.enabled,'state':self.teammate_state()},'evolution':{**self.evolution.snapshot(),'busy':self.evolution_busy,'error':self.evolution_error,'result':self.evolution_result},'specialists':{'models':list(self.specialist_models),'assignments':dict(self.specialists.assignments),'status':self.specialists.status,'result':self.specialist_result},'game':{**self.game.snapshot(),'speech_status':self.game_speech.status,'windows':list(self.game_windows)},'obsidian':self.obsidian.snapshot(),'desktop':{'enabled':self.desktop_enabled,'pending':self.desktop_pending,'result':self.desktop_result},'embedding_setup':self.search_setup.snapshot(),'semantic_search':self.semantic_search.snapshot(),'turn_mode':self.voice.turn_mode if getattr(self.voice,'turn_mode',None)in ('vad','smart')else'vad','turn_setup':self.turn_setup.snapshot(),'idle':self.idle.snapshot(),'agents':self.agents.snapshot(),'local_speed':self.local_speed.snapshot(),'reo_log':list(self.reo_log),'laya':dict(self.laya_state,enabled=self.laya_enabled,control_busy=self.control_busy,setup=self.laya_setup.snapshot(),engine=self.laya_engine.snapshot()),'browser':{'enabled':self.browser_enabled,'pending':self.browser_pending,'status':self.browser.snapshot()if self.browser else {'state':'off'}},'vault':{'connected':self.vault is not None,'folder':str(self.vault.root)if self.vault else'','results':self.vault_results,'search':self.vault_search,'note':self.vault_note},'history':self.history.list()if self.history else[],'chat_id':self.chat_id,'history_error':self.history_error,'history_limits':'Local plain-text storage, up to 50 chats and 200 messages per chat; oldest chats removed at the limit. Only selected chat recent context goes to APIs when you allow it. Delete does not remove external backups.','brains':self.brains.snapshot(),'caption':self.caption,'voice_metrics':self.voice_metrics,'dialogue_metrics':self.dialogue_metrics,'response_diagnostics':self.response_diagnostics,'expression':{'persona':actor,'state':state,'source':'live-runtime','viseme':None},'endpoint_mode':self.voice.endpoint_mode if isinstance(getattr(self.voice,'endpoint_mode',None),str)else'balanced','tts_engine':getattr(self.voice,'tts_engine','kokoro'),'selected':self.voice.name,'status':self.status,'error':self.error,'warning':self.warning,'busy':self.voice.busy,'voice_active':self.voice.runtime is not None and self.voice.runtime.enabled,'barge_in':self.barge_in,'voice_setup':self.setup.snapshot(),'voice_loading':self.voice.busy and self.status=='loading voice','messages':list(self.messages),'awareness':{**self.context.snapshot(),'vision':'on' if self.vision.enabled else 'off'},'judgment':{'enabled':self.judge.enabled,'audio':self.judge.audio,'gaming':self.judge.gaming,'waiting_reason':self.judge.waiting_reason(self.voice.busy or self.voice.runtime is not None)}}
 def save_history(self,force=False):
  if not self.history or not self.archive_dirty:return
  if not force and self.voice.busy and time.monotonic()-self.archive_saved_at<1:return
  try:self.history.save(self.chat_id,self.messages);self.archive_dirty=False;self.archive_saved_at=time.monotonic()
  except Exception:self.history_error='Chat could not be saved. Current session remains available; original archive preserved.'
 def close(self):self.save_history(force=True);self.setup.stop();self.stop();self.judge.close();self.game_speech.close();self.news_speech.close();self.voice.close()
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
