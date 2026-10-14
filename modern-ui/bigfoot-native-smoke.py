"""Actual copied-shell Windows UIA diagnostic. No model/download/mic/control starts."""
import os,pathlib,subprocess,time,json,importlib.util,sys,io,ctypes
if "--owned-target" in sys.argv:
 import tkinter as tk
 root=tk.Tk();root.title("JARVIS owned foreground capture target");root.geometry("800x450+40+40");root.configure(bg="#144c9d");root.mainloop();sys.exit(0)
from pywinauto import Desktop,mouse
# Proof-only pywinauto compatibility: WebView2 can expose a transient
# unknown/null role. Use the generic UIA wrapper instead of a registry KeyError.
# All original role/name/state/readback assertions and real input stay intact.
from pywinauto.controls.uiawrapper import UiaMeta,UIAWrapper
UiaMeta.control_type_to_cls.setdefault(None,UIAWrapper)
from PIL import ImageGrab
spec=importlib.util.spec_from_file_location('native_input',pathlib.Path(__file__).with_name('native-input.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
if os.name!='nt':raise RuntimeError('Actual copied-shell diagnostic requires Windows')
exe=pathlib.Path(os.environ['JARVIS_UI_EXE']).resolve();out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
env=dict(os.environ,JARVIS_LEGACY_WORKSPACE_DIAGNOSTIC='0',JARVIS_DATA_DIR=str((out/'bigfoot-native-isolated-data').resolve()))
child=subprocess.Popen([str(exe)],env=env);checks=[];target_child=None
try:
 window=Desktop(backend='uia').window(title='JARVIS',process=child.pid);window.wait('visible',timeout=30)
 def button(name):
  control=window.child_window(title=name,control_type='Button',visible_only=True);control.wait('exists enabled',timeout=15);return control
 def visible_text(text):
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   if any(text in c.window_text()for c in window.descendants(control_type='Text')):return
   time.sleep(.2)
  raise AssertionError('Copied native text absent: '+text)
 visible_text('Make JARVIS yours');checks.append('actual first-open profile prompt')
 profile=window.child_window(title='Your name',control_type='Edit');profile.wait('exists',timeout=15);profile.wrapper_object().set_edit_text('Native Fixture')
 address=window.child_window(title='Call me',control_type='Edit');address.wait('exists',timeout=15);address.wrapper_object().set_edit_text('Friend')
 helper.activate(button('Save profile'));time.sleep(.5);helper.activate(button('Voice'));visible_text('Local speech assets');checks.append('actual profile save then Voice navigation')
 for name in ('Models','JARVIS','General','Voice'):
  helper.activate(button(name));time.sleep(.3);ImageGrab.grab().save(out/('native-bigfoot-'+name.lower()+'.png'));checks.append('actual native '+name+' navigation')
 helper.activate(button('Home'));time.sleep(.3)
 for label in ('Settings','Computer tools','Start voice','Stop','Activate Laya (Brave)'):
  button(label).wait('exists enabled',timeout=15)
 window.capture_as_image().save(out/'native-bigfoot-home-session-controls.png')
 checks.append('actual default Home settings/mic/Stop/Brave controls visibly present, no audio/control started')
 helper.activate(button('Settings'))
 # General has a real scrollable pane. Reach the Button with actual wheel input,
 # rather than seeking its label only among Text nodes or invoking it offscreen.
 deadline=time.monotonic()+15;edit=None
 while time.monotonic()<deadline:
  candidates=window.descendants(control_type='Button')
  edit=next((c for c in candidates if c.window_text()=='Edit your profile'and c.is_visible()),None)
  r=window.rectangle()
  if edit is not None:
   rect=edit.rectangle()
   if rect.width()>0 and rect.height()>0 and rect.top>=r.top+40 and rect.bottom<=r.bottom-10:break
  mouse.scroll(coords=(r.right-80,r.bottom-130),wheel_dist=-3);time.sleep(.2)
 else:raise AssertionError('Profile edit button is not reachable with native scroll')
 window.capture_as_image().save(out/'native-bigfoot-profile-edit-reached.png')
 helper.activate(button('Edit your profile'));visible_text('Make JARVIS yours')
 name_control=window.child_window(title='Your name',control_type='Edit').wrapper_object();call_control=window.child_window(title='Call me',control_type='Edit').wrapper_object()
 assert name_control.iface_value.CurrentValue=='Native Fixture','Profile name did not persist after navigation'
 assert call_control.iface_value.CurrentValue=='Friend','Address preference did not persist after navigation'
 helper.activate(button('Save profile'));helper.activate(button('Voice'));visible_text('Local speech assets')
 checks.append('actual profile edit readback preserves owner-selected name/address')
 # Inspect existing local controls only. Never click model/speech downloads or capture.
 visible_text('Speech input')
 # Native select displays its chosen value via UIA Value/Selection patterns,
 # not necessarily the accessible Name returned by window_text().
 choices=[];route_control=None
 for c in window.descendants(control_type='ComboBox'):
  values=[c.window_text()]
  try:values.append(c.iface_value.CurrentValue)
  except Exception:pass
  try:values.append(c.selected_text())
  except Exception:pass
  choices.append(values)
  if 'Local - offline default'in str(values):route_control=c
 (out/'native-bigfoot-combobox-values.json').write_text(json.dumps(choices,indent=2))
 assert any('Automatic (multilingual)'in str(values)for values in choices),'Native speech input default value absent'
 checks.append('actual native speech input Automatic (multilingual) value pattern')
 assert any('Local - offline default'in str(values)for values in choices),'Default speech recognition route absent'
 assert route_control is not None
 # Open the native option list only, never select the online route or upload.
 window.set_focus()
 try:route_control.iface_expand_collapse.Expand()
 except Exception:route_control.click_input()
 time.sleep(.4)
 ImageGrab.grab().save(out/'native-bigfoot-stt-route-options.png')
 # Chromium native SELECT popup is a separate UIA pane with ListItem/MenuItem,
 # not Text descendants of the parent WebView window. Never select an option.
 option_rows=[];found=False;deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  option_rows=[]
  for top in Desktop(backend='uia').windows(visible_only=True):
   for kind in ('ListItem','MenuItem','Text'):
    try:controls=top.descendants(control_type=kind)
    except Exception:continue
    for c in controls:
     try:
      name=c.window_text();rect=c.rectangle()
      if name and c.is_visible():
       option_rows.append({'name':name,'type':kind,'rect':[rect.left,rect.top,rect.right,rect.bottom]})
       if name=='Groq - online audio opt-in':found=True
     except Exception:pass
  if found:break
  time.sleep(.2)
 (out/'native-bigfoot-stt-route-options-uia.json').write_text(json.dumps(option_rows,indent=2))
 ImageGrab.grab().save(out/'native-bigfoot-stt-route-options.png')
 assert found,'Actual visible native Groq option absent; inspect popup screenshot and UIA dump' 
 route_control.type_keys('{ESC}');time.sleep(.2)
 checks.append('actual native local-default/Groq opt-in route control visible; no upload')
 # First-open microphone test is below the voice list. Scroll actual pixels,
 # never activate microphone/download controls for this navigation diagnostic.
 def microphone_reachable(label):
  # UIA visibility and outer HWND bounds do not prove a WebView control is
  # fully painted: require client-area inset and keep exact bounds evidence.
  import ctypes
  from ctypes import wintypes
  hwnd=window.wrapper_object().handle;u=ctypes.windll.user32;u.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)];u.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
  client=wintypes.RECT();assert u.GetClientRect(hwnd,ctypes.byref(client))
  origin=wintypes.POINT(0,0);assert u.ClientToScreen(hwnd,ctypes.byref(origin))
  area=helper.work_area();left=max(origin.x,area.left);top=max(origin.y+40,area.top);right=min(origin.x+client.right,area.right)-20;bottom=min(origin.y+client.bottom,area.bottom)-8
  bounds_rows=[]
  for attempt in range(12):
   controls=[c for c in window.descendants(control_type='Button')if c.window_text()=='Test Microphone']
   rect=controls[0].rectangle()if controls else None
   full=bool(rect and controls[0].is_visible()and rect.top>=top and rect.bottom<=bottom and rect.left>=left and rect.right<=right)
   bounds_rows.append({'attempt':attempt,'button':[rect.left,rect.top,rect.right,rect.bottom]if rect else None,'client_content_safe':[left,top,right,bottom],'fully_inside':full})
   if full:break
   mouse.scroll(coords=(right-60,bottom-150),wheel_dist=-3);time.sleep(.2)
  (out/('native-bigfoot-microphone-'+label+'-bounds.json')).write_text(json.dumps(bounds_rows,indent=2))
  ImageGrab.grab().save(out/('native-bigfoot-microphone-'+label+'.png'))
  assert full,'Full Test Microphone button still outside client content area; inspect pixels and bounds, do not accept'
  checks.append('full microphone button inside client/content inset without activation '+label)
 microphone_reachable('initial')

 for size in ((800,600),(1024,768)):
  helper.place_in_work_area(window,size[0],size[1]);time.sleep(.4);ImageGrab.grab().save(out/('native-bigfoot-'+str(size[0])+'.png'));checks.append('native resized '+str(size));microphone_reachable(str(size[0]))
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
