"""Windows synthetic input boundary acceptance. No user's documents or accounts."""
import os,sys,time,json,pathlib,subprocess
TITLE='JARVIS isolated synthetic desktop input'
def fixture():
 import tkinter as tk
 root=tk.Tk();root.title(TITLE);root.geometry('640x360+80+80');tk.Label(root,text='SYNTHETIC LOCAL INPUT ONLY').pack();entry=tk.Entry(root,name='input',width=65);entry.pack(padx=20,pady=30);entry.focus_set();root.mainloop()
def run():
 if os.name!='nt':raise RuntimeError('Windows acceptance only')
 from .desktop_controller import DesktopController
 from pywinauto import Desktop
 from PIL import ImageGrab
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
 child=subprocess.Popen([sys.executable,'--desktop-input-fixture'])
 controller=DesktopController()
 try:
  w=Desktop(backend='uia').window(title=TITLE);w.wait('visible',timeout=15)
  windows=controller.discover(True);matches=[x for x in windows if x['title']==TITLE];assert len(matches)==1,windows;target=matches[0]
  assert target['pid']==child.pid,target
  # Focus the actual edit via mouse, not a fixture adapter or direct text injection.
  field=w.child_window(control_type='Edit').wrapper_object();rect=field.rectangle();point=w.wrapper_object().client_to_screen((0,0));x=rect.left-point[0]+12;y=rect.top-point[1]+rect.height()//2
  text='Literal +^%{} sample 123'
  review=controller.prepare(target,[{'action':'click','x':x,'y':y},{'action':'type','text':text},{'action':'key','key':'left'},{'action':'key','key':'right'},{'action':'move','x':x,'y':y},{'action':'scroll','delta':200}],'Only isolated synthetic fixture. No send, payment, account or file effects.')
  controller.run(review,True,True).join(20)
  state=controller.snapshot();assert not state['busy'];assert state['task']['state']=='completed',state
  actual=field.get_value();assert actual==text,(actual,text)
  ImageGrab.grab().save(out/'native-desktop-literal-input.png')
  # Stop revokes an unsent reviewed task, even if the exact old review is reused.
  stale=controller.prepare(target,[{'action':'type','text':'must not type'}],'Isolated fixture stop test')
  controller.stop()
  try:controller.run(stale,True,True)
  except ValueError:pass
  else:raise AssertionError('Revoked review accepted')
  assert field.get_value()==text
  (out/'native-desktop-input.json').write_text(json.dumps({'windows_actual':True,'foreground_bound_actual_input':True,'literal_text_readback':actual,'mouse_click_move_scroll_navigation_keys':True,'revoked_review_rejected':True,'completed_steps':state['task']['completed_steps'],'scope':'Frozen core on Windows synthetic tkinter fixture; not arbitrary app completion or owner hardware'},indent=2))
 finally:
  controller.close();child.terminate();child.wait(5)
