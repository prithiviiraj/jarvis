import subprocess,sys,time,ctypes
from ctypes import wintypes
from PIL import ImageGrab
api=ctypes.WinDLL('user32',use_last_error=True)
api.FindWindowW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR];api.FindWindowW.restype=wintypes.HWND
p=subprocess.Popen([sys.executable,'-m','jarvis','--voice-preview'])
try:
 deadline=time.monotonic()+30;hwnd=None
 while time.monotonic()<deadline:
  if p.poll() is not None:raise RuntimeError('Preview exited early')
  hwnd=api.FindWindowW(None,'JARVIS - Voice core preview')
  if hwnd:break
  time.sleep(.2)
 if not hwnd:raise RuntimeError('Preview window missing')
 time.sleep(1);r=wintypes.RECT();api.GetWindowRect(hwnd,ctypes.byref(r));ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(sys.argv[1])
finally:p.terminate();p.wait(timeout=10)
