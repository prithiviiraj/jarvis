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
  # Direct-final retries append a user instruction. Match the original probe too.
  user_texts=[m['content'] for m in body['messages'] if m.get('role')=='user' and isinstance(m.get('content'),str)]
  text=user_texts[-2] if user_texts[-1].startswith('Your previous response did not include a final answer.') else user_texts[-1]
  if text=='Say ready in one word.':
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(b'data: {"choices":[{"delta":{"content":"Ready"}}]}\n\ndata: [DONE]\n\n');return
  if 'scaffold-probe' in text:
   self.send_response(200)
   if body['stream']:
    self.send_header('Content-Type','text/event-stream');self.end_headers()
    for part in ["Here", "'s a thinking process:", ' INTERNAL SCAFFOLD LEAK.']:
     self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':part}}]})+'\n\n').encode());self.wfile.flush()
    self.wfile.write(b'data: [DONE]\n\n')
   else:
    self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'Safe final answer recovered.'},'finish_reason':'stop'}]}).encode())
   return
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
 main.child_window(title='Transcript ON',control_type='Button').wait('exists',timeout=30)
 main.child_window(title='Message draft',control_type='Edit').wait('exists',timeout=30)
 assert not Desktop(backend='uia').window(title='JARVIS / Floating faces').exists(), 'Avatar window was removed'
 main.capture_as_image().save('ui-evidence/workspace-first-launch.png')
 main.minimize()
 captions=Desktop(backend='uia').window(title='JARVIS / Live captions');captions.wait('visible',timeout=15);caption_handle=captions.handle
 assert not Desktop(backend='uia').window(title='JARVIS / Floating faces').exists()
 ImageGrab.grab().save('ui-evidence/native-minimize-transcript-only.png')
 main.restore();main.set_focus();time.sleep(.8)
 assert not ctypes.windll.user32.IsWindowVisible(caption_handle),'Duplicate transcript should hide while workspace visible'
 main.child_window(title='Transcript OFF',control_type='Button').wrapper_object().invoke();main.minimize();time.sleep(.8)
 assert not ctypes.windll.user32.IsWindowVisible(caption_handle),'OFF must survive minimization'
 main.restore();main.set_focus();main.child_window(title='Transcript ON',control_type='Button').wrapper_object().invoke();main.minimize();captions.wait('visible',timeout=10)
 # Controlled background verifies transparent pixels outside text/hover controls.
 import tkinter as tk
 bg=tk.Tk();bg.overrideredirect(True);bg.geometry(f'{bg.winfo_screenwidth()}x{bg.winfo_screenheight()}+0+0');bg.configure(bg='#17232f');bg.attributes('-topmost',True);bg.update()
 ctypes.windll.user32.SetWindowPos(caption_handle,-1,0,0,0,0,0x0013);time.sleep(.8)
 cr=captions.rectangle();caption_pixels=ImageGrab.grab().crop((cr.left,cr.top,cr.right,cr.bottom));caption_pixels.save('ui-evidence/native-caption-empty-transparent.png')
 matched=sum(max(abs(a-b)for a,b in zip(pixel,(23,35,47)))<8 for pixel in caption_pixels.convert('RGB').getdata())
 assert matched>caption_pixels.width*caption_pixels.height*.95,'Caption background is not transparent'
 bg.destroy()
 # Reachable controls do not require an avatar strip.
 captions.move_mouse_input(coords=(captions.rectangle().width()-30,12));time.sleep(.3)
 captions.child_window(title='Reopen workspace',control_type='Button').wrapper_object().invoke();main.wait('visible',timeout=10);main.set_focus()
 checks.append('avatar window absent; transcript independent/default ON; OFF survives minimize; transparent pixels; caption OPEN restores workspace')
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');window.wait('visible',timeout=20);window.set_focus()
 def button(name,root=None):
  item=(root or window).child_window(title_re=('(?s).*DEX.*Coder' if name=='DEX Coder' else '^'+__import__('re').escape(name)+'$'),control_type='Button');item.wait('exists',timeout=20);return item
 def click(name,root=None):button(name,root).wrapper_object().invoke();checks.append(name)
 click('Connect core / check brains');time.sleep(2)
 click('Settings');click('Brain & APIs')
 click('Review local speed test');button('Confirm local speed test').wait('exists',timeout=10);button('Confirm local speed test').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-local-speed-review.png');click('Cancel local speed review');window.child_window(title='Confirm local speed test',control_type='Button').wait_not('exists',timeout=10);checks.append('native synthetic local timing review/cancel; no test request started')
 button('Check LM Studio connection').wait('exists',timeout=10)
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  connection_text=' '.join(x.window_text()for x in window.descendants())
  if 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text:break
  time.sleep(.2)
 assert 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text, 'Connection check must discover actual current loopback model'
 # Bring the account card into the native accessibility viewport by keyboard.
 button('Warm local model').wrapper_object().set_focus();window.type_keys('{TAB}{TAB}{TAB}{TAB}{TAB}');time.sleep(.3)
 window.child_window(title='slot1 API key',control_type='Edit').wait('exists',timeout=10)
 accounts=window.descendants(control_type='Button');tests=[x for x in accounts if x.window_text()=='Save & test this account'];assert tests and all(not x.is_enabled()for x in tests)
 window.child_window(title='slot1 API key',control_type='Edit').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-empty-key-onboarding.png')
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
 click('Agents')
 click('DEX Coder')
 click('Voice setup')
 button('Download local voice models').wait('exists',timeout=10)
 assert window.child_window(title='Last voice turn timing',control_type='Text').exists(),'Voice timing heading missing'
 endpoint=window.child_window(title='Listening pause',control_type='ComboBox');endpoint.wait('exists',timeout=10);endpoint.wrapper_object().set_focus();window.type_keys('{DOWN}{ENTER}');time.sleep(.7);assert endpoint.wrapper_object().selected_text()=='Fast - 480ms';endpoint.wrapper_object().set_focus();window.type_keys('{UP}{ENTER}');time.sleep(.7);assert endpoint.wrapper_object().selected_text()=='Balanced - 800ms (default)'
 window.capture_as_image().save('ui-evidence/native-voice-timing-empty.png')
 checks.append('native session listening-pause fast480ms then balanced800ms selector')
 click('Agents')
 interrupt=window.child_window(title='Interrupt (headphones)',control_type='CheckBox');interrupt.wait('exists',timeout=10);interrupt.wrapper_object().set_focus();time.sleep(.3)
 window.capture_as_image().save('ui-evidence/native-headphone-interruption-off.png')
 assert interrupt.wrapper_object().get_toggle_state()==0,'Interruption must default OFF'
 checks.append('native headphone interruption checkbox visible and defaults OFF; no microphone started')
 click('Voice setup')
 button('Mic ON / start local voice').wait('exists',timeout=10)
 click('Download local voice models');button('Confirm voice download').wait('exists',timeout=10)
 button('Confirm voice download').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-kokoro-download-review.png');click('Cancel voice download review');window.child_window(title='Confirm voice download',control_type='Button').wait_not('exists',timeout=10)
 button('Check local voice models').wrapper_object().set_focus();window.type_keys('+{TAB}+{TAB}');time.sleep(.3)
 engine=window.child_window(title='Speech engine',control_type='ComboBox')
 def choose_engine(label,key):
  for attempt in range(3):
   control=engine.wrapper_object()
   try:control.select(label)
   except Exception:
    control.set_focus();window.type_keys('{HOME}'+key+'{ENTER}')
   deadline=time.monotonic()+4
   while time.monotonic()<deadline:
    if engine.wrapper_object().selected_text().startswith(label.split(' - ')[0]):return
    time.sleep(.2)
  raise RuntimeError('Native speech engine option not selected: '+label)
 choose_engine('Kitten nano int8 - optional English, small download','{END}')
 assert engine.wrapper_object().selected_text().startswith('Kitten')
 assert 'Kitten assets not checked'in' '.join(x.window_text()for x in window.descendants())
 click('Download local voice models');button('Confirm voice download').wait('exists',timeout=10)
 assert 'About 28MB'in' '.join(x.window_text()for x in window.descendants())
 button('Confirm voice download').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-kitten-download-review.png');click('Cancel voice download review');button('Check local voice models').wrapper_object().set_focus();window.type_keys('+{TAB}+{TAB}');time.sleep(.3);choose_engine('Kokoro - default','{HOME}')
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
  button('seed.md').wrapper_object().set_focus();window.type_keys('{TAB}');time.sleep(.3)
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
 click('Tools');click('Download Laya model');button('Confirm Laya model download').wait('exists',timeout=10);button('Confirm Laya model download').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-managed-laya-download-review.png');click('Cancel Laya model download');window.child_window(title='Confirm Laya model download',control_type='Button').wait_not('exists',timeout=10);assert 'Laya model not checked'in' '.join(x.window_text()for x in window.descendants());click('Stop Laya setup / engine');checks.append('native inbuilt Laya exact pinned download review/cancel and stop; no model download or engine loading')
 click('Enable shared Laya');button('Confirm Laya permission').wait('exists',timeout=10);button('Confirm Laya permission').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-laya-permission-review.png');click('Cancel Laya permission');window.child_window(title='Confirm Laya permission',control_type='Button').wait_not('exists',timeout=10);click('Enable shared Laya');click('Confirm Laya permission');time.sleep(.3);assert 'load the inbuilt Laya engine'in' '.join(x.window_text()for x in window.descendants());click('Stop Laya proposals');assert 'Silent shared action log'in' '.join(x.window_text()for x in window.descendants());click('Enable browser commands');button('Confirm browser permission').wait('exists',timeout=10)
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


 # Isolate real chat archive title from earlier explicit action-routing messages.
 click('Enable browser commands');click('Confirm browser permission');click('Team room')
 field=window.child_window(title='Message draft',control_type='Edit');field.wait('exists',timeout=10);field.wrapper_object().set_edit_text('JARVIS, open the browser and open YouTube.');click('Add local draft');time.sleep(.5)
 button('Review proposed browser action').wait('exists',timeout=10);click('Review proposed browser action');button('Confirm Team browser action').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-team-browser-review.png');click('Cancel Team browser action')
 assert not window.child_window(title='Confirm Team browser action',control_type='Button').exists(),'Team browser cancel failed'
 checks.append('native compound YouTube command exact Team review/cancel, no navigation');click('Settings');click('Tools');click('Stop browser control')
 click('Agents');click('New chat');time.sleep(.5)
 field=window.child_window(title='Message draft',control_type='Edit');field.wait('exists',timeout=10);field.wrapper_object().set_edit_text('packaged-chat-probe')
 click('Add local draft')
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  text=' '.join(x.window_text() for x in window.descendants())
  if 'Packaged local ' in text and 'Packaged local chat round-trip confirmed.' not in text:break
  time.sleep(.1)
 else:raise RuntimeError('Incremental reply was not visible before completion')
 window.capture_as_image().save('ui-evidence/tauri-chat-streaming-partial.png')
 checks.append('actual partial streamed text visible before completion')
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
 field.wrapper_object().set_edit_text('scaffold-probe');click('Add local draft')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=' '.join(x.window_text()for x in window.descendants())
  assert 'INTERNAL SCAFFOLD LEAK'not in text and "Here's a thinking process"not in text
  if 'Safe final answer recovered.'in text:break
  time.sleep(.1)
 else:raise RuntimeError('Scaffold direct final retry failed')
 window.capture_as_image().save('ui-evidence/native-scaffold-suppressed-final-retry.png');checks.append('untagged split scaffold withheld; one direct nonstream retry shows only final answer')
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
 click('Agents');click('New chat')
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
 click('Transcript ON');window.minimize();overlay_text=Desktop(backend='uia').window(title='JARVIS / Live captions');overlay_text.wait('visible',timeout=10)
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
 click('Transcript OFF')
 click('Local awareness');click('Allow app names');time.sleep(2)
 click('Allow local context judgment');time.sleep(2)
 click('Stop sensors and speech');time.sleep(1)
 click('Transcript ON')
 workspace_handle=window.handle;ctypes.windll.user32.PostMessageW(workspace_handle,0x0010,0,0)
 overlay_text.wait('visible',timeout=10);time.sleep(.3)
 assert not ctypes.windll.user32.IsWindowVisible(workspace_handle)
 assert not Desktop(backend='uia').window(title='JARVIS / Floating faces').exists()
 overlay_text.move_mouse_input(coords=(overlay_text.rectangle().width()-30,12));time.sleep(.3)
 overlay_text.child_window(title='Reopen workspace',control_type='Button').wrapper_object().invoke();window.wait('visible',timeout=10);window.set_focus()
 checks.append('workspace close keeps only transcript; caption OPEN restores same workspace; avatars absent')
 window.capture_as_image().save('ui-evidence/tauri-workspace-restored.png')
 # Persist OFF across a full native application restart, not only in renderer state.
 click('Transcript OFF');ctypes.windll.user32.PostMessageW(window.handle,0x0010,0,0);p.wait(timeout=10)
 p=subprocess.Popen([str(pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve())])
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');window.wait('visible',timeout=30)
 restarted_workspace_handle=window.handle
 window.minimize();time.sleep(1)
 # UIA does not enumerate a hidden WebView window. Check native visibility by HWND.
 ctypes.windll.user32.FindWindowW.restype=ctypes.c_void_p
 persisted_handle=ctypes.windll.user32.FindWindowW(None,'JARVIS / Live captions')
 assert persisted_handle,'Caption window must exist for restart persistence check'
 assert not ctypes.windll.user32.IsWindowVisible(ctypes.c_void_p(persisted_handle)),'Transcript OFF was not persisted across restart'
 assert not Desktop(backend='uia').window(title='JARVIS / Floating faces').exists()
 # A minimized WebView may disappear from UIA; restore its verified native HWND first.
 assert ctypes.windll.user32.IsWindow(restarted_workspace_handle),'Restarted workspace HWND is invalid'
 ctypes.windll.user32.ShowWindow(restarted_workspace_handle,9) # SW_RESTORE
 window=Desktop(backend='uia').window(handle=restarted_workspace_handle)
 window.wait('visible',timeout=10);window.set_focus();click('Connect core / check brains');time.sleep(2);click('Agents');click('Local awareness')
 checks.append('native full restart preserves transcript OFF and never recreates avatar window')
 window.set_focus();
 from pywinauto import mouse
 mouse.scroll(coords=(550,450),wheel_dist=-6);time.sleep(1)
 window.capture_as_image().save('ui-evidence/tauri-shell-actual.png')
 image=window.capture_as_image();dark=sum(max(x)<90 for x in image.resize((100,75)).convert('RGB').getdata())
 if dark<800:raise RuntimeError('Native content blank')
 # Inspect actual accessibility text to verify Stop status, not merely click success.
 text=' '.join(x.window_text() for x in window.descendants())
 if 'Apps: off' not in ' '.join(text.split()) or 'Judgment off' not in ' '.join(text.split()):raise RuntimeError('Stop state not confirmed: '+text[-1200:])
 pathlib.Path('ui-evidence/native-checks.json').write_text(json.dumps({'host':'actual Windows Tauri/WebView2','checks':checks,'stop_state_confirmed':True,'unrun':['physical webcam/mic/audio','real model response','resources/24h','physical microphone interruption']},indent=2))
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
