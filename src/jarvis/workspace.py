"""Phase2 workspace preview. Real UI navigation, no simulated worker completion.
Five planned profiles, not five running agents. Sensors/network stay off on launch.
"""
import tkinter as tk
from tkinter import messagebox
BG='#101013';RAIL='#151518';PANEL='#19191e';LINE='#2b2b32';TEXT='#eeeeF1';MUTED='#96969f'
ROSTER=[('JARVIS','Team leader','#5bc8b2'),('NOVA','Secretary','#aa8be9'),('KAI','Researcher','#ec9d65'),('LYRA','Writer','#e287b5'),('DEX','Coder','#79a9e8')]
class Workspace:
 def __init__(self,root):
  self.root=root;root.title('JARVIS - Workspace preview');root.geometry('1220x780');root.minsize(980,680);root.configure(bg=BG)
  self.selected=0;self.view='Voice';self.mini=None;self.settings_window=None
  root.grid_columnconfigure(1,weight=1);root.grid_rowconfigure(0,weight=1)
  self.rail=tk.Frame(root,bg=RAIL,width=205,padx=16,pady=18);self.rail.grid(row=0,column=0,sticky='nsew');self.rail.grid_propagate(False)
  self.center=tk.Frame(root,bg=BG,padx=26,pady=18);self.center.grid(row=0,column=1,sticky='nsew')
  self.right=tk.Frame(root,bg=PANEL,width=260,padx=22,pady=22);self.right.grid(row=0,column=2,sticky='nsew');self.right.grid_propagate(False)
  self.build_rail();self.render()
  root.protocol('WM_DELETE_WINDOW',self.close)
 def label(self,parent,text,size=11,color=TEXT,bg=None,**kw):
  return tk.Label(parent,text=text,bg=bg or parent.cget('bg'),fg=color,font=('Segoe UI',size),anchor='w',justify='left',**kw)
 def button(self,parent,text,fn,bg=PANEL,color=TEXT,**kw):
  return tk.Button(parent,text=text,command=fn,bg=bg,fg=color,activebackground=LINE,activeforeground=TEXT,relief='flat',bd=0,cursor='hand2',font=('Segoe UI',10),padx=12,pady=8,**kw)
 def build_rail(self):
  for child in self.rail.winfo_children():child.destroy()
  self.label(self.rail,'J A R V I S',15).pack(anchor='w',pady=(0,4));self.label(self.rail,'VOICE WORKSPACE',8,MUTED).pack(anchor='w',pady=(0,24))
  self.label(self.rail,'YOUR TEAM  /  5 PLANNED',8,MUTED).pack(anchor='w',pady=(0,12))
  for i,(name,role,color) in enumerate(ROSTER):
   row=tk.Frame(self.rail,bg=LINE if i==self.selected else RAIL,pady=9,padx=6);row.pack(fill='x',pady=3)
   c=tk.Canvas(row,width=30,height=30,bg=row.cget('bg'),highlightthickness=0);c.pack(side='left',padx=(0,8));c.create_oval(1,1,29,29,fill=color,outline='');c.create_text(15,15,text=name[0],fill=BG,font=('Segoe UI',11,'bold'))
   title=self.button(row,name+'\n'+role,lambda n=i:self.select(n),bg=row.cget('bg'),anchor='w',justify='left');title.pack(side='left',fill='x',expand=True)
   c.bind('<Button-1>',lambda e,n=i:self.select(n))
  self.label(self.rail,'Profiles only. Workers arrive\nin Phase3.',9,MUTED,wraplength=170).pack(anchor='w',pady=(18,14))
  self.button(self.rail,'Team Room',lambda:self.set_view('Team Room')).pack(fill='x',pady=4)
  self.button(self.rail,'Settings',self.settings).pack(side='bottom',fill='x',pady=4)
  self.button(self.rail,'Mini orb',self.open_mini).pack(side='bottom',fill='x',pady=4)
 def select(self,i):self.selected=i;self.build_rail();self.render()
 def set_view(self,view):self.view=view;self.render()
 def render(self):
  for child in self.center.winfo_children():child.destroy()
  for child in self.right.winfo_children():child.destroy()
  name,role,color=ROSTER[self.selected]
  header=tk.Frame(self.center,bg=BG);header.pack(fill='x',pady=(0,14))
  self.label(header,name,17).pack(side='left');self.label(header,'  /  '+role,10,MUTED).pack(side='left')
  self.label(header,'LOCAL  /  OFF',8,color).pack(side='right')
  tabs=tk.Frame(self.center,bg=BG);tabs.pack(fill='x',pady=(0,14))
  for view in ['Voice','Chat','Team Room']:
   self.button(tabs,view,lambda v=view:self.set_view(v),bg=LINE if self.view==view else BG).pack(side='left',padx=(0,6))
  self.label(self.center,'Preview build - microphone and camera OFF',9,MUTED).pack(anchor='w')
  self.body=tk.Frame(self.center,bg=BG);self.body.pack(fill='both',expand=True,pady=12)
  if self.view=='Voice':self.voice_view(name,color)
  elif self.view=='Chat':self.chat_view()
  else:self.team_view()
  self.details(name,role,color)
  bar=tk.Frame(self.center,bg=BG);bar.pack(fill='x',pady=(10,0))
  for label,fn in [('Mic OFF',self.voice_setup),('Camera OFF',lambda:self.note('Camera','Camera is not implemented in this build. It remains OFF.')),('Privacy ON',lambda:self.note('Privacy','No recordings, camera, screen capture or cloud calls run from this workspace.')),('Pause all',self.pause)]:
   self.button(bar,label,fn,bg=PANEL).pack(side='left',padx=(0,5))
  self.label(self.center,'Software preview only. Voice core and agent workers are still being built.',8,MUTED,wraplength=630).pack(anchor='w',pady=(10,0))
 def voice_view(self,name,color):
  self.body.grid_columnconfigure(0,weight=1);self.body.grid_rowconfigure(0,weight=1)
  zone=tk.Frame(self.body,bg=BG);zone.grid(sticky='nsew');zone.grid_columnconfigure(0,weight=1);zone.grid_rowconfigure(0,weight=1)
  canvas=tk.Canvas(zone,width=260,height=260,bg=BG,highlightthickness=0);canvas.grid(row=0,column=0)
  for r,fill in [(114,'#1a2427'),(91,'#253c40'),(70,'#365c61'),(51,color)]:canvas.create_oval(130-r,130-r,130+r,130+r,fill=fill,outline='')
  for i,h in enumerate([12,24,38,51,32,19,42,57,35,22,12]):
   x=91+i*7;canvas.create_line(x,130-h/2,x,130+h/2,fill='#e4fff7',width=3)
  self.label(zone,'Ready when you are.',18).grid(row=1,column=0,pady=(0,8))
  self.label(zone,'Choose your voice, then set up the local brain.',10,MUTED,wraplength=490).grid(row=2,column=0,pady=(0,20))
  self.button(zone,'Set up voice',self.voice_setup,bg='#b6e7d9',color='#11231f').grid(row=3,column=0,pady=(0,20))
  card=tk.Frame(self.body,bg=PANEL,padx=16,pady=14);card.grid(row=1,column=0,sticky='ew',pady=(18,0))
  self.label(card,'LIVE CAPTIONS',8,MUTED).pack(anchor='w',pady=(0,8));self.label(card,'No conversation yet. Nothing is listening.',11,wraplength=520).pack(anchor='w')
 def chat_view(self):
  card=tk.Frame(self.body,bg=PANEL,padx=18,pady=18);card.pack(fill='x',pady=12)
  self.label(card,'A calm place for your conversations.',15,wraplength=500).pack(anchor='w');self.label(card,'Chat history will appear here once the voice runtime is connected.\nThis preview does not send messages to a model.',10,MUTED,wraplength=500).pack(anchor='w',pady=10)
  row=tk.Frame(self.body,bg=PANEL,padx=10,pady=10);row.pack(side='bottom',fill='x')
  entry=tk.Entry(row,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));entry.pack(side='left',fill='x',expand=True);entry.insert(0,'Type a message...')
  self.button(row,'Send',lambda:self.note('Not connected','Chat sending is not connected yet. Nothing was sent.')).pack(side='right')
 def team_view(self):
  self.label(self.body,'Team Room',19).pack(anchor='w',pady=(8,4));self.label(self.body,'Five planned roles. No background workers are running.',10,MUTED,wraplength=520).pack(anchor='w',pady=(0,18))
  for name,role,color in ROSTER:
   card=tk.Frame(self.body,bg=PANEL,padx=15,pady=13);card.pack(fill='x',pady=5)
   self.label(card,name,11,color).pack(side='left');self.label(card,'  '+role,10,MUTED).pack(side='left');self.label(card,'NOT CONFIGURED',8,MUTED).pack(side='right')
 def details(self,name,role,color):
  avatar=tk.Canvas(self.right,width=60,height=60,bg=PANEL,highlightthickness=0);avatar.pack(anchor='w',pady=(0,18));avatar.create_oval(1,1,59,59,fill=color,outline='');avatar.create_text(30,30,text=name[0],fill=BG,font=('Segoe UI',24))
  self.label(self.right,'AGENT PROFILE',8,MUTED).pack(anchor='w',pady=(0,10));self.label(self.right,name,19).pack(anchor='w');self.label(self.right,role,11,MUTED).pack(anchor='w',pady=(4,24))
  descriptions={'JARVIS':'Coordinates the team and reports to you.','NOVA':'Reminders, schedule and daily briefing.','KAI':'Research, news and learning.','LYRA':'Writing, stories, scripts and subtitles.','DEX':'Coding, debugging and technical help.'}
  self.label(self.right,'INSTRUCTIONS',8,MUTED).pack(anchor='w',pady=(0,8));self.label(self.right,descriptions[name],10,wraplength=210).pack(anchor='w',pady=(0,24))
  for heading,value in [('VOICE','Waiting for your selection'),('BRAIN','Local default / not connected'),('TOOLS','No permissions enabled'),('NOTIFICATIONS','Off until configured')]:
   self.label(self.right,heading,8,MUTED).pack(anchor='w',pady=(0,7));self.label(self.right,value,10,wraplength=210).pack(anchor='w',pady=(0,20))
  self.button(self.right,'Edit profile',self.edit_profile).pack(fill='x',pady=5);self.label(self.right,'Planned profile, not a running agent.',8,MUTED,wraplength=210).pack(anchor='w',pady=14)
 def note(self,title,text):messagebox.showinfo(title,text,parent=self.root)
 def voice_setup(self):self.note('Voice setup','Voice core is still in testing. The separate diagnostic voice preview uses session consent, headphones and LM Studio. This workspace does not start a microphone or download models.')
 def pause(self):
  if self.mini:self.mini.title('JARVIS - Mini orb / OFF')
  self.note('Paused','All workspace sensors remain OFF. No background agent jobs are running.')
 def settings(self):
  if self.settings_window and self.settings_window.winfo_exists():self.settings_window.lift();return
  win=tk.Toplevel(self.root);self.settings_window=win;win.title('JARVIS - Settings preview');win.geometry('660x440');win.configure(bg=PANEL);win.transient(self.root)
  nav=tk.Frame(win,bg=RAIL,padx=15,pady=20,width=175);nav.pack(side='left',fill='y');content=tk.Frame(win,bg=PANEL,padx=28,pady=22);content.pack(side='left',fill='both',expand=True)
  def page(tab):
   for x in content.winfo_children():x.destroy()
   self.label(content,tab,19).pack(anchor='w',pady=(0,20))
   texts={'General':'Dark workspace preview\nFive planned profiles\nStartup: OFF\nAuto-update: not enabled','Computer':'Microphone: OFF\nCamera: OFF\nScreen capture: OFF\nNo device permission is requested here.','Usage & Billing':'No paid providers or billing setup.\nGroq requires verified Free-tier status.\nAPI keys must use Windows Credential Manager.','Voice':'Two favorites selected in listening tests.\nRemaining voices await your choice.\nNo voice is assigned in this preview.'}
   self.label(content,texts[tab],11,wraplength=400).pack(anchor='w');self.label(content,'Settings shown here are status only.\nOnboarding and persistent controls remain in progress.',9,MUTED,wraplength=400).pack(anchor='w',pady=25)
  for tab in ['General','Computer','Usage & Billing','Voice']:self.button(nav,tab,lambda t=tab:page(t),bg=RAIL).pack(fill='x',pady=4)
  page('General')
 def edit_profile(self):
  win=tk.Toplevel(self.root);win.title('JARVIS - Profile preview');win.geometry('560x500');win.configure(bg=PANEL);win.transient(self.root);panel=tk.Frame(win,bg=PANEL,padx=28,pady=25);panel.pack(fill='both',expand=True)
  self.label(panel,'Agent profile',19).pack(anchor='w',pady=(0,15))
  for field,value in [('Name',ROSTER[self.selected][0]),('Role',ROSTER[self.selected][1]),('Voice','Awaiting selection'),('Allowed tools','None enabled')]:
   self.label(panel,field,9,MUTED).pack(anchor='w',pady=(7,5));e=tk.Entry(panel,bg=LINE,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11));e.insert(0,value);e.pack(fill='x',ipady=7)
  self.label(panel,'Preview form only. Agent creation and saving arrive in Phase3.',9,MUTED,wraplength=490).pack(anchor='w',pady=20)
  self.button(panel,'Close',win.destroy).pack(anchor='e')
 def open_mini(self):
  if self.mini and self.mini.winfo_exists():self.mini.lift();return
  win=tk.Toplevel(self.root);self.mini=win;win.title('JARVIS - Mini orb / OFF');win.geometry('200x190');win.attributes('-topmost',True);win.configure(bg=BG)
  c=tk.Canvas(win,width=180,height=130,bg=BG,highlightthickness=0);c.pack();c.create_oval(48,24,132,108,fill='#365c61',outline='#76cab3',width=2);c.create_text(90,65,text='OFF',fill=TEXT,font=('Segoe UI',13))
  self.button(win,'Open workspace',self.root.lift).pack()
 def close(self):self.root.destroy()
def main():root=tk.Tk();Workspace(root);root.mainloop()
