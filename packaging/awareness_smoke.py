"""Windows local awareness verification. No owner's camera, model or network requests."""
import tkinter as tk,time,json,pathlib,sys
from unittest.mock import patch
from PIL import ImageGrab
import cv2,numpy as np
from jarvis.workspace import Workspace
from jarvis.local_awareness import foreground_app,CameraWorker
out=pathlib.Path('workspace-evidence');out.mkdir(exist_ok=True)
root=tk.Tk();app=Workspace(root);root.update();backdrop=tk.Toplevel(root);backdrop.geometry('1024x768+0+0');backdrop.overrideredirect(True);backdrop.configure(bg='#e7ecef');backdrop.lower(root);app.local_awareness.open();root.update();panel=app.local_awareness
panel.window.geometry('680x670+325+40')
checks={}
def capture(name):
 root.update();time.sleep(.3);root.update();ImageGrab.grab().save(out/(name+'.png'))
try:
 capture('local-awareness-off');assert panel.context.camera=='off' and panel.context.apps is False
 panel.apps.set(True);panel.set_apps();root.lift();root.focus_force();root.update();panel.last_app=0;panel.tick()
 checks['real_windows_foreground']=foreground_app(False);assert checks['real_windows_foreground'];assert not checks['real_windows_foreground']['title']
 checks['real_window_title']=foreground_app(True);assert checks['real_window_title'] is not None
 panel.window.lift();root.update()
 capture('local-awareness-app')
 cascade=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml');assert not cascade.empty()
 assert len(cascade.detectMultiScale(np.zeros((240,320),np.uint8)))==0;checks['real_detector_blank_frame']='no face'
 class Cap:
  def isOpened(self):return True
  def read(self):return True,object()
  def release(self):self.released=True
 cap=Cap();panel.camera=CameraWorker(panel.context,lambda:cap,lambda f:True);panel.start_camera()
 for _ in range(30):root.update();time.sleep(.1)
 panel.tick();panel.window.lift();assert panel.context.presence=='present';assert panel.badge.winfo_exists();capture('local-awareness-synthetic-present')
 # Deterministic model adapter exercises actual asynchronous judgment controls.
 from types import SimpleNamespace
 panel.judge.router_factory=lambda:SimpleNamespace(providers=[SimpleNamespace(cloud=False)],ask=lambda *a,**k:{'text':'{"speak":true,"text":"Want a little water, master?"}','cloud':False,'model':'synthetic-ci-not-llm'})
 panel.judge.hour=lambda:9;panel.judge_consent.set(True);panel.configure_judge()
 panel.context.app_event({'process':'synthetic-work.exe','title':''});worker=panel.judge.poll();assert worker;worker.join(3);app.poll_voice();panel.refresh();assert 'water' in panel.comment;panel.window.lift();capture('local-persona-judgment-synthetic')
 panel.judge.stop();panel.judge_consent.set(False)
 # Visible indicator must survive faces-only/hidden workspace.
 root.withdraw();panel.window.withdraw();backdrop.attributes('-topmost',True);panel.tick();panel.badge.lift();capture('local-awareness-indicator-hidden-workspace');assert panel.badge.winfo_viewable()
 panel.stop_all();panel.camera.thread.join(2);panel.tick();assert cap.released and panel.context.camera=='off';assert not any(e.kind in ('presence','foreground-app') for e in panel.context.events);assert not panel.context.apps
 backdrop.attributes('-topmost',False);backdrop.lower(root);root.deiconify();panel.window.deiconify();panel.window.lift();capture('local-awareness-stopped')
 checks['synthetic_camera']='debounced presence, indicator and release';checks['model_api_calls']=0;checks['media_retained']=0
 checks['unrun']=['physical webcam accuracy/permissions','real owner app behavior','24/7 soak','automatic persona judgment','screen/game content','cloud vision']
 (out/'local-awareness-checks.json').write_text(json.dumps(checks,indent=2))
finally:app.close()
