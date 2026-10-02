"""Phase2 workspace preview. Real UI navigation, no simulated worker completion.
Five planned profiles, not five running agents. Sensors/network stay off on launch.
"""
import tkinter as tk
from tkinter import messagebox
from .workspace_voice import WorkspaceVoice,VOICES
import queue,threading
BG='#101013';RAIL='#151518';PANEL='#19191e';LINE='#2b2b32';TEXT='#eeeeF1';MUTED='#96969f'
ROSTER=[('JARVIS','Team leader','#5bc8b2'),('NOVA','Secretary','#aa8be9'),('KAI','Researcher','#ec9d65'),('LYRA','Writer','#e287b5'),('DEX','Coder','#79a9e8')]
class Workspace:
 def __init__(self,root,controller=None):
  self.root=root;self.voice=controller or WorkspaceVoice();self.voice_status='off';self.caption='No conversation yet. Nothing is listening.';self.response='';self.setup_busy=False;self.download_cancel=threading.Event();root.title('JARVIS - Voice workspace / experimental');root.geometry(f'{min(1220,root.winfo_screenwidth()-30)}x{min(720,root.winfo_screenheight()-145)}+8+8');root.minsize(940,580);root.configure(bg=BG)
  self.selected=0;self.view='Voice';self.mini=None;self.settings_window=None
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
  for label,fn in [('Mic OFF',self.voice_setup),('Camera OFF',lambda:self.note('Camera','Camera is not implemented in this build. It remains OFF.')),('Privacy ON',lambda:self.note('Privacy','Audio stays local. No recordings, camera or screen capture. Groq is off unless you consent this session; if enabled, recognized text is sent to Groq.')),('Pause all',self.pause)]:
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
  self.label(card,'LIVE CAPTIONS',8,MUTED).pack(anchor='w',pady=(0,8));self.caption_label=self.label(card,self.caption,11,wraplength=520);self.caption_label.pack(anchor='w')
 def chat_view(self):
  card=tk.Frame(self.body,bg=PANEL,padx=18,pady=18);card.pack(fill='x',pady=12)
  self.label(card,'A calm place for your conversations.',15,wraplength=500).pack(anchor='w');self.chat_caption=self.label(card,self.caption+'\n'+self.response,11,wraplength=500);self.chat_caption.pack(anchor='w');self.label(card,'Voice replies appear here for this session.\nTyped chat is not connected yet.',10,MUTED,wraplength=500).pack(anchor='w',pady=10)
  row=tk.Frame(self.body,bg=PANEL,padx=10,pady=10);row.pack(side='bottom',fill='x')
  entry=tk.Entry(row,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));entry.pack(side='left',fill='x',expand=True);entry.insert(0,'Type a message...')
  self.button(row,'Send',lambda:self.note('Not connected','Chat sending is not connected yet. Nothing was sent.')).pack(side='right')
 def team_view(self):
  self.label(self.body,'Team Room',17).pack(anchor='w',pady=(2,4));self.label(self.body,'Five distinct voices. No background workers are running.',10,MUTED,wraplength=520).pack(anchor='w',pady=(0,8))
  for name,role,color in ROSTER:
   card=tk.Frame(self.body,bg=PANEL,padx=12,pady=7);card.pack(fill='x',pady=3)
   self.label(card,name,11,color).pack(side='left');self.label(card,'  '+role,10,MUTED).pack(side='left');self.label(card,VOICES[name],8,MUTED).pack(side='right')
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
   elif kind=='transcript':self.caption='You: '+str(value)[:220]
   elif kind=='answer':self.response=ROSTER[self.selected][0]+': '+value['text'][:450]
  if self.status_label.winfo_exists():self.status_label.configure(text='VOICE / '+self.voice_status.upper()[:20])
  if self.mic_button.winfo_exists():self.mic_button.configure(text='Mic ON' if self.voice.runtime and self.voice.runtime.enabled else 'Mic OFF')
  if hasattr(self,'caption_label') and self.caption_label.winfo_exists():self.caption_label.configure(text=self.caption+'\n'+self.response)
  if hasattr(self,'chat_caption') and self.chat_caption.winfo_exists():self.chat_caption.configure(text=self.caption+'\n'+self.response)
  self.root.after(80,self.poll_voice)
 def voice_setup(self):
  win=tk.Toplevel(self.root);win.title('JARVIS - Voice setup');win.geometry('680x540');win.configure(bg=PANEL);win.transient(self.root)
  frame=tk.Frame(win,bg=PANEL,padx=24,pady=18);frame.pack(fill='both',expand=True)
  self.label(frame,'Voice setup / '+VOICES[ROSTER[self.selected][0]],17).pack(anchor='w')
  self.label(frame,'Microphone starts OFF. Headphones required. Half-duplex only.\nNo echo cancellation or barge-in. Physical acceptance is pending.',10,MUTED,wraplength=610).pack(anchor='w',pady=10)
  mic=tk.BooleanVar(value=False);cloud=tk.BooleanVar(value=False);free=tk.BooleanVar(value=False)
  def check(text,var):tk.Checkbutton(frame,text=text,variable=var,bg=PANEL,fg=TEXT,selectcolor=LINE,activebackground=PANEL,activeforeground=TEXT,wraplength=605,anchor='w',justify='left').pack(anchor='w',pady=4)
  check('Allow microphone for this session (headphones connected)',mic)
  check('Use Groq this session: send recognized text to Groq, not audio',cloud)
  check('I checked my Groq account billing page: it is on the Free plan',free)
  self.label(frame,'Groq model ID (required only when Groq is selected)',9,MUTED).pack(anchor='w',pady=(10,4))
  model=tk.Entry(frame,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat');model.pack(fill='x',ipady=5)
  self.label(frame,'Local default: LM Studio, one loaded model, server on port 1234.\nGroq key: Settings > Usage & Billing. No paid tier is permitted.',10,MUTED,wraplength=605).pack(anchor='w',pady=10)
  def enable():
   try:self.voice.start(mic.get(),cloud.get(),model.get(),free.get());win.destroy()
   except Exception as exc:messagebox.showerror('Cannot start voice',str(exc),parent=win)
  def download():
   if self.setup_busy:return
   if not messagebox.askyesno('Download models','Download roughly 500 MB of verified local speech models and all five voices? No audio is uploaded. Native frontend must also be installed by the build.',parent=win):return
   self.setup_busy=True;self.download_cancel.clear()
   def run():
    try:
     from .paths import ensure_layout
     from . import models,voice_assets
     cache=ensure_layout()/'models';models.download(cache,consent=True,cancel=self.download_cancel);voice_assets.download(cache/'voices',consent=True,cancel=self.download_cancel)
     self.voice.notify('status','Models downloaded. Native frontend and LM Studio must be ready.')
    except Exception:self.voice.notify('error','Model download failed or was cancelled. Retry to resume.')
    finally:self.setup_busy=False
   threading.Thread(target=run,daemon=True).start()
  row=tk.Frame(frame,bg=PANEL);row.pack(fill='x',pady=12)
  self.button(row,'Download models',download).pack(side='left',padx=4);self.button(row,'Enable voice',enable,bg='#b6e7d9',color='#11231f').pack(side='left',padx=4);self.button(row,'Cancel',win.destroy).pack(side='right')
 def pause(self):
  self.download_cancel.set();self.voice.pause();self.voice_status='off'
  if self.mini:self.mini.title('JARVIS - Mini orb / OFF')
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
 def groq_key(self):
  win=tk.Toplevel(self.root);win.title('Groq - secure key onboarding');win.geometry('620x360');win.configure(bg=PANEL);win.transient(self.root)
  panel=tk.Frame(win,bg=PANEL,padx=24,pady=22);panel.pack(fill='both',expand=True)
  self.label(panel,'Groq API key',18).pack(anchor='w')
  self.label(panel,'Stored only in Windows Credential Manager. Never in config or logs.\nAdding a key does not enable cloud calls or prove a Free plan.\nCheck billing at console.groq.com before enabling Groq.',10,MUTED,wraplength=560).pack(anchor='w',pady=12)
  secret=tk.Entry(panel,show='*',bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat');secret.pack(fill='x',ipady=7)
  status=self.label(panel,'No key read or displayed here.',9,MUTED);status.pack(anchor='w',pady=10)
  def save():
   try:
    from .security import WindowsCredentials
    WindowsCredentials().set('groq',secret.get());secret.delete(0,'end');status.configure(text='Key saved securely. Cloud remains OFF until session consent.')
   except Exception:secret.delete(0,'end');status.configure(text='Secure storage failed. No plaintext fallback was used.')
  def delete():
   try:
    from .security import WindowsCredentials
    WindowsCredentials().delete('groq');secret.delete(0,'end');status.configure(text='Groq key removed.')
   except Exception:status.configure(text='Key removal failed. Check Windows Credential Manager.')
  row=tk.Frame(panel,bg=PANEL);row.pack(fill='x')
  self.button(row,'Save securely',save).pack(side='left',padx=4);self.button(row,'Remove key',delete).pack(side='left',padx=4);self.button(row,'Close',win.destroy).pack(side='right')
 def edit_profile(self):
  win=tk.Toplevel(self.root);win.title('JARVIS - Profile preview');win.geometry('560x500');win.configure(bg=PANEL);win.transient(self.root);panel=tk.Frame(win,bg=PANEL,padx=28,pady=25);panel.pack(fill='both',expand=True)
  self.label(panel,'Agent profile',19).pack(anchor='w',pady=(0,15))
  for field,value in [('Name',ROSTER[self.selected][0]),('Role',ROSTER[self.selected][1]),('Voice',VOICES[ROSTER[self.selected][0]]),('Allowed tools','None enabled')]:
   self.label(panel,field,9,MUTED).pack(anchor='w',pady=(7,5));e=tk.Entry(panel,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));e.insert(0,value);e.pack(fill='x',ipady=7)
  self.label(panel,'Preview form only. Agent creation and saving arrive in Phase3.',9,MUTED,wraplength=490).pack(anchor='w',pady=20)
  self.button(panel,'Close',win.destroy).pack(anchor='e')
 def open_mini(self):
  if self.mini and self.mini.winfo_exists():self.mini.lift();return
  win=tk.Toplevel(self.root);self.mini=win;win.title('JARVIS - Mini orb / OFF');win.geometry('200x190');win.attributes('-topmost',True);win.configure(bg=BG)
  c=tk.Canvas(win,width=180,height=130,bg=BG,highlightthickness=0);c.pack();c.create_oval(48,24,132,108,fill='#365c61',outline='#76cab3',width=2);c.create_text(90,65,text='OFF',fill=TEXT,font=('Segoe UI',13))
  self.button(win,'Open workspace',self.root.lift).pack()
 def close(self):self.download_cancel.set();self.voice.close();self.root.destroy()
def main():root=tk.Tk();Workspace(root);root.mainloop()
