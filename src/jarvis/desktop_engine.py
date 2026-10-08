"""Reviewed foreground-bound Windows mouse/keyboard steps. No shell or model code."""
import threading,time,hashlib,json
def literal_keys(text):return ''.join('{'+c+'}'if c in '+^%~(){}'else c for c in text)
ALLOWED_KEYS={'left','right','up','down','home','end','backspace','delete','tab','escape'}
def validate_steps(steps):
 if not isinstance(steps,list)or not 1<=len(steps)<=30:raise ValueError('Review1to30bounded desktop steps')
 out=[]
 for row in steps:
  if not isinstance(row,dict):raise ValueError('Invalid desktop step')
  kind=row.get('action')
  if kind in ('move','click'):
   if set(row)!={'action','x','y'}or any(type(row[k])is not int or not 0<=row[k]<=10000 for k in ('x','y')):raise ValueError('Choose client-area coordinates')
  elif kind=='type':
   if set(row)!={'action','text'}or not isinstance(row['text'],str)or not 0<len(row['text'])<=2000 or any(ord(c)<32 for c in row['text']):raise ValueError('Review plain text without control characters. No secrets.')
  elif kind=='key':
   if set(row)!={'action','key'}or row['key']not in ALLOWED_KEYS:raise ValueError('Enter/submit, modifiers, hotkeys and shell keys are unavailable')
  elif kind=='scroll':
   if set(row)!={'action','delta'}or type(row['delta'])is not int or row['delta']not in (-600,-200,200,600):raise ValueError('Choose bounded scrolling')
  else:raise ValueError('Unsupported mouse/keyboard action')
  out.append(dict(row))
 return out
class DesktopEngine:
 def __init__(self,adapter):self.adapter=adapter;self.pending=None;self.cancel=threading.Event();self.state='off';self.completed=0;self.result='';self.lock=threading.RLock()
 def prepare(self,target,steps,scope):
  if self.state=='running':raise ValueError('Stop and wait for the current desktop task')
  if not isinstance(target,dict)or set(target)!={'hwnd','pid','title','width','height'}or any(type(target[k])is not int or target[k]<=0 for k in ('hwnd','pid','width','height'))or not isinstance(target['title'],str):raise ValueError('Choose an observed exact window')
  if not isinstance(scope,str)or not 0<len(scope)<=500:raise ValueError('Review the task purpose and effects')
  steps=validate_steps(steps)
  for row in steps:
   if row['action']in ('move','click')and not(0<=row['x']<target['width']and 0<=row['y']<target['height']):raise ValueError('Coordinate outside reviewed window')
  if self.adapter.observe(target['hwnd'])!=target:raise ValueError('Window changed before review')
  payload={'target':dict(target),'steps':steps,'scope':scope,'limits':'No secrets, credential fields, send/publish/pay/delete workflows. Mouse clicks can have effects; review exact targets.'};self.pending={'payload':payload,'sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()};self.state='review';return json.loads(json.dumps(self.pending))
 def stop(self):self.cancel.set();self.result='Stopped. Already completed input cannot be undone.'
 def run(self,reviewed,confirm=False,effect_approved=False):
  if confirm is not True or effect_approved is not True or self.state!='review'or not self.pending or reviewed!=self.pending:raise ValueError('Review exact window, task and steps before input')
  plan=json.loads(json.dumps(self.pending));target=plan['payload']['target'];self.cancel=threading.Event();self.completed=0;self.state='running'
  try:
   for row in plan['payload']['steps']:
    if self.cancel.is_set():self.state='stopped';break
    if self.adapter.observe(target['hwnd'])!=target:raise ValueError('Target window changed; no next input')
    self.adapter.focus(target['hwnd'])
    if self.cancel.is_set():self.state='stopped';break
    if self.adapter.foreground()!=target['hwnd']:raise ValueError('Foreground mismatch; no next input')
    # Recheck after foreground acquisition: moved/resized/replaced target cannot use stale coordinates.
    if self.adapter.observe(target['hwnd'])!=target:raise ValueError('Target changed during focus')
    self.adapter.perform(target,row);self.completed+=1
   else:self.state='completed';self.result='Reviewed input submitted. Task outcome needs source readback.'
  except Exception as e:self.state='blocked';self.result=str(e)[:200];raise
  finally:self.pending=None
  return self.snapshot()
 def snapshot(self):return {'state':self.state,'pending':self.pending,'completed_steps':self.completed,'result':self.result,'scope':'Foreground/window-bound input, not proof of task completion'}
class WindowsAdapter:
 def __init__(self):
  import os
  if os.name!='nt':raise RuntimeError('Desktop input is Windows-only')
 def observe(self,hwnd):
  from pywinauto import Desktop
  w=Desktop(backend='uia').window(handle=hwnd).wrapper_object();r=w.client_rect();return {'hwnd':hwnd,'pid':w.process_id(),'title':w.window_text(),'width':r.width(),'height':r.height()}
 def focus(self,hwnd):
  from pywinauto import Desktop
  Desktop(backend='uia').window(handle=hwnd).set_focus()
 def foreground(self):
  import ctypes
  ctypes.windll.user32.GetForegroundWindow.restype=ctypes.c_void_p
  return ctypes.windll.user32.GetForegroundWindow()
 def perform(self,target,row):
  from pywinauto import Desktop,mouse,keyboard
  w=Desktop(backend='uia').window(handle=target['hwnd']).wrapper_object()
  if row['action']in ('move','click'):
   point=w.client_to_screen((row['x'],row['y']))
   if row['action']=='move':mouse.move(coords=point)
   else:mouse.click(coords=point)
  elif row['action']=='scroll':mouse.scroll(coords=w.client_to_screen((target['width']//2,target['height']//2)),wheel_dist=row['delta']//200)
  elif row['action']=='type':
   from pywinauto.uia_defines import IUIA
   focused=IUIA().iuia.GetFocusedElement()
   if focused.CurrentProcessId!=target['pid']or focused.CurrentIsPassword:raise ValueError('Typing target changed or is a protected field')
   keyboard.send_keys(literal_keys(row['text']),with_spaces=True,with_tabs=False,with_newlines=False,vk_packet=True,turn_off_numlock=False)
  else:keyboard.send_keys('{'+row['key'].upper()+'}')
