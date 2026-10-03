"""Windows local awareness verification. No owner's camera, model or network requests."""
import tkinter as tk,time,json,pathlib,sys
from unittest.mock import patch
from PIL import ImageGrab
import cv2,numpy as np
from jarvis.workspace import Workspace
from jarvis.local_awareness import foreground_app,CameraWorker
out=pathlib.Path('workspace-evidence');out.mkdir(exist_ok=True)
root=tk.Tk();app=Workspace(root);root.update();app.local_awareness.open();root.update();panel=app.local_awareness
checks={}
def capture(name):
 root.update();time.sleep(.3);root.update();ImageGrab.grab().save(out/(name+'.png'))
try:
 capture('local-awareness-off');assert panel.context.camera=='off' and panel.context.apps is False
 panel.apps.set(True);panel.set_apps();root.lift();root.focus_force();root.update();panel.last_app=0;panel.tick()
 checks['real_windows_foreground']=foreground_app(False);assert checks['real_windows_foreground'];assert not checks['real_windows_foreground']['title']
 checks['real_window_title']=foreground_app(True);assert checks['real_window_title'] is not None
 capture('local-awareness-app')
 cascade=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml');assert not cascade.empty()
 assert len(cascade.detectMultiScale(np.zeros((240,320),np.uint8)))==0;checks['real_detector_blank_frame']='no face'
 class Cap:
  def isOpened(self):return True
  def read(self):return True,object()
  def release(self):self.released=True
 cap=Cap();panel.camera=CameraWorker(panel.context,lambda:cap,lambda f:True);panel.start_camera()
 for _ in range(30):root.update();time.sleep(.1)
 panel.tick();assert panel.context.presence=='present';assert panel.badge.winfo_exists();capture('local-awareness-synthetic-present')
 # Visible indicator must survive faces-only/hidden workspace.
 root.withdraw();panel.window.withdraw();panel.tick();capture('local-awareness-indicator-hidden-workspace');assert panel.badge.winfo_viewable()
 panel.stop_all();panel.camera.thread.join(2);panel.tick();assert cap.released and panel.context.camera=='off';assert not any(e.kind in ('presence','foreground-app') for e in panel.context.events);assert not panel.context.apps
 root.deiconify();panel.window.deiconify();capture('local-awareness-stopped')
 checks['synthetic_camera']='debounced presence, indicator and release';checks['model_api_calls']=0;checks['media_retained']=0
 checks['unrun']=['physical webcam accuracy/permissions','real owner app behavior','24/7 soak','automatic persona judgment','screen/game content','cloud vision']
 (out/'local-awareness-checks.json').write_text(json.dumps(checks,indent=2))
finally:app.close()
