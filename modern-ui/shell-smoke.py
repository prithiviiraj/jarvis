"""Actual Tauri2/WebView2 host, IPC and workspace rendering acceptance."""
import subprocess,time,pathlib,ctypes,json,os
from PIL import ImageGrab
# Test-only loopback debugging. Production launches never set this environment.
env=dict(os.environ,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9222',WEBVIEW2_USER_DATA_FOLDER=str(pathlib.Path('ui-evidence/test-webview-profile').resolve()))
p=subprocess.Popen([str(pathlib.Path('src-tauri/target/release/jarvis-modern-ui.exe').resolve())],env=env);found=[]
try:
 subprocess.run(['node','native-smoke.mjs'],check=True,timeout=90)
 from ctypes import wintypes
 user32=ctypes.windll.user32
 user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
 user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
 user32.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int]
 user32.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
 user32.SetForegroundWindow.argtypes=[wintypes.HWND]
 user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
 user32.PostMessageW.argtypes=[wintypes.HWND,ctypes.c_uint,wintypes.WPARAM,wintypes.LPARAM]
 def enum(hwnd,_):
  b=ctypes.create_unicode_buffer(256);ctypes.windll.user32.GetWindowTextW(hwnd,b,256)
  owner=ctypes.c_ulong();ctypes.windll.user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
  if owner.value==p.pid and b.value=='JARVIS / Modern workspace preview':found.append(hwnd)
  return True
 callback=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)(enum)
 ctypes.windll.user32.EnumWindows(callback,0)
 if len(found)!=1:raise RuntimeError('Expected exactly one workspace HWND in launched process: '+str(len(found)))
 hwnd=found[0];ctypes.windll.user32.ShowWindow(hwnd,9)
 ctypes.windll.user32.SetWindowPos(hwnd,0,0,0,1000,740,0x0040);ctypes.windll.user32.SetForegroundWindow(hwnd)
 time.sleep(1)
 from ctypes import wintypes
 rect=wintypes.RECT();ctypes.windll.user32.GetWindowRect(hwnd,ctypes.byref(rect))
 image=ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom));image.save('ui-evidence/tauri-shell-actual.png')
 dark=sum(1 for pixel in image.crop((100,120,900,650)).resize((80,53)).convert('RGB').getdata() if max(pixel)<90)
 if dark<500:raise RuntimeError('Actual Tauri content blank or not rendered')
 pathlib.Path('ui-evidence/shell-checks.json').write_text(json.dumps({'actual_windows_shell_launched':True,'webview2_host':'Tauri2','cdp_contract_passed':True,'blank_pixel_check':True,'unrun':['physical laptop resources','physical sensors/audio']},indent=2))
finally:
 # Native WM_CLOSE exercises application exit teardown, then hard-stop only if stuck.
 if found:ctypes.windll.user32.PostMessageW(found[0],0x0010,0,0)
 try:p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
