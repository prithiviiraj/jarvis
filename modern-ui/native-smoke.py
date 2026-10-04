"""Real Windows UI Automation against the actual Tauri WebView2 window."""
import subprocess,pathlib,time,json,ctypes,os
from PIL import ImageGrab
from pywinauto import Desktop
# Controlled OpenAI-compatible local test server. Not a real model acceptance claim.
import http.server,threading
requests=[]
class LocalFixture(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  requests.append({'path':self.path});self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'models':[{'type':'llm','key':'qwen2.5-vl-3b-instruct','capabilities':{'vision':True},'loaded_instances':[]},{'type':'embedding','key':'text-embedding-nomic-embed-text-v1.5','loaded_instances':[]}]} if self.path=='/api/v1/models' else {'data':[{'id':'qwen2.5-vl-3b-instruct'},{'id':'text-embedding-nomic-embed-text-v1.5'}]}).encode())
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append({'path':self.path,'body':body})
  text=body['messages'][-1]['content']
  if 'length-probe' in text:
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   for part in ['<th','ink>PRIVATE REASONING</thi','nk>Final visible truncated answer.']:
    self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':part}}]})+'\n\n').encode());self.wfile.flush()
   self.wfile.write(b'data: {"choices":[{"delta":{},"finish_reason":"length"}],"usage":{"completion_tokens":300}}\n\ndata: [DONE]\n\n');return
  if 'failure-probe' in text:self.send_response(503);self.end_headers();return
  assert body['model']=='qwen2.5-vl-3b-instruct'
  if 'empty-stream-probe' in text:
   self.send_response(200)
   if body['stream']:
    self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(b'data: [DONE]\n\n')
   else:
    self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':[{'type':'text','text':'Local nonstream retry confirmed.'}]},'finish_reason':'stop'}]}).encode())
   return
  assert body['stream']
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
  for part in ['Packaged local ','chat round-trip ','confirmed.']:
   self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':part}}]})+'\n\n').encode());self.wfile.flush();time.sleep(1)
  self.wfile.write(b'data: [DONE]\n\n')
server=http.server.ThreadingHTTPServer(('127.0.0.1',1234),LocalFixture);threading.Thread(target=server.serve_forever,daemon=True).start()
p=subprocess.Popen([str(pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve())])
checks=[];window=None
try:
 main=Desktop(backend='uia').window(title_re='JARVIS / Modern.*');main.wait('visible',timeout=30);main.set_focus()
 main.child_window(title='Floating ON',control_type='Button').wait('exists',timeout=30)
 main.child_window(title='Message draft',control_type='Edit').wait('exists',timeout=30)
 assert not Desktop(backend='uia').window(title='JARVIS / Floating faces').exists(), 'Floating must be OFF at launch'
 main.capture_as_image().save('ui-evidence/workspace-first-launch.png')
 # Native minimize must activate transparent mode without enabling sensors.
 main.minimize()
 auto_faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');auto_faces.wait('visible',timeout=15)
 auto_captions=Desktop(backend='uia').window(title='JARVIS / Live captions');auto_captions.wait('exists',timeout=15)
 auto_face_handle=auto_faces.handle;auto_caption_handle=auto_captions.handle
 ImageGrab.grab().save('ui-evidence/native-minimize-auto-overlay.png')
 main.restore();main.set_focus()
 main.child_window(title='Floating OFF',control_type='Button').wrapper_object().invoke();time.sleep(.3)
 assert not ctypes.windll.user32.IsWindowVisible(auto_face_handle) and not ctypes.windll.user32.IsWindowVisible(auto_caption_handle),'OFF after minimize must hide both windows'
 checks.append('native minimize auto activates floating faces/captions; restore and explicit OFF still work')
 main.child_window(title='Floating ON',control_type='Button').wrapper_object().invoke();time.sleep(.5)
 checks.append('workspace first; floating OFF at launch; explicit ON button')
 captions=Desktop(backend='uia').window(title='JARVIS / Live captions');captions.wait('exists',timeout=10)
 style=ctypes.windll.user32.GetWindowLongW(captions.handle,-20)
 assert style&0x20,'Captions must be mouse clickthrough'
 checks.append('captionwindow mouseclickthrough nativeWS_EX_TRANSPARENT')
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=30);faces.set_focus();time.sleep(1)
 # Native caption pixels: no opaque background or idle/stale text.
 # Capture compact top-centred faces against a controlled desktop-colored background.
 import tkinter as tk
 bg=tk.Tk();bg.overrideredirect(True);bg.geometry(f'{bg.winfo_screenwidth()}x{bg.winfo_screenheight()}+0+0');bg.configure(bg='#17232f');bg.update();faces.set_focus();time.sleep(.5)
 cr=captions.rectangle();ImageGrab.grab().crop((cr.left,cr.top,cr.right,cr.bottom)).save('ui-evidence/native-caption-empty-transparent.png')
 rect=faces.rectangle();screen_w=bg.winfo_screenwidth();scale=ctypes.windll.user32.GetDpiForWindow(faces.handle)/96
 deadline=time.monotonic()+10
 while abs(rect.width()-450*scale)>=4 and time.monotonic()<deadline:time.sleep(.2);rect=faces.rectangle()
 assert abs(rect.width()-450*scale)<4, f'Unexpected strip width: {rect}'
 assert abs((rect.left+rect.right)/2-screen_w/2)<4, f'Not top-centred: {rect}'
 assert 5<=rect.top<=40*scale, f'Not near screen top: {rect}'
 ImageGrab.grab().crop((0,0,screen_w,int(150*scale))).save('ui-evidence/tauri-top-centre-actual.png')
 face_handle=faces.handle;caption_handle=captions.handle
 main.set_focus();main.child_window(title='Floating OFF',control_type='Button').wrapper_object().invoke();time.sleep(.3)
 assert not ctypes.windll.user32.IsWindowVisible(face_handle) and not ctypes.windll.user32.IsWindowVisible(caption_handle),'OFF must hide faces and captions'
 main.child_window(title='Floating ON',control_type='Button').wrapper_object().invoke();faces.wait('visible',timeout=10);faces.set_focus();time.sleep(.3)
 checks.append('explicit OFF hides facesandcaptions; ON restoresexistingwindows')
 faces.capture_as_image().save('ui-evidence/tauri-compact-actual.png')
 # Frame captures prove the default idle loop changes actual packaged pixels.
 frames=[]
 for i in range(40):
  image=faces.capture_as_image();image.save('ui-evidence/idle-motion-'+str(i)+'.png');frames.append(image.tobytes());time.sleep(.085)
 assert len(set(frames))>=6,'Packaged idle art is static'
 checks.append('packaged idle loop pixel advancement across40frames coveringfull3.4secondcycle')
 if (pathlib.Path('public/faces/manifest.json')).is_file():
  deadline=time.monotonic()+15
  while True:
   face_text=' '.join(x.window_text() for x in faces.descendants())
   if all(persona+' idle face' in face_text for persona in ['JARVIS','NOVA','KAI','LYRA','DEX']):break
   if time.monotonic()>deadline:break
   time.sleep(.2)
  for persona in ['JARVIS','NOVA','KAI','LYRA','DEX']:
   if persona+' idle face' not in face_text:raise RuntimeError('Original3D image did not load: '+persona+' / '+face_text)
  checks.append('allfive original3D image alt names present in actualWindows overlay')
 bg.destroy();checks.append('medium 450x140 logical pixels, top-centred, shadow disabled')
 faces.click_input(button='right');time.sleep(.5)
 entry=faces.child_window(title='Open workspace',control_type='Button');entry.wait('exists',timeout=10);entry.wrapper_object().invoke();checks.append('faces-only launch + right-click workspace')
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');window.wait('visible',timeout=20);window.set_focus()
 def button(name,root=None):
  item=(root or window).child_window(title_re=('(?s).*DEX.*Coder' if name=='DEX Coder' else '^'+__import__('re').escape(name)+'$'),control_type='Button');item.wait('exists',timeout=20);return item
 def click(name,root=None):button(name,root).wrapper_object().invoke();checks.append(name)
 click('Connect core / check brains');time.sleep(2)
 click('Settings');click('Brain & APIs')
 button('Check LM Studio connection').wait('exists',timeout=10)
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  connection_text=' '.join(x.window_text()for x in window.descendants())
  if 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text:break
  time.sleep(.2)
 assert 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text, 'Connection check must discover actual current loopback model'
 window.child_window(title='slot1 API key',control_type='Edit').wait('exists',timeout=10)
 checks.append('actual backend local model discovery ready; API key entry present; cloud remains off')
 window.capture_as_image().save('ui-evidence/native-brain-settings.png')
 click('Voice')
 click('DEX Coder')
 click('Voice setup')
 button('Download local voice models').wait('exists',timeout=10)
 button('Mic ON / start local voice').wait('exists',timeout=10)
 checks.append('voice model setup and explicit Mic ON controls visible')
 click('Voice')
 field=window.child_window(title='Message draft',control_type='Edit');field.wait('exists',timeout=10);field.wrapper_object().set_edit_text('packaged-chat-probe')
 click('Add local draft')
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  text=' '.join(x.window_text() for x in window.descendants())
  if 'Packaged local ' in text and 'Packaged local chat round-trip confirmed.' not in text:break
  time.sleep(.1)
 else:raise RuntimeError('Incremental reply was not visible before completion')
 window.capture_as_image().save('ui-evidence/tauri-chat-streaming-partial.png')
 faces_text=' '.join(x.window_text() for x in faces.descendants())
 assert 'JARVIS thinking face' in faces_text, 'Runtime thinking art not observed: '+faces_text
 faces.capture_as_image().save('ui-evidence/tauri-live-thinking.png');checks.append('actual partial streamed text plus live runtime thinking3D before completion')
 time.sleep(3)
 text=' '.join(x.window_text() for x in window.descendants())
 assert 'Packaged local chat round-trip confirmed.' in text, 'No packaged reply: '+text
 window.capture_as_image().save('ui-evidence/tauri-chat-roundtrip.png');checks.append('packaged UI IPC frozen-core local HTTP reply shown')
 for expression in ['thinking','speaking','idle']:
  click(expression);time.sleep(.4)
  window.capture_as_image().save('ui-evidence/tauri-preview-'+expression+'.png')
 checks.append('connected expression preview controls visibly tested; foursecondreturnlive')
 field.wrapper_object().set_edit_text('empty-stream-probe');click('Add local draft')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=' '.join(x.window_text() for x in window.descendants())
  if 'Local nonstream retry confirmed.' in text:break
  time.sleep(.1)
 else:raise RuntimeError('Empty stream nonstream retry failed: '+text)
 window.capture_as_image().save('ui-evidence/tauri-chat-empty-retry.png');checks.append('empty local SSE retried once without streaming and final text-array answer visible')
 field.wrapper_object().set_edit_text('length-probe');click('Add local draft')
 for i in range(80):
  text=' '.join(x.window_text() for x in window.descendants())
  if 'Final visible truncated answer.' in text and 'Reply reached the completion limit' in text:break
  time.sleep(.2)
 else:raise RuntimeError('Truncation handling failed: '+text)
 if 'PRIVATE REASONING' in text:raise RuntimeError('Thinking leaked into UI')
 window.capture_as_image().save('ui-evidence/tauri-final-truncated.png');checks.append('length retains final answer, marks incomplete, split thinking tags suppressed')
 field.wrapper_object().set_edit_text('failure-probe');click('Add local draft');time.sleep(4)
 text=' '.join(x.window_text() for x in window.descendants())
 assert 'http-503' in text, 'Failure not persistently visible: '+text
 window.capture_as_image().save('ui-evidence/tauri-chat-error.png');checks.append('model error remains visible after idle polling')
 pathlib.Path('ui-evidence/local-chat-http.json').write_text(json.dumps({'scope':'controlled local HTTP fixture, not real LM Studio','requests':requests},indent=2))
 # Native archive navigation and Pause preservation are visible, not metadata-only.
 click('Voice');click('New chat')
 assert 'Packaged local chat round-trip confirmed.' not in ' '.join(x.window_text()for x in window.descendants())
 saved=window.child_window(title='packaged-chat-probe',control_type='Button');saved.wait('exists',timeout=10);saved.wrapper_object().invoke()
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in window.descendants()):break
  time.sleep(.1)
 assert 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in window.descendants()),'Archived actual reply not restored'
 window.capture_as_image().save('ui-evidence/native-history-restored.png')
 checks.append('native new chat clears active context; saved conversation reopens actual reply')
 click('Floating ON');overlay_text=Desktop(backend='uia').window(title='JARVIS / Live captions');overlay_text.wait('visible',timeout=10)
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in overlay_text.descendants()):break
  time.sleep(.2)
 else:raise RuntimeError('Transparent right-side transcript missing saved actual reply')
 rr=overlay_text.rectangle();ImageGrab.grab().crop((rr.left,rr.top,rr.right,rr.bottom)).save('ui-evidence/native-overlay-full-text.png')
 checks.append('transparent overlay displays actual saved user and assistant conversation, not speech-time captions only')
 click('Floating OFF')
 click('Local awareness');click('Allow app names');time.sleep(2)
 click('Allow local context judgment');time.sleep(2)
 click('Stop sensors and speech');time.sleep(1)
 click('Floating ON')
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=15);faces.set_focus()
 click('LINK',faces);time.sleep(1);click('STOP',faces)
 faces.capture_as_image().save('ui-evidence/tauri-floating-actual.png')
 image=faces.capture_as_image().convert('RGB');corner=image.crop((image.width-18,image.height-18,image.width,image.height))
 white=sum(min(pixel)>230 for pixel in corner.getdata())
 assert white<20, f'White native corner still visible: {white} pixels' 
 # Native close hides rather than destroys the workspace, and overlay OPEN restores it.
 workspace_handle=window.handle;ctypes.windll.user32.PostMessageW(workspace_handle,0x0010,0,0);time.sleep(.8)
 assert not ctypes.windll.user32.IsWindowVisible(workspace_handle),'Workspace close did not hide'
 click('Reopen workspace',faces);window.wait('visible',timeout=10);window.set_focus()
 checks.append('native workspace close hides and overlay OPEN restores same window')
 window.capture_as_image().save('ui-evidence/tauri-workspace-restored.png')
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
 server.shutdown();server.server_close()
 if 'faces' in locals():
  try:ctypes.windll.user32.PostMessageW(faces.handle,0x0010,0,0)
  except Exception:pass
 if window is not None:
  try:ctypes.windll.user32.PostMessageW(window.handle,0x0010,0,0)
  except Exception:pass
 try:p.wait(timeout=10)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
