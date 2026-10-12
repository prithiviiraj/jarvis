"""Actual copied-shell Windows UIA diagnostic. No model/download/mic/control starts."""
import os,pathlib,subprocess,time,json,importlib.util,sys,io,ctypes
if "--owned-target" in sys.argv:
 import tkinter as tk
 root=tk.Tk();root.title("JARVIS owned foreground capture target");root.geometry("800x450+40+40");root.configure(bg="#144c9d");root.mainloop();sys.exit(0)
from pywinauto import Desktop,mouse
from PIL import ImageGrab
spec=importlib.util.spec_from_file_location('native_input',pathlib.Path(__file__).with_name('native-input.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
if os.name!='nt':raise RuntimeError('Actual copied-shell diagnostic requires Windows')
exe=pathlib.Path(os.environ['JARVIS_UI_EXE']).resolve();out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
env=dict(os.environ,JARVIS_BIGFOOT_DIAGNOSTIC='1',JARVIS_DATA_DIR=str((out/'bigfoot-native-isolated-data').resolve()))
child=subprocess.Popen([str(exe)],env=env);checks=[];target_child=None
try:
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview',process=child.pid);window.wait('visible',timeout=30)
 def button(name):
  control=window.child_window(title=name,control_type='Button',visible_only=True);control.wait('exists enabled',timeout=15);return control
 def visible_text(text):
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   if any(text in c.window_text()for c in window.descendants()):return
   time.sleep(.2)
  raise AssertionError('Copied native text absent: '+text)
 visible_text('Voice');visible_text('Local speech assets');checks.append('actual first-open Voice offer')
 for name in ('Models','JARVIS','General','Voice'):
  helper.activate(button(name));time.sleep(.3);ImageGrab.grab().save(out/('native-bigfoot-'+name.lower()+'.png'));checks.append('actual native '+name+' navigation')
 # Inspect existing local controls only. Never click model/speech downloads or capture.
 visible_text('Speech input');visible_text('Automatic (multilingual)');visible_text('Test Microphone')
 for size in ((800,600),(1024,768)):
  helper.resize(window,size[0],size[1]);time.sleep(.4);ImageGrab.grab().save(out/('native-bigfoot-'+str(size[0])+'.png'));checks.append('native resized '+str(size))
 # JARVIS itself may be minimized while a different selected target stays foreground.
 sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
 from jarvis.game_companion import windows,capture
 from PIL import Image
 target_child=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'--owned-target'])
 target_window=Desktop(backend='uia').window(title='JARVIS owned foreground capture target',process=target_child.pid);target_window.wait('visible',timeout=15)
 helper.minimize(window)
 target_window.wrapper_object().set_focus()
 target=next(x for x in windows()if x['title']=='JARVIS owned foreground capture target');raw=None;deadline=time.monotonic()+10
 while raw is None and time.monotonic()<deadline:
  target_window.wrapper_object().set_focus();raw=capture(target)
  if raw is None:time.sleep(.1)
 assert raw,'Foreground target capture failed with actual JARVIS minimized'
 frame=Image.open(io.BytesIO(raw));frame.save(out/'native-bigfoot-minimized-target-frame.png');center=frame.convert('RGB').getpixel((frame.width//2,frame.height//2));assert max(abs(x-y)for x,y in zip(center,(20,76,157)))<10,'Wrong target pixels with JARVIS minimized'
 ImageGrab.grab().save(out/'native-bigfoot-minimized-target-desktop.png');checks.append('actual copied JARVIS minimized while selected foreground owned blue target captured exact pixels')
 helper.minimize(target_window);assert capture(target)is None,'Minimized TARGET should still be rejected';checks.append('minimized TARGET rejected separately from minimized JARVIS')
 (out/'native-bigfoot-report.json').write_text(json.dumps({'checks':checks,'scope':'Actual Windows WebView/UIA pixels and navigation only. Includes actual minimized JARVIS plus selected synthetic foreground target pixels. No model, microphone, audio, live video understanding, desktop task or owner-hardware proof.'},indent=2))
finally:
 if target_child:
  subprocess.run(['taskkill','/PID',str(target_child.pid),'/T','/F'],check=False,capture_output=True,timeout=10)
  try:target_child.wait(timeout=5)
  except subprocess.TimeoutExpired:target_child.kill();target_child.wait(timeout=5)
 subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],check=False,capture_output=True,timeout=10)
 try:child.wait(timeout=10)
 except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
