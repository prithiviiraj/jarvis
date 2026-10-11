"""Actual Windows fixture control activation, never dispatch a hidden DOM click."""
def activate(control):
 wrapper=control.wrapper_object()
 try:wrapper.invoke()
 except Exception as error:
  # WebView2 summary has Button role but no UIA Invoke pattern.
  # Other failures must remain visible instead of silently changing input route.
  if type(error).__name__!='NoPatternInterfaceError':raise
  wrapper.click_input()
