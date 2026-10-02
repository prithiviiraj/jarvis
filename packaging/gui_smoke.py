"""Build harness only. Captures just the foundation window with sensors absent."""
import subprocess,sys,time
from pathlib import Path
from PIL import ImageGrab
import ctypes
from ctypes import wintypes
exe=sys.argv[1];output=sys.argv[2]
user32=ctypes.WinDLL('user32',use_last_error=True)
user32.FindWindowW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR];user32.FindWindowW.restype=wintypes.HWND
user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
p=subprocess.Popen([exe])
try:
    deadline=time.monotonic()+30
    hwnd=None
    while time.monotonic()<deadline:
        if p.poll() is not None:raise RuntimeError('Foundation window exited early')
        hwnd=user32.FindWindowW(None,'JARVIS - Foundation')
        if hwnd:break
        time.sleep(.2)
    if not hwnd:raise RuntimeError('Foundation window did not appear')
    time.sleep(1)
    rect=wintypes.RECT();user32.GetWindowRect(hwnd,ctypes.byref(rect))
    ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom)).save(output)
finally:
    p.terminate();p.wait(timeout=10)
