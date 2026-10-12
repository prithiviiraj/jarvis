"""Opt-in modifier hold detector. No hook/injection or capture on construction.

Ctrl+Alt hold talks; Shift+Alt interrupts. Owner-proposed key mapping.
"""
import threading,time
class ShortcutEdges:
 def __init__(self,clock=time.monotonic,delay=.15):self.clock=clock;self.delay=delay;self.talk_since=None;self.talking=False;self.interrupt_down=False
 def feed(self,ctrl,alt,shift,win):
  if any(type(v)is not bool for v in (ctrl,alt,shift,win)):raise ValueError('Invalid modifier state')
  events=[];interrupt=shift and alt and not ctrl and not win;talk=ctrl and alt and not shift and not win
  if interrupt and not self.interrupt_down:events.append('interrupt')
  self.interrupt_down=interrupt
  if talk:
   if self.talk_since is None:self.talk_since=self.clock()
   if not self.talking and self.clock()-self.talk_since>=self.delay:self.talking=True;events.append('talk-start')
  else:
   if self.talking:events.append('talk-stop')
   self.talk_since=None;self.talking=False
  return events
class ModifierMonitor:
 def __init__(self,notify,read=None):self.notify=notify;self.read=read;self.cancel=threading.Event();self.worker=None;self.error='';self.enabled=False
 def start(self,consent=False):
  if consent is not True:raise ValueError('Enable the reviewed talk/interrupt shortcuts explicitly')
  if self.worker and self.worker.is_alive():raise ValueError('Shortcuts already running')
  read=self.read
  if read is None:
   import os
   if os.name!='nt':raise ValueError('Native modifier shortcuts require Windows')
   import ctypes
   user=ctypes.windll.user32
   read=lambda:(bool(user.GetAsyncKeyState(0x11)&0x8000),bool(user.GetAsyncKeyState(0x12)&0x8000),bool(user.GetAsyncKeyState(0x10)&0x8000),bool((user.GetAsyncKeyState(0x5B)|user.GetAsyncKeyState(0x5C))&0x8000))
  self.cancel=threading.Event();cancel=self.cancel;self.error='';self.enabled=True
  def run():
   edges=ShortcutEdges()
   try:
    while not cancel.is_set():
     for event in edges.feed(*read()):
      if not cancel.is_set():self.notify(event)
     cancel.wait(.025)
   except Exception as e:self.error=type(e).__name__
   finally:self.enabled=False
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def stop(self):self.cancel.set();self.enabled=False
 def snapshot(self):return{'enabled':self.enabled,'error':self.error,'mapping':{'talk':'Ctrl+Alt hold','interrupt':'Shift+Alt'},'scope':'Explicit session modifier monitor. Hold capture/release and interruption callbacks are local; physical Windows timing/audio unverified'}
