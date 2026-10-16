"""Actual Windows fixture control activation, never dispatch a hidden DOM click."""
def activate(control):
 wrapper=control.wrapper_object()
 try:wrapper.invoke()
 except Exception as error:
  # WebView2 summary has Button role but no UIA Invoke pattern.
  # Other failures must remain visible instead of silently changing input route.
  if type(error).__name__!='NoPatternInterfaceError':raise
  # Native UIA descendants may be mounted but clipped by a scroll pane.
  # Refuse an offscreen mouse fallback rather than clicking another control.
  rect=wrapper.rectangle();top=wrapper.top_level_parent().rectangle()
  if rect.width()<=0 or rect.height()<=0 or rect.top<top.top or rect.bottom>top.bottom or rect.left<top.left or rect.right>top.right:
   # A native popup (the More drawer is control_type Window) can own its own
   # HWND while UIA-parenting under the main window: its children are visible
   # and clickable inside the popup bounds even though they sit outside the
   # main window rect. Accept the click only when a real Window ancestor
   # contains the target; otherwise keep refusing offscreen coordinates.
   try:
    parent=wrapper
    for _ in range(8):
     parent=parent.parent()
     if parent is None:break
     if getattr(parent.element_info,'control_type',None)!='Window':continue
     bounds=parent.rectangle()
     if rect.width()>0 and rect.height()>0 and bounds.top<=rect.top and rect.bottom<=bounds.bottom and bounds.left<=rect.left and rect.right<=bounds.right:
      wrapper.click_input();return
   except Exception:pass
   raise RuntimeError('Native mouse target is outside its window: '+wrapper.window_text()+' rect='+str(rect)+' toplevel='+str(top))from error
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
