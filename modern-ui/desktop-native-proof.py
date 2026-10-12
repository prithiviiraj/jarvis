"""Actual Windows selected-window literal editing in an owned disposable Tk app.
No user app, file opening, shell submission, network, microphone or model effects.
"""
import os,sys,pathlib,json,subprocess,time
if os.name!='nt':raise RuntimeError('Requires actual Windows input boundary')
out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
record=(out/'desktop-owned-app-readback.json').resolve()
if '--owned-app' in sys.argv:
 import tkinter as tk
 root=tk.Tk();root.title('JARVIS owned desktop input diagnostic');root.geometry('720x440')
 tk.Label(root,text='Disposable diagnostic text only. No file or network effects.').pack()
 edit=tk.Entry(root,width=70);edit.pack(padx=20,pady=20);edit.focus_set()
 def readback():record.write_text(json.dumps({'text':edit.get(),'pid':os.getpid()}));root.after(50,readback)
 root.after(50,readback);root.mainloop();sys.exit(0)
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.desktop_controller import DesktopController
from pywinauto import Desktop
from PIL import ImageGrab
record.unlink(missing_ok=True)
child=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'--owned-app'])
controller=DesktopController();checks=[]
def wait(test,timeout=10):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if test():return
  time.sleep(.05)
 raise AssertionError('Owned desktop diagnostic timed out')
def text():
 try:return json.loads(record.read_text())['text']
 except (FileNotFoundError,json.JSONDecodeError):return None
try:
 window=Desktop(backend='uia').window(title='JARVIS owned desktop input diagnostic',process=child.pid);window.wait('visible',timeout=15)
 rows=controller.discover(True);target=next(w for w in rows if w['pid']==child.pid and w['title']=='JARVIS owned desktop input diagnostic')
 # Owned Tk app sets its entry focus. Activate only its actual top-level window;
 # no UIA child-role guess is used for Tk's custom edit implementation.
 window.wrapper_object().set_focus()
 wait(lambda:text()=='')
 reviewed=controller.prepare(target,[{'action':'type','text':'Owned ^+%{} literal text'}],'Type this exact fixture text in the owned disposable input only')
 assert text()=='', 'No input before review'
 controller.run(reviewed,True,True).join(timeout=15)
 assert not controller.snapshot()['busy'];wait(lambda:text()=='Owned ^+%{} literal text');checks.append('actual literal Win32 input equals owned app readback')
 reviewed=controller.prepare(target,[{'action':'type','text':'SHOULD NOT TYPE'}],'Cancelled owned text only');controller.stop()
 try:controller.run(reviewed,True,True)
 except ValueError:pass
 else:raise AssertionError('Cancelled review accepted')
 assert text()=='Owned ^+%{} literal text';checks.append('cancelled review produced no input')
 reviewed=controller.prepare(target,[{'action':'type','text':'SHOULD NOT TYPE'}],'Stale geometry rejection only')
 window.move_window(width=800,height=480)
 controller.run(reviewed,True,True).join(timeout=15)
 assert controller.snapshot()['task']['state']=='blocked';assert text()=='Owned ^+%{} literal text';checks.append('changed actual window blocked next input')
 ImageGrab.grab().save(out/'desktop-owned-app-native.png')
 (out/'desktop-native-proof.json').write_text(json.dumps({'checks':checks,'scope':'Actual WindowsAdapter/controller with owned disposable Tk app readback. No copied-shell controls, physical voice concurrency, general autonomy or owner-hardware proof.'},indent=2))
finally:
 controller.close()
 subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=10,check=False)
 try:child.wait(timeout=5)
 except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
