"""Experimental Phase1 harness, not Phase2 UI. No microphone or network on launch."""
import queue,threading
from pathlib import Path
from .paths import ensure_layout
from . import models

def main():
 import tkinter as tk
 from tkinter import ttk,messagebox
 root=tk.Tk();root.title('JARVIS - Voice core preview');root.geometry('920x680');root.minsize(800,620)
 root.configure(bg='#101217');panel=tk.Frame(root,bg='#101217',padx=30,pady=24);panel.pack(fill='both',expand=True)
 events=queue.Queue();runtime=[None];busy=[False];cancel=threading.Event();cache=ensure_layout()/'models'
 def notify(kind,value):events.put((kind,value))
 def text(value,size=12,color='#b5c1ce'):
  w=tk.Label(panel,text=value,bg='#101217',fg=color,font=('Segoe UI',size),justify='left',anchor='w',wraplength=850);w.pack(anchor='w',pady=(0,10));return w
 text('JARVIS / VOICE CORE PREVIEW',22,'#d0eedc')
 text('Experimental Phase1. Mic starts OFF. Headphones required. No camera or recordings.')
 text('Local Whisper base + Silero VAD + LM Studio + installed Windows voice.\nNo cloud providers are enabled in this preview. No echo cancellation or barge-in yet.')
 state=text('OFF - microphone released',15,'#d0eedc')
 row=tk.Frame(panel,bg='#101217');row.pack(fill='x',pady=(5,12))
 consent=tk.BooleanVar(value=False)
 tk.Checkbutton(row,text='Allow continuous mic for this session (headphones)',variable=consent,bg='#101217',fg='#edf0f5',selectcolor='#243831',activebackground='#101217',activeforeground='#edf0f5').pack(side='left')
 def pause():
  cancel.set()
  if runtime[0]:runtime[0].pause()
  state.configure(text='OFF - microphone released')
 def download():
  if busy[0]:return
  if not messagebox.askyesno('Download local models','Download about 145 MB of local speech models from Hugging Face and the Silero GitHub repository? Models are hash-verified and saved in your Windows user folder. No microphone audio is uploaded.'):
   return
  busy[0]=True;cancel.clear();state.configure(text='Downloading verified local models...')
  def run():
   try:models.download(cache,consent=True,cancel=cancel);notify('status','Models ready. Start LM Studio and press Enable voice.')
   except Exception as e:notify('error',str(e))
   finally:busy[0]=False
  threading.Thread(target=run,daemon=True).start()
 def enable():
  if busy[0]:return
  if not consent.get():state.configure(text='Tick session microphone consent first.');return
  busy[0]=True;cancel.clear();state.configure(text='Checking models and local brain...')
  def run():
   try:
    if not models.ready(cache):raise RuntimeError('Local models missing. Press Download models first.')
    from .providers import local_models,configured
    from .router import BrainRouter
    from .audio import SileroVad
    from .speech import WhisperSTT,SapiSpeaker
    from .runtime import VoiceRuntime
    ids=local_models()
    if len(ids)!=1:raise RuntimeError('Load exactly one chat model in LM Studio for this preview. Multiple models need the later settings picker.')
    if runtime[0] is None:runtime[0]=VoiceRuntime(SileroVad(cache/'silero.onnx'),WhisperSTT(cache/'whisper-base'),BrainRouter([configured('local',ids[0])]),SapiSpeaker(),notify)
    if cancel.is_set():return
    runtime[0].enable(consent=True)
   except Exception as e:notify('error',str(e))
   finally:busy[0]=False
  threading.Thread(target=run,daemon=True).start()
 actions=tk.Frame(panel,bg='#101217');actions.pack(fill='x',pady=(0,16))
 for title,action in [('Download models',download),('Enable voice',enable),('Pause all',pause)]:
  tk.Button(actions,text=title,command=action,bg='#d0eedc',fg='#14251e',relief='flat',padx=18,pady=10).pack(side='left',padx=(0,12))
 text('Start LM Studio: load one model -> Developer -> start local server on port 1234.\nThis harness only chats. It cannot send, delete, book, browse or change Windows settings.',11)
 transcript=text('You: -',13,'#edf0f5');answer=text('JARVIS: -',13,'#edf0f5')
 brain=text('Brain: local only / speech: Windows installed voice',11)
 text('Try: "Hello, who are you?" or "Tell me a short joke."\nPause all releases the mic and stops voice playback. Closing releases everything.\nOffline chat works only if LM Studio is already running a local model.',11)
 def poll():
  for _ in range(30):
   try:kind,value=events.get_nowait()
   except queue.Empty:break
   if kind in ('state','status','error'):state.configure(text=str(value)[:350])
   elif kind=='transcript':transcript.configure(text='You: '+str(value)[:600])
   elif kind=='answer':
    answer.configure(text='JARVIS: '+value['text'][:900]);brain.configure(text='Brain: '+value.get('provider','local')+' / speech: Windows installed voice')
  root.after(80,poll)
 def close():
  pause()
  if runtime[0]:runtime[0].close()
  root.destroy()
 root.protocol('WM_DELETE_WINDOW',close);root.after(80,poll);root.mainloop()
