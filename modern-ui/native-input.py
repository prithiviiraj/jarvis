"""Actual Windows fixture control activation, never dispatch a hidden DOM click."""
def activate(control):
 wrapper=control.wrapper_object()
 try:wrapper.invoke()
 except Exception as error:
  # WebView2 summary has Button role but no UIA Invoke pattern.
  # Other failures must remain visible instead of silently changing input route.
  if type(error).__name__!='NoPatternInterfaceError':raise
  wrapper.click_input()

def resize(control,width,height):
 import ctypes
 from ctypes import wintypes
 u=ctypes.windll.user32;u.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
 hwnd=control.wrapper_object().handle
 if not u.SetWindowPos(hwnd,None,0,0,width,height,0x0002|0x0004):raise ctypes.WinError()

def minimize(control):
 import ctypes
 from ctypes import wintypes
 u=ctypes.windll.user32;u.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];u.IsIconic.argtypes=[wintypes.HWND]
 hwnd=control.wrapper_object().handle;u.ShowWindow(hwnd,6)
 if not u.IsIconic(hwnd):raise AssertionError('Actual window did not minimize')

def work_area():
 import ctypes
 from ctypes import wintypes
 rect=wintypes.RECT();u=ctypes.windll.user32
 if not u.SystemParametersInfoW(0x0030,0,ctypes.byref(rect),0):raise ctypes.WinError()
 return rect

def place_in_work_area(control,width,height):
 import ctypes
 from ctypes import wintypes
 rect=work_area();u=ctypes.windll.user32;u.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
 if not u.SetWindowPos(control.wrapper_object().handle,None,rect.left,rect.top,width,height,0x0004):raise ctypes.WinError()
