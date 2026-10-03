"""Launch actual Windows Tauri/WebView2 shell and capture pixels. No backend."""
import subprocess,time,pathlib,ctypes,json
from PIL import ImageGrab
p=subprocess.Popen([str(pathlib.Path('src-tauri/target/release/jarvis-modern-ui.exe').resolve())]);found=[]
try:
 def enum(hwnd,_):
  b=ctypes.create_unicode_buffer(256);ctypes.windll.user32.GetWindowTextW(hwnd,b,256)
  if 'JARVIS / Modern workspace preview' in b.value:found.append(hwnd)
  return True
 callback=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)(enum)
 for _ in range(30):
  ctypes.windll.user32.EnumWindows(callback,0)
  if found:break
  if p.poll() is not None:raise RuntimeError('Shell exited before window')
  time.sleep(.5)
 if not found:raise RuntimeError('Tauri shell window unavailable')
 ctypes.windll.user32.ShowWindow(found[0],9);ctypes.windll.user32.SetForegroundWindow(found[0]);time.sleep(8)
 image=ImageGrab.grab();image.save('ui-evidence/tauri-shell-actual.png')
 dark=sum(1 for pixel in image.crop((100,120,900,650)).resize((80,53)).convert('RGB').getdata() if max(pixel)<90)
 if dark<500:raise RuntimeError('Actual Tauri content blank or not rendered')
 pathlib.Path('ui-evidence/shell-checks.json').write_text(json.dumps({'actual_windows_shell_launched':True,'webview2_host':'Tauri2','backend_connected':False,'unrun':['physical laptop resources','transparent floating overlay','voice backend bridge']},indent=2))
finally:p.terminate();p.wait(timeout=10)
