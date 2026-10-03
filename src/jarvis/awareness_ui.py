"""Local awareness controls. Never dispatches persona/model/API requests."""
import tkinter as tk,json,time
from .ui_theme import BG,PANEL,LINE,TEXT,MUTED
from .local_awareness import LocalContext,CameraWorker,foreground_app
class AwarenessPanel:
 def __init__(self,root):
  self.root=root;self.context=LocalContext();self.camera=CameraWorker(self.context);self.window=None;self.badge=None;self.title_allowed=False;self.last_app=0;self.app_error=False
 def open(self):
  if self.window and self.window.winfo_exists():self.window.lift();return
  self.window=tk.Toplevel(self.root);w=self.window;w.title('JARVIS - Local awareness');w.geometry('620x575');w.configure(bg=BG)
  f=tk.Frame(w,bg=BG,padx=20,pady=16);f.pack(fill='both',expand=True)
  tk.Label(f,text='Local awareness / foundation',bg=BG,fg=TEXT,font=('Segoe UI',17)).pack(anchor='w')
  tk.Label(f,text='Camera frames stay local and transient. No screen capture, model calls,\nautomatic speech, cloud upload or recordings in this phase.',bg=BG,fg=MUTED,justify='left').pack(anchor='w',pady=10)
  self.status=tk.Label(f,bg=BG,fg=TEXT,anchor='w');self.status.pack(fill='x',pady=5)
  row=tk.Frame(f,bg=BG);row.pack(fill='x')
  self.on=tk.Button(row,text='Enable local camera',command=self.start_camera,bg=PANEL,fg=TEXT);self.on.pack(side='left')
  tk.Button(row,text='Camera OFF',command=self.stop_camera,bg=PANEL,fg=TEXT).pack(side='left',padx=8)
  self.apps=tk.BooleanVar(value=self.context.apps);self.titles=tk.BooleanVar(value=self.title_allowed)
  tk.Checkbutton(f,text='Local foreground app (process name)',variable=self.apps,command=self.set_apps,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w',pady=(10,0))
  tk.Checkbutton(f,text='Include window title (may contain private text)',variable=self.titles,command=self.set_titles,bg=BG,fg=TEXT,selectcolor=LINE).pack(anchor='w')
  tk.Label(f,text='Presence means a detected face, not identity, sleep or attention.\nEvents are RAM-only context; persona decision dispatch is not enabled.',bg=BG,fg=MUTED,justify='left').pack(anchor='w',pady=10)
  self.preview=tk.Text(f,height=12,bg=PANEL,fg=TEXT,wrap='word',font=('Consolas',9));self.preview.pack(fill='both',expand=True)
  tk.Button(f,text='Stop all sensing + clear context',command=self.stop_all,bg=PANEL,fg=TEXT).pack(anchor='w',pady=10)
  w.protocol('WM_DELETE_WINDOW',self.close_panel);self.refresh()
 def start_camera(self):
  if not self.camera.stopped():return
  self.show_badge() # Visible BEFORE device acquisition, even while workspace is hidden.
  self.camera.start(consent=True)
 def stop_camera(self):self.camera.stop()
 def set_apps(self):
  self.context.set_apps(self.apps.get());self.app_error=False
  if self.context.apps:self.show_badge()
 def set_titles(self):
  self.title_allowed=self.titles.get();self.context.app=None;self.last_app=0
  if not self.title_allowed:
   with self.context.lock:self.context.events.clear()
 def show_badge(self):
  if self.badge and self.badge.winfo_exists():return
  self.badge=tk.Toplevel(self.root);self.badge.title('JARVIS sensing indicator');self.badge.geometry('375x67+30+115');self.badge.attributes('-topmost',True);self.badge.configure(bg=PANEL);self.badge.resizable(False,False)
  self.badge_label=tk.Label(self.badge,text='LOCAL SENSING / STARTING',bg=PANEL,fg=TEXT);self.badge_label.pack(side='left',padx=8)
  tk.Button(self.badge,text='OFF',command=self.stop_all,bg=LINE,fg=TEXT).pack(side='right',padx=8)
  self.badge.protocol('WM_DELETE_WINDOW',self.stop_all)
 def tick(self):
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
  self.preview.configure(state='normal');self.preview.delete('1.0','end');self.preview.insert('end',json.dumps(self.context.snapshot(),indent=2));self.preview.configure(state='disabled')
 def stop_all(self):
  self.camera.stop();self.context.clear();self.title_allowed=False
  if self.window and self.window.winfo_exists():self.apps.set(False);self.titles.set(False)
  # Keep badge while the device thread unwinds, so OFF is not falsely promised.
  if not self.camera.stopped():self.context.camera_state('stopping')
  self.refresh()
 def close_panel(self):self.stop_all();self.window.destroy();self.window=None
