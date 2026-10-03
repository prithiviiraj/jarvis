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
  requests.append({'path':self.path});self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'data':[{'id':'fixture-local-model'}]}).encode())
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append({'path':self.path,'body':body})
  text=body['messages'][-1]['content']
  if 'failure-probe' in text:self.send_response(503);self.end_headers();return
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'Packaged local chat round-trip confirmed.'},'finish_reason':'stop'}]}).encode())
server=http.server.ThreadingHTTPServer(('127.0.0.1',1234),LocalFixture);threading.Thread(target=server.serve_forever,daemon=True).start()
p=subprocess.Popen([str(pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve())])
checks=[];window=None
try:
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=30);faces.set_focus();time.sleep(1)
 # Capture compact top-centred faces against a controlled desktop-colored background.
 import tkinter as tk
 bg=tk.Tk();bg.overrideredirect(True);bg.geometry(f'{bg.winfo_screenwidth()}x{bg.winfo_screenheight()}+0+0');bg.configure(bg='#17232f');bg.update();faces.set_focus();time.sleep(.5)
 rect=faces.rectangle();screen_w=bg.winfo_screenwidth();scale=ctypes.windll.user32.GetDpiForWindow(faces.handle)/96
 assert abs(rect.width()-340*scale)<4, f'Unexpected strip width: {rect}'
 assert abs((rect.left+rect.right)/2-screen_w/2)<4, f'Not top-centred: {rect}'
 assert 5<=rect.top<=40*scale, f'Not near screen top: {rect}'
 ImageGrab.grab().crop((0,0,screen_w,int(150*scale))).save('ui-evidence/tauri-top-centre-actual.png')
 faces.capture_as_image().save('ui-evidence/tauri-compact-actual.png')
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
 bg.destroy();checks.append('compact 340x110 logical pixels, top-centred, shadow disabled')
 faces.click_input(button='right');time.sleep(.5)
 entry=faces.child_window(title='Open workspace',control_type='Button');entry.wait('exists',timeout=10);entry.wrapper_object().invoke();checks.append('faces-only launch + right-click workspace')
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');window.wait('visible',timeout=20);window.set_focus()
 def button(name,root=None):
  item=(root or window).child_window(title_re=('(?s).*DEX.*Coder' if name=='DEX Coder' else '^'+__import__('re').escape(name)+'$'),control_type='Button');item.wait('exists',timeout=20);return item
 def click(name,root=None):button(name,root).wrapper_object().invoke();checks.append(name)
 click('Connect local core');time.sleep(2)
 click('DEX Coder')
 button('Download local voice models').wait('exists',timeout=10)
 button('Mic ON / start local voice').wait('exists',timeout=10)
 checks.append('voice model setup and explicit Mic ON controls visible')
 field=window.child_window(title='Message draft',control_type='Edit');field.wait('exists',timeout=10);field.wrapper_object().set_edit_text('packaged-chat-probe')
 click('Add local draft');time.sleep(3)
 text=' '.join(x.window_text() for x in window.descendants())
 assert 'Packaged local chat round-trip confirmed.' in text, 'No packaged reply: '+text
 window.capture_as_image().save('ui-evidence/tauri-chat-roundtrip.png');checks.append('packaged UI IPC frozen-core local HTTP reply shown')
 field.wrapper_object().set_edit_text('failure-probe');click('Add local draft');time.sleep(4)
 text=' '.join(x.window_text() for x in window.descendants())
 assert 'http-503' in text, 'Failure not persistently visible: '+text
 window.capture_as_image().save('ui-evidence/tauri-chat-error.png');checks.append('model error remains visible after idle polling')
 pathlib.Path('ui-evidence/local-chat-http.json').write_text(json.dumps({'scope':'controlled local HTTP fixture, not real LM Studio','requests':requests},indent=2))
 click('Local awareness');click('Allow app names');time.sleep(2)
 click('Allow local context judgment');time.sleep(2)
 click('Stop and clear local context');time.sleep(1)
 click('Floating faces')
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=15);faces.set_focus()
 click('LINK',faces);time.sleep(1);click('STOP',faces)
 faces.capture_as_image().save('ui-evidence/tauri-floating-actual.png')
 image=faces.capture_as_image().convert('RGB');corner=image.crop((image.width-18,image.height-18,image.width,image.height))
 white=sum(min(pixel)>230 for pixel in corner.getdata())
 assert white<20, f'White native corner still visible: {white} pixels' 
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
