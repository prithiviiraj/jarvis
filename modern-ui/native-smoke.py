"""Real Windows UI Automation against the actual Tauri WebView2 window."""
import subprocess,pathlib,time,json,ctypes
from PIL import ImageGrab
from pywinauto import Desktop
p=subprocess.Popen([str(pathlib.Path('src-tauri/target/release/jarvis-modern-ui.exe').resolve())])
checks=[];window=None
try:
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=30);faces.set_focus();time.sleep(1)
 faces.click_input(button='right');time.sleep(.5)
 entry=faces.child_window(title='Open workspace',control_type='Button');entry.wait('exists',timeout=10);entry.wrapper_object().invoke();checks.append('faces-only launch + right-click workspace')
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');window.wait('visible',timeout=20);window.set_focus()
 def button(name,root=None):
  item=(root or window).child_window(title_re=('(?s).*DEX.*Coder' if name=='DEX Coder' else '^'+__import__('re').escape(name)+'$'),control_type='Button');item.wait('exists',timeout=20);return item
 def click(name,root=None):button(name,root).wrapper_object().invoke();checks.append(name)
 click('Connect local core');time.sleep(2)
 click('DEX Coder')
 click('Local awareness');click('Allow app names');time.sleep(2)
 click('Allow local context judgment');time.sleep(2)
 click('Stop and clear local context');time.sleep(1)
 click('Floating faces')
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=15);faces.set_focus()
 click('LINK',faces);time.sleep(1);click('STOP',faces)
 faces.capture_as_image().save('ui-evidence/tauri-floating-actual.png')
 window.set_focus();
 from pywinauto import mouse
 mouse.scroll(coords=(550,450),wheel_dist=-6);time.sleep(1)
 window.capture_as_image().save('ui-evidence/tauri-shell-actual.png')
 image=window.capture_as_image();dark=sum(max(x)<90 for x in image.resize((100,75)).convert('RGB').getdata())
 if dark<800:raise RuntimeError('Native content blank')
 # Inspect actual accessibility text to verify Stop status, not merely click success.
 text=' '.join(x.window_text() for x in window.descendants())
 if 'Apps: off' not in ' '.join(text.split()) or 'Judgment off' not in ' '.join(text.split()):raise RuntimeError('Stop state not confirmed: '+text[-1200:])
 pathlib.Path('ui-evidence/native-checks.json').write_text(json.dumps({'host':'actual Windows Tauri/WebView2','checks':checks,'stop_state_confirmed':True,'unrun':['physical webcam/mic/audio','real model response','resources/24h','transparent desktop pixels']},indent=2))
except Exception:
 ImageGrab.grab().save('ui-evidence/native-failure.png')
 if 'faces' in locals():
  try:pathlib.Path('ui-evidence/faces-tree.txt').write_text('\n'.join(f'{x.element_info.control_type}: {x.window_text()}' for x in faces.descendants()),encoding='utf-8')
  except Exception:pass
 if window is not None:
  try:pathlib.Path('ui-evidence/native-tree.txt').write_text('\n'.join(f'{x.element_info.control_type}: {x.window_text()}' for x in window.descendants()),encoding='utf-8')
  except Exception:pass
 raise
finally:
 if 'faces' in locals():
  try:ctypes.windll.user32.PostMessageW(faces.handle,0x0010,0,0)
  except Exception:pass
 if window is not None:
  try:ctypes.windll.user32.PostMessageW(window.handle,0x0010,0,0)
  except Exception:pass
 try:p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
