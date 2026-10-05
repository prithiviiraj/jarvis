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
  if text=='Say ready in one word.':
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(b'data: {"choices":[{"delta":{"content":"Ready"}}]}\n\ndata: [DONE]\n\n');return
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
 # Workspace header must sit below the visible native face strip.
 faces_for_dock=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces_for_dock.wait('visible',timeout=15)
 def header_rectangle():
  rows=[x.rectangle()for x in main.descendants(control_type='Text')if x.window_text()=='Voice'and x.rectangle().left>main.rectangle().left+220]
  assert rows,'Voice header missing'
  return max(rows,key=lambda r:r.left)
 dock_header=header_rectangle
 deadline=time.monotonic()+10
 while dock_header().top<faces_for_dock.rectangle().bottom and time.monotonic()<deadline:time.sleep(.2)
 assert dock_header().top>=faces_for_dock.rectangle().bottom,'Floating strip overlaps workspace header'
 main.capture_as_image().save('ui-evidence/workspace-floating-dock.png')
 checks.append('native floating visible reserves header space; actual face/header rectangles do not overlap')

 time.sleep(.8);assert not ctypes.windll.user32.IsWindowVisible(auto_caption_handle),'Duplicate captions must hide while workspace visible'
 style=ctypes.windll.user32.GetWindowLongW(auto_caption_handle,-20)
 assert style&0x20,'Captions must be mouse clickthrough'
 checks.append('captionwindow mouseclickthrough nativeWS_EX_TRANSPARENT')
 faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=30);faces.set_focus();time.sleep(1)
 # Native caption pixels: no opaque background or idle/stale text.
 # Capture compact top-centred faces against a controlled desktop-colored background.
 import tkinter as tk
 bg=tk.Tk();bg.overrideredirect(True);bg.geometry(f'{bg.winfo_screenwidth()}x{bg.winfo_screenheight()}+0+0');bg.configure(bg='#17232f');bg.update();main_handle=main.handle;ctypes.windll.user32.ShowWindow(main_handle,0);bg.attributes('-topmost',True);bg.lift();bg.update();
 ctypes.windll.user32.ShowWindow(auto_caption_handle,5)
 captions=Desktop(backend='uia').window(handle=auto_caption_handle);captions.wait('visible',timeout=10)
 for overlay_window in (faces,captions):ctypes.windll.user32.SetWindowPos(overlay_window.handle,-1,0,0,0,0,0x0013)
 time.sleep(.8)
 ctypes.windll.user32.ShowWindow(captions.handle,5)
 cr=captions.rectangle();caption_pixels=ImageGrab.grab().crop((cr.left,cr.top,cr.right,cr.bottom));caption_pixels.save('ui-evidence/native-caption-empty-transparent.png')
 matched=sum(max(abs(a-b)for a,b in zip(pixel,(23,35,47)))<8 for pixel in caption_pixels.convert('RGB').getdata())
 assert matched>caption_pixels.width*caption_pixels.height*.95,'Native caption window is opaque, not desktop-transparent'
 checks.append('native caption pixels match controlled desktop background across95percent of empty overlay')
 ctypes.windll.user32.ShowWindow(main_handle,5)
 rect=faces.rectangle();screen_w=bg.winfo_screenwidth();scale=ctypes.windll.user32.GetDpiForWindow(faces.handle)/96
 deadline=time.monotonic()+10
 while abs(rect.width()-450*scale)>=4 and time.monotonic()<deadline:time.sleep(.2);rect=faces.rectangle()
 strip_bottom_before_off=rect.bottom
 assert abs(rect.width()-450*scale)<4, f'Unexpected strip width: {rect}'
 assert abs((rect.left+rect.right)/2-screen_w/2)<4, f'Not top-centred: {rect}'
 assert 5<=rect.top<=40*scale, f'Not near screen top: {rect}'
 ImageGrab.grab().crop((0,0,screen_w,int(150*scale))).save('ui-evidence/tauri-top-centre-actual.png')
 face_handle=faces.handle;caption_handle=auto_caption_handle
 main.set_focus();main.child_window(title='Floating OFF',control_type='Button').wrapper_object().invoke();time.sleep(.3)
 assert not ctypes.windll.user32.IsWindowVisible(face_handle) and not ctypes.windll.user32.IsWindowVisible(caption_handle),'OFF must hide faces and captions'
 time.sleep(.7);assert header_rectangle().top<strip_bottom_before_off,'Workspace dock not released after OFF'
 bg.attributes('-topmost',False);bg.lower();main.set_focus();time.sleep(.3)
 main.capture_as_image().save('ui-evidence/workspace-floating-off-dock.png')
 bg.attributes('-topmost',True);bg.lift();bg.update()
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
 before_warmup=len(requests)
 button('Warm local model').wait('exists',timeout=10)
 assert not any(x.get('body',{}).get('messages',[{}])[-1].get('content')=='Say ready in one word.'for x in requests),'Warmup started without click'
 click('Warm local model')
 button('Confirm local warmup').wait('exists',timeout=10)
 assert len(requests)==before_warmup,'Review itself sent an unexpected model request'
 window.capture_as_image().save('ui-evidence/native-local-warmup-review.png')
 click('Confirm local warmup')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  if any(x.get('body',{}).get('messages',[{}])[-1].get('content')=='Say ready in one word.'for x in requests[before_warmup:]):break
  time.sleep(.2)
 time.sleep(1)
 assert any(x.get('body',{}).get('messages',[{}])[-1].get('content')=='Say ready in one word.'for x in requests[before_warmup:]),'No explicit fixed local warmup request'
 checks.append('explicit local warmup sends fixed greeting only after review; no automatic launch inference')
 window.capture_as_image().save('ui-evidence/native-local-warmup.png')

 window.capture_as_image().save('ui-evidence/native-brain-settings.png')
 click('Voice')
 click('DEX Coder')
 click('Voice setup')
 button('Download local voice models').wait('exists',timeout=10)
 assert window.child_window(title='Last voice turn timing',control_type='Text').exists(),'Voice timing heading missing'
 endpoint=window.child_window(title='Listening pause',control_type='ComboBox');endpoint.wait('exists',timeout=10);endpoint.wrapper_object().set_focus();window.type_keys('{DOWN}{ENTER}');time.sleep(.7);assert endpoint.wrapper_object().selected_text()=='Fast - 480ms';endpoint.wrapper_object().set_focus();window.type_keys('{UP}{ENTER}');time.sleep(.7);assert endpoint.wrapper_object().selected_text()=='Balanced - 800ms (default)'
 window.capture_as_image().save('ui-evidence/native-voice-timing-empty.png')
 checks.append('native session listening-pause fast480ms then balanced800ms selector')
 button('Mic ON / start local voice').wait('exists',timeout=10)
 click('Download local voice models');button('Confirm voice download').wait('exists',timeout=10)
 button('Confirm voice download').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-kokoro-download-review.png');click('Cancel voice download review');window.child_window(title='Confirm voice download',control_type='Button').wait_not('exists',timeout=10)
 button('Check local voice models').wrapper_object().set_focus();window.type_keys('+{TAB}+{TAB}');time.sleep(.3)
 engine=window.child_window(title='Speech engine',control_type='ComboBox');engine.wrapper_object().set_focus();window.type_keys('{DOWN}{ENTER}');time.sleep(.7)
 assert engine.wrapper_object().selected_text().startswith('Kitten')
 click('Download local voice models');button('Confirm voice download').wait('exists',timeout=10)
 assert 'About 28MB'in' '.join(x.window_text()for x in window.descendants())
 button('Confirm voice download').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-kitten-download-review.png');click('Cancel voice download review');button('Check local voice models').wrapper_object().set_focus();window.type_keys('+{TAB}+{TAB}');time.sleep(.3);engine.wrapper_object().set_focus();window.type_keys('{UP}{ENTER}');time.sleep(.7)
 assert 'Downloading 'not in' '.join(x.window_text()for x in window.descendants())
 button('Mic ON / start local voice').wait('exists',timeout=10)
 checks.append('native exact Kokoro/Kitten download reviews canceled; no download or microphone start; engine restored')
 # Actual temporary-vault UI flow, no owner's files. Reviews must fire nothing.
 import tempfile
 with tempfile.TemporaryDirectory()as vault_tmp:
  vault_root=pathlib.Path(vault_tmp);(vault_root/'.obsidian').mkdir();(vault_root/'seed.md').write_text('native-vault-fixture',encoding='utf-8')
  click('Settings');click('Memory')
  folder=window.child_window(title='Obsidian vault folder',control_type='Edit');folder.wait('exists',timeout=10);folder.wrapper_object().set_edit_text(vault_tmp)
  click('Connect local vault');button('Confirm vault connection').wait('exists',timeout=10)
  click('Cancel vault connection');window.child_window(title='Confirm vault connection',control_type='Button').wait_not('exists',timeout=10)
  click('Connect local vault');click('Confirm vault connection')
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   if 'Connected locally: '+str(vault_root.resolve()) in' '.join(x.window_text()for x in window.descendants()):break
   time.sleep(.1)
  assert 'Connected locally: '+str(vault_root.resolve()) in' '.join(x.window_text()for x in window.descendants())
  window.child_window(title='Search vault',control_type='Edit').wrapper_object().set_edit_text('native-vault-fixture');click('Search local notes');button('seed.md').wait('exists',timeout=10)
  name_field=window.child_window(title='New note path',control_type='Edit');name_field.wrapper_object().set_edit_text('native-created.md')
  body_field=window.child_window(title='New note text',control_type='Edit');body_field.wrapper_object().set_edit_text('exact native review text')
  click('Review / create new note');button('Confirm create new note').wait('exists',timeout=10);assert not(vault_root/'native-created.md').exists()
  click('Cancel new note');assert not(vault_root/'native-created.md').exists()
  click('Review / create new note');click('Confirm create new note')
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   if(vault_root/'native-created.md').exists():break
   time.sleep(.1)
  assert(vault_root/'native-created.md').read_text(encoding='utf-8')=='exact native review text'
  click('Review / create new note');click('Confirm create new note');time.sleep(.5);assert(vault_root/'native-created.md').read_text(encoding='utf-8')=='exact native review text'
  click('Disconnect vault');time.sleep(.5)
  checks.append('native vault connect review/cancel/confirm, local search, exact note review/cancel/create, no overwrite, disconnect')
 click('Tools');click('Enable browser commands');button('Confirm browser permission').wait('exists',timeout=10)
 button('Confirm browser permission').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-browser-permission-review.png')
 click('Cancel browser permission');window.child_window(title='Confirm browser permission',control_type='Button').wait_not('exists',timeout=10)
 click('Enable browser commands');click('Confirm browser permission');time.sleep(.5)
 browser_field=window.child_window(title='Browser command',control_type='Edit');browser_field.wrapper_object().set_edit_text('browser open example.com');click('Prepare browser command');button('Review / run browser command').wait('exists',timeout=10)
 click('Review / run browser command');button('Confirm browser command').wait('exists',timeout=10)
 assert 'https://example.com'in' '.join(x.window_text()for x in window.descendants())
 button('Confirm browser command').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-browser-command-review.png')
 click('Cancel browser command');window.child_window(title='Confirm browser command',control_type='Button').wait_not('exists',timeout=10)
 click('Stop browser control');time.sleep(.5);checks.append('native visible browser permission review/cancel/enable and exact destination review/cancel; no navigation fired')


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
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.'not in' '.join(x.window_text()for x in window.descendants()):break
  time.sleep(.1)
 assert 'Packaged local chat round-trip confirmed.' not in ' '.join(x.window_text()for x in window.descendants())
 saved=window.child_window(title='packaged-chat-probe',control_type='Button');saved.wait('exists',timeout=10);saved.wrapper_object().invoke()
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in window.descendants()):break
  time.sleep(.1)
 assert 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in window.descendants()),'Archived actual reply not restored'
 window.capture_as_image().save('ui-evidence/native-history-restored.png')
 checks.append('native new chat clears active context; saved conversation reopens actual reply')
 click('Floating ON');window.minimize();overlay_text=Desktop(backend='uia').window(title='JARVIS / Live captions');overlay_text.wait('visible',timeout=10)
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.' in ' '.join(x.window_text()for x in overlay_text.descendants()):break
  time.sleep(.2)
 else:raise RuntimeError('Transparent right-side transcript missing saved actual reply')
 rr=overlay_text.rectangle();ImageGrab.grab().crop((rr.left,rr.top,rr.right,rr.bottom)).save('ui-evidence/native-overlay-full-text.png')
 checks.append('transparent overlay displays actual saved user and assistant conversation while workspace minimized')
 transcript_handle=overlay_text.handle
 window.restore();window.set_focus();time.sleep(.8)
 assert not ctypes.windll.user32.IsWindowVisible(transcript_handle),'Caption transcript must hide on workspace restore'
 window.capture_as_image().save('ui-evidence/workspace-restored-no-duplicate-captions.png')
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
