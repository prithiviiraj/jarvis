"""Local awareness controls. Never dispatches persona/model/API requests."""
import tkinter as tk,json,time
from .ui_theme import BG,PANEL,LINE,TEXT,MUTED
from .local_awareness import LocalContext,CameraWorker,foreground_app
from .proactive import ProactiveJudge
class AwarenessPanel:
 def __init__(self,root,voice=None):
  self.root=root;self.voice=voice;self.context=LocalContext();self.camera=CameraWorker(self.context);self.window=None;self.badge=None;self.title_allowed=False;self.last_app=0;self.app_error=False
  from .workspace_voice import build_text_router,build_proactive_speaker
  self.judge=ProactiveJudge(self.context,build_text_router,self.notify,build_proactive_speaker)
  self.judgment_status='OFF';self.comment=''
 def notify(self,kind,value):
  if self.voice:self.voice.notify(kind,value)
 def open(self):
  if self.window and self.window.winfo_exists():self.window.lift();return
  self.window=tk.Toplevel(self.root);w=self.window;w.title('JARVIS - Local awareness');w.geometry('680x670');w.configure(bg=BG)
  f=tk.Frame(w,bg=BG,padx=20,pady=16);f.pack(fill='both',expand=True)
  tk.Label(f,text='Local awareness / foundation',bg=BG,fg=TEXT,font=('Segoe UI',17)).pack(anchor='w')
  tk.Label(f,text='Camera frames stay local and transient. No screen capture or\ncloud upload or recordings. Local persona judgment is separately opt-in.',bg=BG,fg=MUTED,justify='left').pack(anchor='w',pady=10)
  self.status=tk.Label(f,bg=BG,fg=TEXT,anchor='w');self.status.pack(fill='x',pady=5)
  row=tk.Frame(f,bg=BG);row.pack(fill='x')
  self.on=tk.Button(row,text='Enable local camera',command=self.start_camera,bg=PANEL,fg=TEXT);self.on.pack(side='left')
  tk.Button(row,text='Camera OFF',command=self.stop_camera,bg=PANEL,fg=TEXT).pack(side='left',padx=8)
  self.apps=tk.BooleanVar(value=self.context.apps);self.titles=tk.BooleanVar(value=self.title_allowed)
  tk.Checkbutton(f,text='Local foreground app (process name)',variable=self.apps,command=self.set_apps,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w',pady=(10,0))
  tk.Checkbutton(f,text='Include window title (may contain private text)',variable=self.titles,command=self.set_titles,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w')
  tk.Label(f,text='Presence means a detected face, not identity, sleep or attention.\nEvents are RAM-only context. Local judgment requires consent below.',bg=BG,fg=MUTED,justify='left').pack(anchor='w',pady=10)
  self.judge_consent=tk.BooleanVar(value=self.judge.enabled);self.audio_consent=tk.BooleanVar(value=self.judge.audio);self.gaming_var=tk.BooleanVar(value=self.judge.gaming)
  tk.Checkbutton(f,text='Allow local LM Studio persona to read app/presence context',variable=self.judge_consent,command=self.configure_judge,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w')
  tk.Checkbutton(f,text='Allow spontaneous JARVIS voice (headphones)',variable=self.audio_consent,command=self.configure_judge,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w')
  tk.Checkbutton(f,text='Gaming mode: suspend local model judgment',variable=self.gaming_var,command=self.configure_judge,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w')
  self.judge_label=tk.Label(f,text='OFF / local-only, quiet 00:00-07:00, max 12 requests/hour',bg=BG,fg=MUTED,wraplength=630,justify='left');self.judge_label.pack(anchor='w',pady=5)
  self.preview=tk.Text(f,height=8,bg=PANEL,fg=TEXT,wrap='word',font=('Consolas',9));self.preview.pack(fill='both',expand=True)
  tk.Button(f,text='Stop all sensing + clear context',command=self.stop_all,bg=PANEL,fg=TEXT).pack(anchor='w',pady=10)
  w.protocol('WM_DELETE_WINDOW',self.close_panel);self.refresh()
 def configure_judge(self):
  self.judge.stop();self.judge.gaming=self.gaming_var.get()
  if self.judge_consent.get():self.judge.enable(True,self.audio_consent.get())
  self.judgment_status='Local judgment ON' if self.judge.enabled else 'OFF'
 def start_camera(self):
  if not self.camera.stopped():return
  self.show_badge() # Visible BEFORE device acquisition, even while workspace is hidden.
  self.camera.start(consent=True)
 def stop_camera(self):
  self.judge.stop();self.camera.stop()
  with self.context.lock:
   self.context.presence='unknown';self.context.events.clear()
 def set_apps(self):
  self.judge.stop();self.context.set_apps(self.apps.get());self.app_error=False
  if self.judge_consent.get():self.judge.enable(True,self.audio_consent.get())
  if self.context.apps:self.show_badge()
 def set_titles(self):
  self.judge.stop();self.title_allowed=self.titles.get();self.last_app=0
  with self.context.lock:self.context.app=None
  if not self.title_allowed:
   with self.context.lock:self.context.events.clear()
  if self.judge_consent.get():self.judge.enable(True,self.audio_consent.get())
 def show_badge(self):
  if self.badge and self.badge.winfo_exists():return
  self.badge=tk.Toplevel(self.root);self.badge.title('JARVIS sensing indicator');self.badge.geometry('375x67+30+115');self.badge.attributes('-topmost',True);self.badge.configure(bg=PANEL);self.badge.resizable(False,False)
  self.badge_label=tk.Label(self.badge,text='LOCAL SENSING / STARTING',bg=PANEL,fg=TEXT);self.badge_label.pack(side='left',padx=8)
  tk.Button(self.badge,text='OFF',command=self.stop_all,bg=LINE,fg=TEXT).pack(side='right',padx=8)
  self.badge.protocol('WM_DELETE_WINDOW',self.stop_all)
 def tick(self):
  busy=bool(self.voice and (self.voice.busy or self.voice.runtime is not None))
  self.judge.conversation_busy=busy
  if busy and self.judge.busy:self.judge.stop()
  self.judge.poll(conversation_busy=busy)
  if self.context.apps and time.monotonic()-self.last_app>=1:
   self.last_app=time.monotonic()
   try:self.context.app_event(foreground_app(self.title_allowed));self.app_error=False
   except Exception:self.context.app_event(None);self.app_error=True
  active=self.context.camera!='off' or self.context.apps
  if active:self.show_badge()
  if self.badge and self.badge.winfo_exists():
   if active:self.badge_label.configure(text='CAM '+self.context.camera.upper()+' / APP '+('ERROR' if self.app_error else 'ON' if self.context.apps else 'OFF'))
   else:self.badge.destroy();self.badge=None
  self.refresh()
 def refresh(self):
  if not self.window or not self.window.winfo_exists():return
  self.status.configure(text='Camera: '+self.context.camera.upper()+' | Presence: '+self.context.presence.upper())
  self.on.configure(state='normal' if self.camera.stopped() else 'disabled')
  self.judge_label.configure(text=self.judgment_status+' / '+self.comment[:160]+'\nLocal only; quiet 00:00-07:00; 120s cooldown; max12 requests/hour')
  self.preview.configure(state='normal');self.preview.delete('1.0','end');self.preview.insert('end',json.dumps(self.context.snapshot(),indent=2));self.preview.configure(state='disabled')
 def stop_all(self):
  self.judge.stop();self.camera.stop();self.context.clear();self.title_allowed=False
  if self.window and self.window.winfo_exists():self.apps.set(False);self.titles.set(False);self.judge_consent.set(False);self.audio_consent.set(False)
  # Keep badge while the device thread unwinds, so OFF is not falsely promised.
  if not self.camera.stopped():self.context.camera_state('stopping')
  self.refresh()
 def close_panel(self):self.stop_all();self.window.destroy();self.window=None
