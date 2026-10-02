"""Phase2 workspace preview. Real UI navigation, no simulated worker completion.
Five planned profiles, not five running agents. Sensors/network stay off on launch.
"""
import tkinter as tk
from tkinter import messagebox,ttk
from .workspace_voice import WorkspaceVoice,VOICES
import queue,threading,time
BG='#101013';RAIL='#151518';PANEL='#19191e';LINE='#2b2b32';TEXT='#eeeeF1';MUTED='#96969f'
ROSTER=[('JARVIS','Team leader','#5bc8b2'),('NOVA','Secretary','#aa8be9'),('KAI','Researcher','#ec9d65'),('LYRA','Writer','#e287b5'),('DEX','Coder','#79a9e8')]
class Workspace:
 def __init__(self,root,controller=None):
  self.root=root;self.voice=controller or WorkspaceVoice();self.voice_status='off';self.caption='No conversation yet. Nothing is listening.';self.response='';self.setup_busy=False;self.download_cancel=threading.Event();root.title('JARVIS - Voice workspace / experimental');root.geometry(f'{min(1220,root.winfo_screenwidth()-30)}x{min(720,root.winfo_screenheight()-145)}+8+8');root.minsize(940,580);root.configure(bg=BG)
  from .experimental.session_awareness import SessionAwareness
  self.awareness=SessionAwareness(time.monotonic);self.timer_window=None;self.timer_quiet=False
  self.session_setup={'mic':False,'cloud':False,'free':False,'model':''};self.selected=0;self.view='Voice';self.mini=None;self.settings_window=None
  root.grid_columnconfigure(1,weight=1);root.grid_rowconfigure(0,weight=1)
  self.rail=tk.Frame(root,bg=RAIL,width=205,padx=16,pady=18);self.rail.grid(row=0,column=0,sticky='nsew');self.rail.grid_propagate(False)
  self.center=tk.Frame(root,bg=BG,padx=26,pady=18);self.center.grid(row=0,column=1,sticky='nsew')
  self.right=tk.Frame(root,bg=PANEL,width=260,padx=22,pady=22);self.right.grid(row=0,column=2,sticky='nsew');self.right.grid_propagate(False)
  self.build_rail();self.render()
  root.protocol('WM_DELETE_WINDOW',self.close);root.after(80,self.poll_voice)
 def label(self,parent,text,size=11,color=TEXT,bg=None,**kw):
  return tk.Label(parent,text=text,bg=bg or parent.cget('bg'),fg=color,font=('Segoe UI',size),anchor='w',justify='left',**kw)
 def button(self,parent,text,fn,bg=PANEL,color=TEXT,**kw):
  return tk.Button(parent,text=text,command=fn,bg=bg,fg=color,activebackground=LINE,activeforeground=TEXT,relief='flat',bd=0,cursor='hand2',font=('Segoe UI',10),padx=10,pady=6,**kw)
 def build_rail(self):
  for child in self.rail.winfo_children():child.destroy()
  self.label(self.rail,'J A R V I S',15).pack(anchor='w',pady=(0,4));self.label(self.rail,'VOICE WORKSPACE',8,MUTED).pack(anchor='w',pady=(0,15))
  self.label(self.rail,'YOUR TEAM  /  5 VOICES',8,MUTED).pack(anchor='w',pady=(0,12))
  for i,(name,role,color) in enumerate(ROSTER):
   row=tk.Frame(self.rail,bg=LINE if i==self.selected else RAIL,pady=2,padx=6);row.pack(fill='x',pady=3)
   c=tk.Canvas(row,width=30,height=30,bg=row.cget('bg'),highlightthickness=0);c.pack(side='left',padx=(0,8));c.create_oval(1,1,29,29,fill=color,outline='');c.create_text(15,15,text=name[0],fill=BG,font=('Segoe UI',11,'bold'))
   title=self.button(row,name+'\n'+role,lambda n=i:self.select(n),bg=row.cget('bg'),anchor='w',justify='left');title.pack(side='left',fill='x',expand=True)
   c.bind('<Button-1>',lambda e,n=i:self.select(n))
  self.label(self.rail,'Voice profiles. Background\nworkers are not enabled.',9,MUTED,wraplength=170).pack(anchor='w',pady=(10,8))
  self.button(self.rail,'Save notes + clear',self.save_notes).pack(fill='x',pady=4)
  self.button(self.rail,'Provider pool',self.provider_pool).pack(fill='x',pady=4)
  self.button(self.rail,'Session timer',self.session_timer).pack(fill='x',pady=4)
  self.button(self.rail,'Team Room',lambda:self.set_view('Team Room')).pack(fill='x',pady=4)
  self.button(self.rail,'Settings',self.settings).pack(side='bottom',fill='x',pady=4)
  self.button(self.rail,'Mini orb',self.open_mini).pack(side='bottom',fill='x',pady=4)
 def select(self,i):self.voice.select(ROSTER[i][0]);self.voice_status='off';self.selected=i;self.caption='No conversation yet. Nothing is listening.';self.response='';self.build_rail();self.render()
 def set_view(self,view):self.view=view;self.render()
 def render(self):
  for child in self.center.winfo_children():child.destroy()
  for child in self.right.winfo_children():child.destroy()
  name,role,color=ROSTER[self.selected]
  header=tk.Frame(self.center,bg=BG);header.pack(fill='x',pady=(0,14))
  self.label(header,name,17).pack(side='left');self.label(header,'  /  '+role,10,MUTED).pack(side='left')
  self.status_label=self.label(header,'VOICE / '+self.voice_status.upper(),8,color);self.status_label.pack(side='right')
  tabs=tk.Frame(self.center,bg=BG);tabs.pack(fill='x',pady=(0,14))
  for view in ['Voice','Chat','Team Room']:
   self.button(tabs,view,lambda v=view:self.set_view(v),bg=LINE if self.view==view else BG).pack(side='left',padx=(0,6))
  self.label(self.center,'Experimental voice - headphones required / no AEC or barge-in',9,MUTED,wraplength=530).pack(anchor='w')
  bar=tk.Frame(self.center,bg=BG);bar.pack(side='bottom',fill='x',pady=(10,0))
  for label,fn in [('Mic OFF',self.voice_setup),('Camera OFF',lambda:self.note('Camera','Camera is not implemented in this build. It remains OFF.')),('Privacy ON',lambda:self.note('Privacy','Audio stays local. No recordings, camera or screen capture. Groq is off unless you consent this session; if enabled, recognized text and shared recent team conversation are sent to Groq.')),('Pause all',self.pause)]:
   button=self.button(bar,label,fn,bg=PANEL);button.pack(side='left',padx=(0,5))
   if label=='Mic OFF':self.mic_button=button
  self.label(self.center,'Voice integration test build. Hardware acceptance pending. No agent workers.',8,MUTED,wraplength=630).pack(side='bottom',anchor='w',pady=(5,0))
  self.body=tk.Frame(self.center,bg=BG);self.body.pack(fill='both',expand=True,pady=12)
  if self.view=='Voice':self.voice_view(name,color)
  elif self.view=='Chat':self.chat_view()
  else:self.team_view()
  self.details(name,role,color)

 def voice_view(self,name,color):
  self.body.grid_columnconfigure(0,weight=1);self.body.grid_rowconfigure(0,weight=1)
  zone=tk.Frame(self.body,bg=BG);zone.grid(sticky='nsew');zone.grid_columnconfigure(0,weight=1);zone.grid_rowconfigure(0,weight=1)
  canvas=tk.Canvas(zone,width=180,height=180,bg=BG,highlightthickness=0);canvas.grid(row=0,column=0)
  for r,fill in [(80,'#1a2427'),(64,'#253c40'),(49,'#365c61'),(37,color)]:canvas.create_oval(90-r,90-r,90+r,90+r,fill=fill,outline='')
  for i,h in enumerate([12,24,38,51,32,19,42,57,35,22,12]):
   x=51+i*7;canvas.create_line(x,90-h/2,x,90+h/2,fill='#e4fff7',width=3)
  self.voice_state_label=self.label(zone,'Ready when you are.',18);self.voice_state_label.grid(row=1,column=0,pady=(0,8))
  self.label(zone,'Your assigned voice is ready for setup. Start the local brain.',10,MUTED,wraplength=490).grid(row=2,column=0,pady=(0,12))
  self.button(zone,'Set up voice',self.voice_setup,bg='#b6e7d9',color='#11231f').grid(row=3,column=0,pady=(0,12))
  card=tk.Frame(self.body,bg=PANEL,padx=16,pady=10);card.grid(row=1,column=0,sticky='ew',pady=(8,0))
  self.label(card,'LIVE CAPTIONS',8,MUTED).pack(anchor='w',pady=(0,8));self.caption_label=self.label(card,self.caption,11,wraplength=460);self.caption_label.pack(anchor='w')
 def chat_view(self):
  card=tk.Frame(self.body,bg=PANEL,padx=18,pady=18);card.pack(fill='x',pady=12)
  self.label(card,'A calm place for your conversations.',15,wraplength=460).pack(anchor='w');self.chat_caption=self.label(card,self.caption+'\n'+self.response,11,wraplength=460);self.chat_caption.pack(anchor='w');self.label(card,'Voice replies appear here for this session.\nTyped chat uses local LM Studio only. Mic stays OFF.',10,MUTED,wraplength=460).pack(anchor='w',pady=10)
  row=tk.Frame(self.body,bg=PANEL,padx=10,pady=10);row.pack(side='bottom',fill='x')
  entry=tk.Entry(row,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));entry.pack(side='left',fill='x',expand=True);self.chat_entry=entry;entry.bind('<Return>',lambda e:self.send_chat())
  self.button(row,'Send local',self.send_chat).pack(side='right')
 def send_chat(self):
  try:self.voice.send_text(self.chat_entry.get());self.chat_entry.delete(0,'end')
  except (ValueError,RuntimeError) as exc:self.note('Local text chat',str(exc))
 def team_view(self):
  self.label(self.body,'Team Room',17).pack(anchor='w',pady=(2,4));self.label(self.body,'Five distinct voices. No background workers are running.',10,MUTED,wraplength=460).pack(anchor='w',pady=(0,8))
  roster=tk.Frame(self.body,bg=PANEL,padx=8,pady=3);roster.pack(fill='x',pady=3)
  for i,(name,role,color) in enumerate(ROSTER):
   self.label(roster,name+' / '+role,9,color).grid(row=i//2,column=i%2,sticky='w',padx=(0,18),pady=1)
  row=tk.Frame(self.body,bg=PANEL);row.pack(fill='x',pady=(5,2))
  self.round_entry=tk.Entry(row,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',10));self.round_entry.pack(side='left',fill='x',expand=True,padx=5)
  self.button(row,'Start round',self.start_team_round).pack(side='right')
  choices=tk.Frame(self.body,bg=BG);choices.pack(fill='x')
  self.round_agents={}
  for name,role,color in ROSTER:
   var=tk.BooleanVar(value=name in ('NOVA','JARVIS'));self.round_agents[name]=var
   tk.Checkbutton(choices,text=name,variable=var,bg=BG,fg=color,selectcolor=LINE,activebackground=BG,font=('Segoe UI',8),padx=0,pady=0).pack(side='left')
  self.round_status_label=self.label(self.body,'Choose2-5profiles. Order: JARVIS, NOVA, KAI, LYRA, DEX. Text only.',8,MUTED,wraplength=480);self.round_status_label.pack(anchor='w')
  self.label(self.body,'SHARED SESSION CONVERSATION',8,MUTED).pack(anchor='w',pady=(10,4))
  transcript_frame=tk.Frame(self.body,bg=PANEL);transcript_frame.pack(fill='both',expand=True)
  transcript_scroll=tk.Scrollbar(transcript_frame);transcript_scroll.pack(side='right',fill='y')
  self.team_transcript=tk.Text(transcript_frame,yscrollcommand=transcript_scroll.set,bg=PANEL,fg=TEXT,relief='flat',font=('Segoe UI',10),wrap='word',height=7,padx=10,pady=8)
  self.team_transcript.pack(side='left',fill='both',expand=True);transcript_scroll.configure(command=self.team_transcript.yview);self.team_snapshot=None;self.update_team_transcript()
 def start_team_round(self):
  try:self.voice.team_round(self.round_entry.get(),tuple(name for name in self.round_agents if self.round_agents[name].get()));self.round_entry.delete(0,'end')
  except (ValueError,RuntimeError) as exc:self.note('Local team round',str(exc))
 def update_team_transcript(self):
  if not hasattr(self,'team_transcript') or not self.team_transcript.winfo_exists():return
  turns=self.voice.memory.snapshot()
  if turns==self.team_snapshot:return
  self.team_snapshot=turns;self.team_transcript.configure(state='normal');self.team_transcript.delete('1.0','end')
  self.team_transcript.insert('end','Conversation only. No screen/camera/game sensing.\nRAM only; Pause all and close clear this history.\n\n')
  if not turns:self.team_transcript.insert('end','No completed turns yet.')
  for name,user,answer in turns:self.team_transcript.insert('end','You: '+user+'\n'+name+': '+answer+'\n')
  self.team_transcript.configure(state='disabled');self.team_transcript.see('end')
 def details(self,name,role,color):
  avatar=tk.Canvas(self.right,width=60,height=60,bg=PANEL,highlightthickness=0);avatar.pack(anchor='w',pady=(0,8));avatar.create_oval(1,1,59,59,fill=color,outline='');avatar.create_text(30,30,text=name[0],fill=BG,font=('Segoe UI',24))
  self.label(self.right,'AGENT PROFILE',8,MUTED).pack(anchor='w',pady=(0,10));self.label(self.right,name,19).pack(anchor='w');self.label(self.right,role,11,MUTED).pack(anchor='w',pady=(4,24))
  descriptions={'JARVIS':'Coordinates the team and reports to you.','NOVA':'Reminders, schedule and daily briefing.','KAI':'Research, news and learning.','LYRA':'Writing, stories, scripts and subtitles.','DEX':'Coding, debugging and technical help.'}
  self.label(self.right,'INSTRUCTIONS',8,MUTED).pack(anchor='w',pady=(0,8));self.label(self.right,descriptions[name],10,wraplength=210).pack(anchor='w',pady=(0,15))
  for heading,value in [('VOICE',VOICES[name]),('BRAIN','Local default / not connected'),('TOOLS','No permissions enabled'),('NOTIFICATIONS','Off until configured')]:
   self.label(self.right,heading,8,MUTED).pack(anchor='w',pady=(0,7));self.label(self.right,value,10,wraplength=210).pack(anchor='w',pady=(0,12))
  self.button(self.right,'Edit profile',self.edit_profile).pack(fill='x',pady=5);self.label(self.right,'Voice profile, not a background worker.',8,MUTED,wraplength=210).pack(anchor='w',pady=14)
 def note(self,title,text):messagebox.showinfo(title,text,parent=self.root)
 def poll_voice(self):
  for _ in range(40):
   try:kind,value=self.voice.events.get_nowait()
   except queue.Empty:break
   if kind in ('state','status','error'):
    self.voice_status=str(value)[:180]
    if kind=='error':messagebox.showerror('Voice setup',str(value),parent=self.root)
   elif kind=='brain-check-result':
    callback,result=value
    callback(result)
   elif kind=='round-status':
    if hasattr(self,'round_status_label') and self.round_status_label.winfo_exists():self.round_status_label.configure(text=str(value))
   elif kind=='team-updated':self.update_team_transcript()
   elif kind=='transcript':self.caption='You: '+str(value)[:220]
   elif kind=='answer':self.response=ROSTER[self.selected][0]+': '+value['text'][:450]
  if self.status_label.winfo_exists():self.status_label.configure(text='VOICE / '+self.voice_status.upper()[:20])
  if self.mic_button.winfo_exists():self.mic_button.configure(text='Mic ON' if self.voice.runtime and self.voice.runtime.enabled else 'Mic OFF')
  if hasattr(self,'caption_label') and self.caption_label.winfo_exists():self.caption_label.configure(text=self.caption+'\n'+self.response)
  if hasattr(self,'chat_caption') and self.chat_caption.winfo_exists():self.chat_caption.configure(text=self.caption+'\n'+self.response)
  self.update_team_transcript()
  self.poll_timer()
  self.root.after(80,self.poll_voice)
 def session_timer(self):
  if self.timer_window and self.timer_window.winfo_exists():self.timer_window.lift();return
  win=tk.Toplevel(self.root);self.timer_window=win;win.title('JARVIS - Local session timer');win.geometry('520x420');win.configure(bg=PANEL)
  frame=tk.Frame(win,bg=PANEL,padx=20,pady=16);frame.pack(fill='both',expand=True)
  self.label(frame,'Local session timer',18).pack(anchor='w')
  self.label(frame,'You declare the activity. No screen/camera/game detection.\nText suggestions only; no microphone, audio or cloud.',10,MUTED,wraplength=470).pack(anchor='w',pady=10)
  self.label(frame,'Activity you are starting',10).pack(anchor='w')
  activity=tk.StringVar(value='gaming');ttk.Combobox(frame,textvariable=activity,values=('gaming','working','watching videos'),state='readonly').pack(anchor='w',pady=5)
  self.label(frame,'Reminder interval (15-180 minutes)',10).pack(anchor='w')
  interval=tk.StringVar(value='30');tk.Spinbox(frame,from_=15,to=180,textvariable=interval,width=8).pack(anchor='w',pady=5)
  consent=tk.BooleanVar(value=False);tk.Checkbutton(frame,text='Allow local text break reminders for this session',variable=consent,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL).pack(anchor='w',pady=5)
  quiet=tk.BooleanVar(value=self.timer_quiet)
  def quiet_change():self.timer_quiet=quiet.get()
  tk.Checkbutton(frame,text='Quiet: defer reminders',variable=quiet,command=quiet_change,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL).pack(anchor='w')
  self.timer_status=self.label(frame,'OFF. Nothing is watching you.',10,MUTED,wraplength=470);self.timer_status.pack(anchor='w',pady=10)
  def start():
   try:self.awareness.start(activity.get(),consent.get(),int(interval.get()));self.timer_status.configure(text='ON: user-declared '+activity.get()+'. Every '+interval.get()+' minutes. Local text only.')
   except (ValueError,TypeError) as exc:self.note('Session timer',str(exc))
  def stop():self.awareness.stop();self.timer_status.configure(text='OFF. Session timer cleared.')
  row=tk.Frame(frame,bg=PANEL);row.pack(anchor='w');self.button(row,'Start timer',start).pack(side='left');self.button(row,'Stop',stop).pack(side='left',padx=8)
  self.timer_start=start;self.timer_stop=stop;self.timer_consent=consent;self.timer_interval=interval;self.timer_activity=activity
  def close():self.awareness.stop();win.destroy()
  win.protocol('WM_DELETE_WINDOW',close)
 def poll_timer(self):
  if not self.awareness.enabled:return
  hidden=self.root.state() in ('withdrawn','iconic')
  nudge=self.awareness.poll(quiet=self.timer_quiet or hidden,busy=self.voice.busy or self.voice.runtime is not None)
  if nudge and self.timer_window and self.timer_window.winfo_exists():self.timer_status.configure(text=nudge.text)
 def voice_setup(self):
  win=tk.Toplevel(self.root);win.title('JARVIS - Voice setup');win.geometry('680x670');win.configure(bg=PANEL);win.transient(self.root)
  frame=tk.Frame(win,bg=PANEL,padx=24,pady=12);frame.pack(fill='both',expand=True)
  self.label(frame,'Voice setup / '+VOICES[ROSTER[self.selected][0]],17).pack(anchor='w')
  self.label(frame,'Microphone starts OFF. Headphones required. Half-duplex only.\nNo echo cancellation or barge-in. Physical acceptance is pending.',10,MUTED,wraplength=610).pack(anchor='w',pady=10)
  mic=tk.BooleanVar(value=self.session_setup['mic']);cloud=tk.BooleanVar(value=self.session_setup['cloud']);free=tk.BooleanVar(value=self.session_setup['free'])
  def check(text,var):tk.Checkbutton(frame,text=text,variable=var,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL,activeforeground=TEXT,wraplength=605,anchor='w',justify='left').pack(anchor='w',pady=4)
  check('Allow microphone for this session (headphones connected)',mic)
  check('Use Groq this session: send recognized text + shared recent team conversation, not audio',cloud)
  check('I checked my Groq account billing page: it is on the Free plan',free)
  self.label(frame,'Setup choices are remembered across profiles until Pause all or app close.',9,MUTED,wraplength=605).pack(anchor='w')
  self.label(frame,'Groq model: Automatic (active production chat model)',10,wraplength=605).pack(anchor='w',pady=(8,4))
  self.label(frame,'No model to paste. Selection happens only after session consent.\nModel access does not prove billing status.',9,MUTED,wraplength=605).pack(anchor='w')
  advanced=tk.BooleanVar(value=False);locked=tk.StringVar(value='')
  extra=tk.Frame(frame,bg=PANEL)
  model=tk.Entry(extra,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat')
  lock_status=self.label(extra,'Optional: paste a model ID, then press Enter to lock.',9,MUTED,wraplength=605)
  model.pack(fill='x',ipady=4);lock_status.pack(anchor='w')
  def lock(event=None):
   value=model.get().strip()
   if not value or len(value)>200 or not value.isascii() or any(not(c.isalnum() or c in '-_./') for c in value):
    lock_status.configure(text='Enter a valid model ID to lock.');return
   locked.set(value);model.configure(state='disabled');lock_status.configure(text='Locked: '+value)
  def unlock():
   locked.set('');model.configure(state='normal');lock_status.configure(text='Unlocked. Press Enter to lock; otherwise Automatic is used.')
  model.bind('<Return>',lock);self.button(extra,'Unlock / use Automatic',unlock).pack(anchor='w',pady=2)
  def toggle():
   if advanced.get():extra.pack(fill='x',after=advanced_button)
   else:unlock();extra.pack_forget()
  advanced_button=tk.Checkbutton(frame,text='Optional manual model override',variable=advanced,command=toggle,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL,activeforeground=TEXT)
  advanced_button.pack(anchor='w',pady=4)
  self.manual_model_entry=model;self.manual_model_lock=lock;self.manual_model_toggle=advanced_button
  self.manual_model_status=lock_status;self.session_mic_var=mic
  if self.session_setup['model']:
   advanced_button.invoke();model.insert(0,self.session_setup['model']);lock()

  self.label(frame,'Local default: LM Studio, one loaded model, server on port 1234.\nGroq key: Settings > Usage & Billing. No paid tier is permitted.',10,MUTED,wraplength=605).pack(anchor='w',pady=5)
  def enable():
   try:
    self.voice.pool_config=None
    self.voice.start(mic.get(),cloud.get(),locked.get(),free.get())
    from .experimental.session_awareness import SessionAwareness
  self.awareness=SessionAwareness(time.monotonic);self.timer_window=None;self.timer_quiet=False
  self.session_setup={'mic':mic.get(),'cloud':cloud.get(),'free':free.get(),'model':locked.get()}
    win.destroy()
   except Exception as exc:messagebox.showerror('Cannot start voice',str(exc),parent=win)
  check_status=self.label(frame,'No text test run yet. This test does not speak or use your microphone.',9,MUTED,wraplength=605)
  test_pending=[False]
  def checked(result):
   test_pending[0]=False
   if not win.winfo_exists():return
   test_button.configure(state='normal')
   if result.get('ok'):
    text='Connected: '+result['model']+'\nReply: '+result['reply']+'\nFirst answer text: '+format(result['first_text_s'],'.2f')+'s. Text only, not audible latency.'
    check_status.configure(text=text,fg='#b6e7d9');messagebox.showinfo('Groq text test succeeded',text,parent=win)
   else:
    check_status.configure(text='Failed: '+result['error'],fg='#efabab');messagebox.showerror('Groq text test failed',result['error'],parent=win)
  def check_brain():
   if not cloud.get() or not free.get():messagebox.showerror('Groq consent','Tick session Groq consent and Free-plan confirmation first.',parent=win);return
   if test_pending[0]:return
   self.session_setup.update(cloud=cloud.get(),free=free.get(),model=locked.get())
   test_pending[0]=True;test_button.configure(state='disabled');check_status.configure(text='Testing Groq: looking up model, then waiting for one text reply...',fg=MUTED)
   selected_model=locked.get()
   def run():
    try:
     from .brain_check import check_groq
     result=check_groq(selected_model,True,True)
     self.voice.notify('brain-check-result',(checked,dict(ok=True,**result)))
    except Exception as exc:
     from .groq_models import GroqCheckError
     text=str(exc) if isinstance(exc,GroqCheckError) else 'Groq connection check failed. Run GROQ-DIAG.cmd for sanitized error codes. No paid fallback.'
     self.voice.notify('brain-check-result',(checked,{'ok':False,'error':text}))
   threading.Thread(target=run,daemon=True).start()
  test_button=self.button(frame,'Test Groq text connection (sends greeting)',check_brain);test_button.pack(anchor='w',pady=4)
  check_status.pack(anchor='w',pady=2)
  self.groq_test_button=test_button;self.groq_test_status=check_status;self.groq_test_finished=checked
  self.groq_cloud_consent=cloud;self.groq_free_confirmation=free
  def download():
   if self.setup_busy:return
   if not messagebox.askyesno('Download models','Check existing cached models, then download only missing verified speech models and all five voices (roughly500MB if missing)? No audio is uploaded.',parent=win):return
   self.setup_busy=True;self.download_cancel.clear();download_button.configure(state='disabled')
   progress=tk.Toplevel(self.root);progress.title('JARVIS - Model downloads');progress.geometry('620x300');progress.configure(bg=PANEL);progress.transient(self.root)
   pane=tk.Frame(progress,bg=PANEL,padx=24,pady=24);pane.pack(fill='both',expand=True)
   self.label(pane,'Speech models and five voices',17).pack(anchor='w')
   state_label=self.label(pane,'Starting: checking cached files and checksums...',11,wraplength=560);state_label.pack(anchor='w',pady=12)
   meter=ttk.Progressbar(pane,mode='indeterminate');meter.pack(fill='x',pady=4);meter.start(80)
   self.label(pane,'Activity meter, not overall percent. Bytes are for the current file.\nVerified cached models are reused. Partial downloads can resume.',9,MUTED,wraplength=560).pack(anchor='w',pady=8)
   state={'text':'Starting: checking cached files and checksums...','done':False,'ok':False};guard=threading.Lock()
   def update_text(text):
    with guard:state['text']=text
   def report(name,received):update_text('Downloading '+name+'\n'+format(received/1048576,'.2f')+' MiB received in this file. Checking checksum before install.')
   def cancel():
    if state['done']:progress.destroy();return
    self.download_cancel.set();update_text('Cancelling... waiting for the current bounded network read.\nVerified files stay; partial downloads are kept for retry.');cancel_button.configure(state='disabled')
   cancel_button=self.button(pane,'Cancel download',cancel);cancel_button.pack(anchor='e',pady=8)
   progress.protocol('WM_DELETE_WINDOW',cancel)
   self.model_download_window=progress;self.model_download_label=state_label;self.model_download_meter=meter
   def poll():
    if not progress.winfo_exists():return
    with guard:values=dict(state)
    state_label.configure(text=values['text'],fg='#b6e7d9' if values['done'] and values['ok'] else TEXT)
    if values['done']:
     meter.stop();cancel_button.configure(text='Close',state='normal')
     if win.winfo_exists():download_button.configure(state='normal')
     return
    progress.after(100,poll)
   def run():
    try:
     from .paths import ensure_layout
     from . import models,voice_assets
     cache=ensure_layout()/'models';models.download(cache,consent=True,notify=report,cancel=self.download_cancel)
     if self.download_cancel.is_set():raise RuntimeError('cancelled')
     update_text('Checking speech assets complete. Checking cached voice models...')
     voice_assets.download(cache/'voices',consent=True,notify=report,cancel=self.download_cancel)
     if self.download_cancel.is_set():raise RuntimeError('cancelled')
     update_text('Ready: all speech models and five voices are checksum-verified.\nCached files were reused where possible. Close this window, then Enable voice with headphones.')
     with guard:state['ok']=True
    except Exception:
     update_text('Cancelled. Verified files kept; retry resumes eligible partial downloads.' if self.download_cancel.is_set() else 'Download failed. Existing verified files kept. Check connection, then retry.\nNo unverified file was installed.')
    finally:
     self.setup_busy=False
     with guard:state['done']=True
   progress.after(100,poll);threading.Thread(target=run,daemon=True).start()
  self.start_model_download=download
  row=tk.Frame(frame,bg=PANEL);row.pack(fill='x',pady=12)
  download_button=self.button(row,'Download models',download);download_button.pack(side='left',padx=4);self.model_download_button=download_button
  self.button(row,'Enable voice',enable,bg='#b6e7d9',color='#11231f').pack(side='left',padx=4);self.button(row,'Cancel',win.destroy).pack(side='right')
 def pause(self):
  self.awareness.stop()
  if self.timer_window and self.timer_window.winfo_exists():self.timer_status.configure(text="OFF. Pause all cleared the session timer.")
  from .experimental.session_awareness import SessionAwareness
  self.awareness=SessionAwareness(time.monotonic);self.timer_window=None;self.timer_quiet=False
  self.session_setup={'mic':False,'cloud':False,'free':False,'model':''}
  self.download_cancel.set();self.voice.pause();self.voice.memory.clear();self.voice.pool_config=None;self.voice_status='off'
  if self.mini and self.mini.winfo_exists():self.mini.title('JARVIS - Mini orb / OFF')
 def settings(self):
  if self.settings_window and self.settings_window.winfo_exists():self.settings_window.lift();return
  win=tk.Toplevel(self.root);self.settings_window=win;win.title('JARVIS - Settings preview');win.geometry('660x440');win.configure(bg=PANEL);win.transient(self.root)
  nav=tk.Frame(win,bg=RAIL,padx=15,pady=20,width=175);nav.pack(side='left',fill='y');content=tk.Frame(win,bg=PANEL,padx=28,pady=22);content.pack(side='left',fill='both',expand=True)
  def page(tab):
   for x in content.winfo_children():x.destroy()
   self.label(content,tab,19).pack(anchor='w',pady=(0,12))
   texts={'General':'Dark workspace preview\nFive planned profiles\nStartup: OFF\nAuto-update: not enabled','Computer':'Microphone: OFF\nCamera: OFF\nScreen capture: OFF\nNo device permission is requested here.','Usage & Billing':'No paid providers or billing setup.\nGroq requires verified Free-tier status.\nAPI keys must use Windows Credential Manager.','Voice':'JARVIS: am_michael\nNOVA: af_heart\nKAI: am_liam\nLYRA: af_sky\nDEX: am_fenrir\nHeadphone half-duplex. Hardware acceptance pending.'}
   self.label(content,texts[tab],11,wraplength=400).pack(anchor='w')
   if tab=='Usage & Billing':
    self.button(content,'Manage Groq API key',self.groq_key).pack(anchor='w',pady=10)
   self.label(content,'Microphone and cloud consent are session-only.\nBackground workers are not enabled.',9,MUTED,wraplength=400).pack(anchor='w',pady=18)
  for tab in ['General','Computer','Usage & Billing','Voice']:self.button(nav,tab,lambda t=tab:page(t),bg=RAIL).pack(fill='x',pady=4)
  page('General')
 def groq_key(self,provider='groq'):
  win=tk.Toplevel(self.root);win.title(provider+' - secure key onboarding');win.geometry('620x360');win.configure(bg=PANEL);win.transient(self.root)
  panel=tk.Frame(win,bg=PANEL,padx=24,pady=22);panel.pack(fill='both',expand=True)
  self.label(panel,provider+' API key',18).pack(anchor='w')
  self.label(panel,'Stored only in Windows Credential Manager. Never in config or logs.\nAdding a key does not enable cloud calls or prove a Free plan.\nCheck your provider account billing before enabling cloud.',10,MUTED,wraplength=560).pack(anchor='w',pady=12)
  secret=tk.Entry(panel,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat');secret.pack(fill='x',ipady=7)
  status=self.label(panel,'Paste a key. It stays visible here until this window closes.\nStored keys are never read back into this field.',9,MUTED,wraplength=560);status.pack(anchor='w',pady=10)
  def saved_state(prefix=''):
   try:
    from .security import WindowsCredentials
    meta=WindowsCredentials().status(provider)
    if meta['present']:
     status.configure(text=prefix+'Saved key present in Windows Credential Manager. No re-paste needed.\nLast saved: '+str(meta.get('saved_at') or 'time unavailable')+'. Stored key is not displayed.')
    else:status.configure(text='No saved key. Paste a key, then Save securely.')
   except Exception:status.configure(text='Saved-key state unavailable. Check Windows Credential Manager. No plaintext fallback.')
  saved_state()
  def save():
   try:
    from .security import WindowsCredentials
    WindowsCredentials().set(provider,secret.get().strip());saved_state('Saved securely. ')
   except Exception:status.configure(text='Not saved: secure storage failed. No plaintext fallback was used.')
  def delete():
   try:
    from .security import WindowsCredentials
    WindowsCredentials().delete(provider);secret.delete(0,'end');status.configure(text='Groq key removed.')
   except Exception:status.configure(text='Key removal failed. Check Windows Credential Manager.')
  self.groq_key_entry=secret;self.groq_key_status=status;self.groq_key_save=save
  def edited(event=None):status.configure(text='Edited, not saved. Click Save securely.')
  secret.bind('<KeyRelease>',edited)
  row=tk.Frame(panel,bg=PANEL);row.pack(fill='x')
  self.button(row,'Save securely',save).pack(side='left',padx=4);self.button(row,'Remove key',delete).pack(side='left',padx=4);self.button(row,'Close',win.destroy).pack(side='right')
 def edit_profile(self):
  win=tk.Toplevel(self.root);win.title('JARVIS - Profile preview');win.geometry('560x500');win.configure(bg=PANEL);win.transient(self.root);panel=tk.Frame(win,bg=PANEL,padx=28,pady=25);panel.pack(fill='both',expand=True)
  self.label(panel,'Agent profile',19).pack(anchor='w',pady=(0,15))
  for field,value in [('Name',ROSTER[self.selected][0]),('Role',ROSTER[self.selected][1]),('Voice',VOICES[ROSTER[self.selected][0]]),('Allowed tools','None enabled')]:
   self.label(panel,field,9,MUTED).pack(anchor='w',pady=(7,5));e=tk.Entry(panel,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));e.insert(0,value);e.pack(fill='x',ipady=7)
  self.label(panel,'Preview form only. Agent creation and saving arrive in Phase3.',9,MUTED,wraplength=490).pack(anchor='w',pady=20)
  self.button(panel,'Close',win.destroy).pack(anchor='e')
 def save_notes(self):
  from tkinter import filedialog
  if not self.voice.memory.messages():self.note('Session notes','No completed conversation to save.');return
  self.voice.pause();self.voice_status='off'
  directory=filedialog.askdirectory(title='Save private JARVIS notes (Markdown) before clearing context',parent=self.root)
  if not directory:return
  try:
   from .session_notes import checkpoint
   path=checkpoint(self.voice.memory,directory);self.caption='Conversation saved locally. Shared context cleared.';self.response='';self.note('Session notes','Saved local conversation and extractive recap:\n'+str(path)+'\nContext cleared only after successful save. Voice remains OFF. This does not change LM Studio server cache.')
  except Exception:self.note('Session notes','Save failed. Shared conversation was not cleared. Check folder permissions and free space.')
 def provider_pool(self):
  from .provider_pool import Slot,ProviderPool,SLOT_IDS,KINDS
  win=tk.Toplevel(self.root);win.title('JARVIS - Account pool / session');win.geometry('910x620+20+20');win.configure(bg=PANEL)
  panel=tk.Frame(win,bg=PANEL,padx=18,pady=10);panel.pack(fill='both',expand=True)
  self.label(panel,'Five account slots / per-profile route',18).pack(anchor='w')
  self.label(panel,'Your own legitimate accounts only. Keys do not multiply project quotas. No automatic calls.\nCloud sends recognized text + shared recent team conversation. Confirm Free access for every cloud slot.\nNIM developer access is for prototyping. Gemini Free content may be used to improve Google products.\nSettings below are RAM-only for this app session. Keys stay in Windows Credential Manager.',9,MUTED,wraplength=870).pack(anchor='w',pady=8)
  rows=[];existing=self.voice.pool_config[0].slots if self.voice.pool_config else {}
  for sid in SLOT_IDS:
   row=tk.Frame(panel,bg=PANEL);row.pack(fill='x',pady=1);self.label(row,sid,10).pack(side='left',padx=3)
   old=existing.get(sid);kind=tk.StringVar(value=old.provider if old else 'local');ttk.Combobox(row,textvariable=kind,values=KINDS,state='readonly',width=8).pack(side='left',padx=4)
   model=tk.Entry(row,bg=LINE,fg=TEXT,insertbackground=TEXT,width=27);model.pack(side='left',padx=4)
   if old:model.insert(0,old.model)
   enabled=tk.BooleanVar(value=old is not None);consent=tk.BooleanVar();free=tk.BooleanVar()
   for title,var in [('Use',enabled),('Share context',consent),('Free account',free)]:tk.Checkbutton(row,text=title,variable=var,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL).pack(side='left')
   self.button(row,'Key',lambda k=kind,i=sid:self.groq_key(k.get()+'/'+i) if k.get()!='local' else self.note('Local','LM Studio needs no API key.')).pack(side='right')
   rows.append((sid,kind,model,enabled,consent,free))
  self.label(panel,'Route order for each profile (comma-separated slots, e.g. slot1,slot3). Blank = unconfigured.',10,MUTED,wraplength=870).pack(anchor='w',pady=(6,3))
  routes={}
  for name,role,color in ROSTER:
   row=tk.Frame(panel,bg=PANEL);row.pack(fill='x',pady=2);self.label(row,name,10,color,width=10).pack(side='left');entry=tk.Entry(row,bg=LINE,fg=TEXT,insertbackground=TEXT);entry.pack(side='left',fill='x',expand=True)
   if self.voice.pool_config:entry.insert(0,','.join(self.voice.pool_config[0].routes.get(name,())))
   routes[name]=entry
  mic=tk.BooleanVar();tk.Checkbutton(panel,text='Allow microphone for this session (headphones; no AEC/barge-in)',variable=mic,bg=PANEL,fg=TEXT,selectcolor=LINE).pack(anchor='w',pady=8)
  status=self.label(panel,'Models are exact IDs from your provider account. No keys, models or billing tested yet.',9,MUTED,wraplength=860);status.pack(anchor='w')
  def apply(start=False):
   try:
    slots=[Slot(sid,kind.get(),model.get().strip()) for sid,kind,model,on,consent,free in rows if on.get()]
    route={name:tuple(i.strip() for i in entry.get().split(',') if i.strip()) for name,entry in routes.items() if entry.get().strip()}
    pool=ProviderPool(slots,route);consented=tuple(sid for sid,kind,model,on,c,f in rows if on.get() and c.get());confirmed=tuple(sid for sid,kind,model,on,c,f in rows if on.get() and f.get())
    if start:
     if not mic.get():raise ValueError('Microphone session consent required.')
     from .security import WindowsCredentials
     pool.router(ROSTER[self.selected][0],WindowsCredentials(),consented,confirmed)
    self.voice.pause();self.voice.pool_config=(pool,consented,confirmed)
    if start:self.voice.start(True,any(pool.slots[i].provider!='local' for i in pool.routes[ROSTER[self.selected][0]]),'',True);win.destroy()
    else:status.configure(text='Routes saved for this session. Nothing started. Cloud consent is per slot; Enable checks it.')
   except Exception as exc:status.configure(text='Not started: '+str(exc)[:220])
  row=tk.Frame(panel,bg=PANEL);row.pack(fill='x',pady=10)
  self.button(row,'Save session routes',apply).pack(side='left');self.button(row,'Enable selected profile',lambda:apply(True),bg='#b6e7d9',color='#11231f').pack(side='left',padx=5)
  def legacy():self.voice.pause();self.voice.pool_config=None;win.destroy()
  self.button(row,'Use original local/Groq setup',legacy).pack(side='right')
  self.pool_rows=rows;self.pool_routes=routes;self.pool_apply=apply;self.pool_status=status;self.pool_window=win
 def open_mini(self):
  if self.mini and self.mini.winfo_exists():self.mini.lift();return
  from .orbs import OrbOverlay
  self.orb_overlay=OrbOverlay(self.root,lambda:(ROSTER[self.selected][0],self.voice_status),self.select,self.pause)
  self.mini=self.orb_overlay.window
  self.root.withdraw()
 def close(self):self.awareness.stop();self.download_cancel.set();self.voice.close();self.root.destroy()
def main():root=tk.Tk();Workspace(root);root.mainloop()
