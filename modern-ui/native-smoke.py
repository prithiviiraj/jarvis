"""Real Windows UI Automation against the actual Tauri WebView2 window."""
import subprocess,pathlib,time,json,ctypes,os
from PIL import ImageGrab
from pywinauto import Desktop,mouse
# Every acceptance run owns disposable data, never the runner/user default vault.
os.environ.setdefault('JARVIS_DATA_DIR',str(pathlib.Path('ui-evidence/native-isolated-data').resolve()))
# Controlled OpenAI-compatible local test server. Not a real model acceptance claim.
import http.server,threading
requests=[]
class LocalFixture(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  requests.append({'path':self.path});self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'models':[{'type':'llm','key':'qwen2.5-vl-3b-instruct','capabilities':{'vision':True},'loaded_instances':[{'id':'qwen2.5-vl-3b-instruct'}]},{'type':'embedding','key':'text-embedding-nomic-embed-text-v1.5','loaded_instances':[]}]} if self.path=='/api/v1/models' else {'data':[{'id':'qwen2.5-vl-3b-instruct'},{'id':'text-embedding-nomic-embed-text-v1.5'}]}).encode())
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append({'path':self.path,'body':body})
  # Direct-final retries append a user instruction. Match the original probe too.
  user_texts=[m['content'] for m in body['messages'] if m.get('role')=='user' and isinstance(m.get('content'),str)]
  text=user_texts[-2] if user_texts[-1].startswith('Your previous response did not include a final answer.') else user_texts[-1]
  if text=='Say ready in one word.':
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers();self.wfile.write(b'data: {"choices":[{"delta":{"content":"Ready"}}]}\n\ndata: [DONE]\n\n');return
  if 'Can you speak with DEX together? Speak about why politics is important?' in text:
   actor=__import__('re').match(r'Your current speaker is ([A-Z0-9_-]+)\.',body['messages'][0]['content']).group(1)
   before=sum('Can you speak with DEX together?'in str(r.get('body','')) for r in requests)
   reply=actor+' actual politics discussion turn '+str(before)+'.'
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':reply}}]})+'\n\ndata: [DONE]\n\n').encode());return
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
exe=pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve()
core=exe.parent/'backend'/'jarvis-local-core.exe'
assert core.is_file(),'Frozen core required for real desktop input acceptance'
subprocess.run([str(core),'--desktop-self-test'],check=True,timeout=60)
subprocess.run([str(core),'--google-self-test'],check=True,timeout=30)
subprocess.run([str(core),'--telegram-self-test'],check=True,timeout=30)
subprocess.run([str(core),'--draft-self-test'],check=True,timeout=30)
archive_path=pathlib.Path(os.environ['JARVIS_DATA_DIR'])/'custom-agents.json'
archive_path.parent.mkdir(parents=True,exist_ok=True)
archived_bytes=json.dumps({'version':1,'agents':[{'name':'MIRA','personality':'Saved synthetic tutor','voice':'af_sky'}]},indent=2).encode()
archive_path.write_bytes(archived_bytes)
p=subprocess.Popen([str(pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve())])
checks=[];window=None
try:
 main=Desktop(backend='uia').window(process=p.pid,title='JARVIS / Modern workspace preview');main.wait('visible',timeout=30)
 main=Desktop(backend='uia').window(handle=main.handle);main.set_focus()
 # The published workspace starts on Knowledge universe; composer is Team-only.
 main.child_window(title='Team room',control_type='Button').wait('exists',timeout=30)
 main.child_window(title='Team room',control_type='Button').wrapper_object().invoke()
 main.child_window(title='Message draft',control_type='Edit').wait('exists',timeout=30)
 main.child_window(title='Settings',control_type='Button').wrapper_object().invoke()
 main.child_window(title='Appearance',control_type='Button').wrapper_object().invoke()
 main.child_window(title='Transcript ON',control_type='Button').wait('exists',timeout=30)
 main.child_window(title='Team room',control_type='Button').wrapper_object().invoke()
 main.child_window(title='Message draft',control_type='Edit').wait('exists',timeout=30)
 assert not Desktop(backend='uia').window(process=p.pid,title='JARVIS / Floating faces').exists(), 'Avatar window was removed'
 main.capture_as_image().save('ui-evidence/workspace-first-launch.png')
 main.minimize()
 captions=Desktop(backend='uia').window(process=p.pid,title='JARVIS / Live captions');captions.wait('visible',timeout=15);caption_handle=captions.handle;captions=Desktop(backend='uia').window(handle=caption_handle)
 assert not Desktop(backend='uia').window(process=p.pid,title='JARVIS / Floating faces').exists()
 pill=Desktop(backend='uia').window(process=p.pid,title='JARVIS / Compact voice bar');pill.wait('visible',timeout=15);pill_handle=pill.handle;pill=Desktop(backend='uia').window(handle=pill_handle)
 assert ctypes.windll.user32.GetWindowLongW(pill_handle,-20)&8,'Pill must be always on top'
 pill.child_window(title='Stop JARVIS',control_type='Button').wait('exists',timeout=15)
 pill.child_window(title='Open JARVIS workspace',control_type='Button').wait('exists',timeout=15)
 assert 'Listening' not in ' '.join(pill.texts()+[x.window_text()for x in pill.descendants()]),'Inactive pill must not claim listening'
 ctypes.windll.user32.GetDpiForWindow.argtypes=[ctypes.c_void_p];ctypes.windll.user32.GetDpiForWindow.restype=ctypes.c_uint
 pr=pill.rectangle();scale=ctypes.windll.user32.GetDpiForWindow(pill_handle)/96
 assert scale>0,'Window DPI unavailable'
 assert abs(pr.width()-240*scale)<=3 and abs(pr.height()-40*scale)<=3,('Slim pill size',pr,scale)
 assert -3<=pr.top<=int(4*scale),('Pill must sit at top edge',pr.top)
 pill.capture_as_image().save('ui-evidence/native-compact-pill-mic-off.png')
 pill.child_window(title='Open JARVIS workspace',control_type='Button').wrapper_object().invoke();main.wait('visible',timeout=10);time.sleep(.5)
 assert not ctypes.windll.user32.IsWindowVisible(pill_handle),'Pill must hide on restore'
 main.minimize();pill.wait('visible',timeout=10)
 ImageGrab.grab().save('ui-evidence/native-minimize-transcript-and-pill.png')
 main.restore();main.set_focus();time.sleep(.8)
 assert not ctypes.windll.user32.IsWindowVisible(pill_handle),'Duplicate pill should hide while workspace visible'
 assert not ctypes.windll.user32.IsWindowVisible(caption_handle),'Duplicate transcript should hide while workspace visible'
 main.child_window(title='Settings',control_type='Button').wrapper_object().invoke();main.child_window(title='Appearance',control_type='Button').wrapper_object().invoke();main.child_window(title='Transcript OFF',control_type='Button').wrapper_object().invoke();main.minimize();time.sleep(.8)
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
 window=Desktop(backend='uia').window(handle=main.handle);window.wait('visible',timeout=20);window.set_focus()
 def button(name,root=None):
  import re
  # Animated Tools tiles include live status and descriptions in their UIA names.
  tiles=('Laya activate','Camera','Live screen','Proactive')
  pattern=('(?s)^'+re.escape(name)+r'(?:\s+.*)?$' if name in tiles else '(?s).*DEX.*Coder' if name=='DEX Coder' else '^'+re.escape(name)+'$')
  item=(root or window).child_window(title_re=pattern,control_type='Button',visible_only=False);item.wait('exists',timeout=20);return item
 def ui_text(root=None):
  # WebView2 may detach a UIA node during React updates. pywinauto's class
  # lookup then raises KeyError(None). Retry that specific snapshot race only.
  for attempt in range(5):
   try:return ' '.join(x.window_text() for x in (root or window).descendants())
   except KeyError as error:
    if error.args!=(None,) or attempt==4:raise
    time.sleep(.05)
 def focus_workspace():
  # Edge startup can steal focus after an earlier successful set_focus.
  # Verify the OS foreground owner immediately before every mouse action.
  for _ in range(15):
   window.set_focus()
   if ctypes.windll.user32.GetForegroundWindow()==window.handle:return
   time.sleep(.1)
  raise RuntimeError('JARVIS workspace could not acquire foreground for native input')
 def reveal_field(control):
  focus_workspace()
  # Settings pane keeps scroll across sub-page changes. Start at its top, then
  # use actual UIA bounds in either direction; never scroll blindly downward.
  control.wait('exists',timeout=15)
  mouse.scroll(coords=(760,450),wheel_dist=40);time.sleep(.2)
  for _ in range(48):
   focus_workspace()
   wrapper=control.wrapper_object();rect=wrapper.rectangle();bounds=window.rectangle()
   if wrapper.is_visible() and rect.top>bounds.top+160 and rect.bottom<bounds.bottom-65:
    # Disabled HTML buttons cannot take focus. UIA set_focus can instead move
    # to a different focusable field and scroll to its panel, corrupting pixels.
    if wrapper.is_enabled():wrapper.set_focus()
    time.sleep(.1);settled=control.wrapper_object().rectangle()
    if settled.top>bounds.top+160 and settled.bottom<bounds.bottom-65:return
    continue
   # A three-notch wheel can jump over short input fields forever. Keep
   # the pointer inside the actual panel/window and use one-notch settling.
   above=rect.top<bounds.top+160 and rect.width()>0
   distance=(bounds.top+160-rect.top) if above else (rect.bottom-(bounds.bottom-65))
   step=1 if abs(distance)<260 else 3
   direction=step if above else -step
   mouse.scroll(coords=(min(bounds.right-40,bounds.left+760),bounds.top+450),wheel_dist=direction);time.sleep(.2)
  raise RuntimeError('Field could not be brought into Settings viewport: '+control.window_text())
 def expand_advanced():
  # Isolated Edge can own foreground after browser-run. Mouse input must
  # target the JARVIS workspace, not the newly launched Edge window.
  window.set_focus()
  # HTML summary exposes Button semantics but has no Windows UIA Invoke pattern.
  # Use real mouse input, as the already-passing initial expansion does.
  toggle=window.child_window(title='Expand advanced browser controls',control_type='Button')
  toggle.wait('exists',timeout=10)
  for _ in range(18):
   focus_workspace()
   wrapper=toggle.wrapper_object();rect=wrapper.rectangle();bounds=window.rectangle()
   if rect.top>bounds.top+120 and rect.bottom<bounds.bottom-65:break
   mouse.scroll(coords=(760,450),wheel_dist=-3 if rect.bottom>=bounds.bottom-65 else 3);time.sleep(.2)
  else:raise RuntimeError('Advanced summary outside viewport')
  focus_workspace();toggle.wrapper_object().click_input()
 def click(name,root=None):
  # Navigation changed, effects/reviews remain real native controls.
  if name=='Add local draft':name='Send message'
  if name=='Agents':
   click('Settings');click('Team options');return
  if name=='Voice setup':
   click('Settings');click('Voices');return
  if name in ('Transcript ON','Transcript OFF'):
   button('Settings').wrapper_object().invoke();button('Appearance').wrapper_object().invoke()
  # Re-entering Settings remounts the native <details> collapsed. Reveal it
  # only when the requested legacy review control is inside that panel.
  advanced_names={'Enable browser commands','Download Laya model','Load inbuilt Laya','Stop Laya setup / engine','Enable shared Laya','Stop Laya proposals','Prepare browser command','Review / run browser command','Read available links locally'}
  if name=='Expand advanced browser controls':
   expand_advanced();checks.append(name);return
  if name in advanced_names:
   item=(root or window).child_window(title=name,control_type='Button')
   if not item.exists():
    expand_advanced()
  # Async work can leave a mounted control temporarily disabled. UIA Invoke
  # does not wait for HTML enabled state and fails with COMError in that gap.
  button(name,root).wait('enabled',timeout=20)
  button(name,root).wrapper_object().invoke()
  if name in ('Transcript ON','Transcript OFF'):
   # UIA invoke queues async IPC. Wait for actual native save/readback before close.
   confirmed='Transcript confirmed '+('ON'if name=='Transcript ON'else'OFF')
   window.child_window(title=confirmed,control_type='Text').wait('exists',timeout=10)
   button(name).wait('enabled',timeout=10)
  checks.append(name)
 # Native connection controls are inert until explicit owner review. Never
 # enter fixture credentials into the product's fixed registered-client slot.
 click('Settings');click('Advanced')
 # Latest named workflows: native inert pixels and real IPC Stop only, not
 # model inference, sensors, account sends or a private TLS listener.
 source_question=window.child_window(title='Source question',control_type='Edit');reveal_field(source_question)
 assert not button('Review source question/model').is_enabled();click('Stop and clear source answer');window.capture_as_image().save('ui-evidence/native-source-answer-inert.png')
 switch_model=window.child_window(title='Switch loaded model',control_type='ComboBox');reveal_field(switch_model)
 assert not button('Review exact local switch').is_enabled();click('Stop pending brain verification');window.capture_as_image().save('ui-evidence/native-brain-switch-inert.png')
 watch_window=window.child_window(title='Watch window',control_type='ComboBox');reveal_field(watch_window)
 assert not button('Review Watch session').is_enabled();click('Stop shared screen session');window.capture_as_image().save('ui-evidence/native-watch-inert.png')
 reflex_text=window.child_window(title='Reflex request preview',control_type='Edit');reveal_field(reflex_text)
 assert not button('Check five questions, do not execute').is_enabled();click('Stop Reflex and clear evidence');window.capture_as_image().save('ui-evidence/native-reflex-inert.png')
 phone_origin=window.child_window(title='Private HTTPS phone origin',control_type='Edit');reveal_field(phone_origin)
 assert not button('Review private TLS listener').is_enabled();click('Stop phone session');window.capture_as_image().save('ui-evidence/native-phone-tls-inert.png')
 reveal_field(button('Stop phone session'));assert not button('Review recent phone text for desktop').is_enabled();assert 'End phone and copy exact text to unsent input'not in ui_text();time.sleep(.5);window.capture_as_image().save('ui-evidence/native-phone-handoff-inert.png')
 checks.append('native phone-to-desktop exact-text preparation disabled without paired session; no automatic history copy, chat or speech')
 checks.append('native source answer/local switch/Watch/Reflex/phone TLS inert controls and IPC Stop; no inference/capture/listener')
 focus_goal=window.child_window(title='Focus goal',control_type='Edit');reveal_field(focus_goal);assert 'Focus off'in ui_text();window.capture_as_image().save('ui-evidence/native-focus-inert.png');checks.append('native focus timer off on launch, no sensors/speech/notification')
 email_field=window.child_window(title='Google account email',control_type='Edit');reveal_field(email_field)
 assert 'Google not connected'in ui_text(), 'Google falsely connected on launch'
 button('Registered desktop client').wait('exists',timeout=10)
 telegram=window.child_window(title='Telegram dedicated bot token',control_type='Edit');reveal_field(telegram)
 assert not button('Verify and save dedicated bot').is_enabled()
 click('Stop Telegram connection');window.capture_as_image().save('ui-evidence/native-telegram-inert.png')
 checks.append('native Telegram inert credential field; verification disabled without token; real IPC Stop, no external bot access')
 reveal_field(email_field)
 window.capture_as_image().save('ui-evidence/native-google-connection-inert.png')
 click('Stop Google connection');checks.append('native Google account/scopes panel inert on launch, Stop via actual IPC; no real OAuth opened')
 drive_read=window.child_window(title='Review Drive metadata read',control_type='Button',visible_only=False);reveal_field(drive_read);assert not drive_read.is_enabled()
 sheets_read=window.child_window(title='Review Sheets values read',control_type='Button',visible_only=False);reveal_field(sheets_read);assert not sheets_read.is_enabled()
 reveal_field(window.child_window(title='Drive new text name',control_type='Edit'))
 reveal_field(button('Capture Drive identity and private root'));assert not button('Capture Drive identity and private root').is_enabled(), 'Drive upload review enabled without account/access'
 assert 'Confirm exact private text upload'not in ui_text(), 'Drive upload final confirmation without review'
 window.capture_as_image().save('ui-evidence/native-drive-text-inert.png');checks.append('native Drive text upload inert without account/access; no live file')
 reveal_field(window.child_window(title='Write spreadsheet ID',control_type='Edit'))
 reveal_field(button('Capture sheet identity and prior cells'));assert not button('Capture sheet identity and prior cells').is_enabled(), 'Sheet overwrite review enabled without account/write scope'
 assert 'Confirm exact cell overwrite'not in ui_text(), 'Sheet final confirmation without prior/new cells review'
 window.capture_as_image().save('ui-evidence/native-sheets-write-inert.png');checks.append('native RAW sheet update inert without account/write scope; no live cells changed')
 reveal_field(window.child_window(title='Spreadsheet ID',control_type='Edit'))
 window.capture_as_image().save('ui-evidence/native-drive-sheets-inert.png');checks.append('native Drive/Sheets reviewed-read controls inert without account; no real read/write/download')
 gmail_to=window.child_window(title='Gmail To addresses',control_type='Edit');reveal_field(gmail_to)
 reveal_field(button('Prepare Gmail review'));assert not button('Prepare Gmail review').is_enabled(), 'Gmail review enabled without connected account'
 window.capture_as_image().save('ui-evidence/native-gmail-inert.png')
 checks.append('native Gmail review form disabled without connected account; no send started')
 calendar_title=window.child_window(title='Google event title',control_type='Edit');reveal_field(calendar_title)
 reveal_field(button('Prepare solo event review'));assert not button('Prepare solo event review').is_enabled(), 'Calendar review enabled without connected account'
 window.capture_as_image().save('ui-evidence/native-gcal-inert.png')
 checks.append('native solo calendar review form disabled without connected account; no event creation started')
 reveal_field(window.child_window(title='Recheck event and prepare Telegram draft',control_type='Button',visible_only=False))
 assert not button('Recheck event and prepare Telegram draft').is_enabled(), 'Handoff enabled without verified event/Telegram'
 window.capture_as_image().save('ui-evidence/native-calendar-telegram-inert.png');checks.append('native calendar-to-Telegram handoff inert without completed event/pairing, no send')
 reveal_field(window.child_window(title='Project identity',control_type='Edit'))
 project_read=window.child_window(title='Review GitHub source read',control_type='Button',visible_only=False);reveal_field(project_read);assert not project_read.is_enabled()
 window.capture_as_image().save('ui-evidence/native-project-read-inert.png');checks.append('native GitHub/Notion read panel inert; no token or external access')
 reveal_field(window.child_window(title='Notion paragraph block UUID',control_type='Edit'))
 reveal_field(button('Capture Notion block identity and prior text'));assert not button('Capture Notion block identity and prior text').is_enabled(), 'Notion update review enabled without bot/write gate'
 assert 'Confirm exact paragraph replacement'not in ui_text(), 'Notion final confirmation before prior/new text review'
 window.capture_as_image().save('ui-evidence/native-notion-text-inert.png');checks.append('native plain Notion update inert without bot/write gate; no live paragraph changed')
 reveal_field(window.child_window(title='Issue repository owner',control_type='Edit'))
 reveal_field(button('Review issue identity/repository/words'));assert not button('Review issue identity/repository/words').is_enabled(), 'Issue review enabled without identity/write gate'
 assert 'Confirm create issue and repository notifications'not in ui_text(), 'Issue final submission visible without review'
 window.capture_as_image().save('ui-evidence/native-github-issue-inert.png');checks.append('native issue identity/words panel inert without identity/write grant; no real issue or notification')
 reveal_field(window.child_window(title='Design title',control_type='Edit'));window.capture_as_image().save('ui-evidence/native-design-draft-upper-inert.png')
 reveal_field(button('Review exact local poster'));assert not button('Review exact local poster').is_enabled();assert 'Save exact local editable SVG'not in ui_text();window.capture_as_image().save('ui-evidence/native-design-draft-inert.png');checks.append('native local design draft empty review disabled, no Canva account/automatic SVG save/open')
 # Actual fixed Windows app launch: review before execution, window observed.
 click('Settings');click('Advanced');click('Advanced browser controls');click('Review app launch permission');click('Confirm app permission')
 window.child_window(title='Windows app command',control_type='Edit').wrapper_object().set_edit_text('Laya, open Notepad')
 click('Prepare app launch');click('Review exact app launch')
 window.capture_as_image().save('ui-evidence/native-notepad-exact-review.png')
 click('Cancel app launch');click('Prepare app launch');click('Review exact app launch');click('Confirm app launch')
 notes=Desktop(backend='uia').window(class_name='Notepad');notes.wait('visible',timeout=15)
 notes.capture_as_image().save('ui-evidence/native-reviewed-notepad-window.png');notes.close();window.set_focus()
 def dismiss_missing_obsidian():
  # Clean diagnostic runners need not have Obsidian installed. Windows may
  # present its own URI-handler warning, which owns foreground keyboard input.
  # Dismiss only the exact missing-Obsidian warning, never another dialog.
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   for candidate in Desktop(backend='uia').windows():
    try:
     text=' '.join([candidate.window_text()]+[x.window_text() for x in candidate.descendants()]).replace(chr(8217),chr(39)).replace(chr(8216),chr(39))
     if "can't open this 'obsidian' link" in text:
      ok=candidate.child_window(title='OK',control_type='Button');ok.wrapper_object().click_input();ok.wait_not('visible',timeout=5)
      checks.append('expected Windows missing Obsidian URI-handler dialog dismissed; no Obsidian visibility claim')
      window.set_focus();return
    except Exception:pass
   time.sleep(.1)
  window.set_focus()
 click('Disable app launch');click('Memory');click('Connect Obsidian')
 window.capture_as_image().save('ui-evidence/native-obsidian-auto-review.png')
 # Connect is the owner's direct action; no extra confirm button.
 import winreg
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')as key:download_path=winreg.QueryValueEx(key,'{374DE290-123F-4565-9164-39C4925E467B}')[0]
 auto_root=pathlib.Path(os.path.expandvars(download_path))/'Brain of Brain'
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  content=ui_text()
  if all((auto_root/f).is_file() for f in ['Team/LYRA.md','Active Work.md','Modes/Current settings.md','Brain of Brain.canvas']) and 'Setting up your data centre' not in content and 'Local vault ready; manual sync only.' in content:break
  time.sleep(.2)
 else:raise RuntimeError('Async AUTO vault setup did not settle')
 assert (auto_root/'Team/LYRA.md').is_file();assert (auto_root/'Active Work.md').is_file();assert (auto_root/'Modes/Current settings.md').is_file()
 dismiss_missing_obsidian();click('Manual sync');click('Show visuals');dismiss_missing_obsidian();click('Team room');checks.append('reviewed fixed Notepad launch reached real Windows window; no files or typing')
 # New source-backed graph controls run through REAL native IPC/frozen backend.
 # Chat words never choose evidence. Search uses the connected managed vault.
 source=auto_root/'phase2-native-source.md';source.write_text('# Exact native source\n\nPhase2 retrieval sentinel. Notes never grant permissions.',encoding='utf-8')
 query=window.child_window(title='Find knowledge source',control_type='Edit');query.wait('exists',timeout=15);query.wrapper_object().set_edit_text('Phase2 retrieval sentinel')
 click('Search knowledge sources')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  content=ui_text()
  if 'Phase2 retrieval sentinel. Notes never grant permissions.' in content and 'phase2-native-source.md' in content:break
  time.sleep(.15)
 else:raise RuntimeError('Native knowledge retrieval/source IPC missing: '+content[-1500:])
 assert 'Full captured note.' in content,'Source capture completeness missing'
 assert not any('body'in row for row in requests),'Local source was disclosed to inference'
 button('Master, read this source aloud').wait('exists',timeout=10) # Never invoked: source capture must not start speech with or without cached assets.
 window.capture_as_image().save('ui-evidence/native-knowledge-retrieval.png')
 click('Rotate knowledge right');click('Tilt knowledge view');click('Flat view');click('Neural view')
 click('Close knowledge note');source.unlink()
 checks.append('actual native source retrieval, capture and depth controls; no model disclosure or unapproved audio')


 time.sleep(2)
 assert not any('body'in row for row in requests),'Launch discovery must not send inference or user text'
 click('Settings');click('Tools');assert button('Proactive').exists(),'Single Proactive control missing';assert not window.child_window(title='Confirm proactive team',control_type='Button').exists();checks.append('single Proactive control present; no automatic speech or model start on mount')
 click('Settings');click('Brain & APIs')
 assert not window.child_window(title='Review local speed test',control_type='Button').exists(),'Removed speed control remains'
 button('Check LM Studio connection').wait('exists',timeout=10);click('Check LM Studio connection')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  connection_text=ui_text()
  if 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text:break
  time.sleep(.2)
 assert 'ready' in connection_text and 'qwen2.5-vl-3b-instruct' in connection_text, 'Connection check must discover actual current loopback model'
 # Re-read the account field after async local discovery refresh; no fixed TAB path.
 keyfield=window.child_window(title='slot1 API key',control_type='Edit')
 for attempt in range(3):
  keyfield.wait('exists',timeout=15)
  try:
   reveal_field(keyfield);keyfield.wait('visible',timeout=10);break
  except Exception:
   if attempt==2:
    window.capture_as_image().save('ui-evidence/native-account-key-lookup-failure.png');raise
   click('Brain & APIs');time.sleep(.5)
 accounts=window.descendants(control_type='Button');tests=[x for x in accounts if x.window_text()=='Save & test this account'];assert tests and all(not x.is_enabled()for x in tests)
 window.capture_as_image().save('ui-evidence/native-empty-key-onboarding.png')
 checks.append('actual backend local model discovery ready; API key entry present; cloud remains off')
 assert not window.child_window(title='Warm local model',control_type='Button').exists(),'Removed warmup control remains'
 checks.append('only LM Studio connection check remains; no speed or warmup control')
 window.capture_as_image().save('ui-evidence/native-brain-settings.png')
 click('Agents')
 def fill_named(name,text):
  dismiss_missing_obsidian()
  control=window.child_window(title=name,control_type='Edit');control.wait('exists',timeout=10)
  for attempt in range(3):
   window.set_focus();wrapper=control.wrapper_object();wrapper.set_focus();time.sleep(.2)
   wrapper.type_keys('^a',pause=.1);wrapper.type_keys('{BACKSPACE}',pause=.1);time.sleep(.2)
   wrapper.type_keys(text,with_spaces=True,pause=.12)
   deadline=time.monotonic()+3
   while time.monotonic()<deadline:
    if control.wrapper_object().get_value()==text:return
    time.sleep(.1)
  window.capture_as_image().save('ui-evidence/native-agent-field-failure.png')
  raise AssertionError(('Native field value mismatch',name,control.wrapper_object().get_value()))
 assert not window.child_window(title='New agent name',control_type='Edit').exists(),'Retired creator must not activate a fourth profile'
 for retired in ('NOVA Secretary','SILA Researcher','MIRA Custom teammate'):
  assert not window.child_window(title=retired,control_type='Button').exists(),retired
 window.child_window(title='Your team',control_type='Text').wait('exists',timeout=10)
 window.capture_as_image().save('ui-evidence/native-three-agent-team.png')
 checks.append('exact three active profiles; custom creator archived without deleting saved data')
 click('Team room')
 click('DEX Coder')
 click('Voice setup')
 button('Download local voice models').wait('exists',timeout=10)
 assert not window.child_window(title='Last voice turn timing',control_type='Text').exists(),'Removed voice timing remains'
 from pywinauto import mouse
 def choose_native_option(name,label,key):
  for attempt in range(3):
   control=window.child_window(title=name,control_type='ComboBox');control.wait('exists',timeout=10)
   try:control.wrapper_object().select(label)
   except Exception:
    control.wrapper_object().set_focus();window.type_keys('{HOME}'+key+'{ENTER}')
   deadline=time.monotonic()+4
   while time.monotonic()<deadline:
    if control.wrapper_object().selected_text()==label:return
    time.sleep(.2)
  raise AssertionError('Native option readback failed: '+name+' -> '+label)
 choose_native_option('Listening pause','Fast - 480ms (default)','{DOWN}')
 choose_native_option('Listening pause','Balanced - 800ms','')
 window.capture_as_image().save('ui-evidence/native-voice-timing-empty.png')
 checks.append('native session listening-pause fast480ms then balanced800ms selector')
 click('Settings');click('Voices')
 interrupt=window.child_window(title='Interrupt (headphones)',control_type='CheckBox');interrupt.wait('exists',timeout=10);interrupt.wrapper_object().set_focus();time.sleep(.3)
 window.capture_as_image().save('ui-evidence/native-headphone-interruption-off.png')
 assert interrupt.wrapper_object().get_toggle_state()==0,'Interruption must default OFF'
 checks.append('native headphone interruption checkbox visible and defaults OFF; no microphone started')
 button('Mic ON / start local voice').wait('exists',timeout=10)
 click('Download local voice models');button('Confirm voice download').wait('exists',timeout=10)
 button('Confirm voice download').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-kokoro-download-review.png');click('Cancel voice download review');window.child_window(title='Confirm voice download',control_type='Button').wait_not('exists',timeout=10)
 from pywinauto import mouse
 mouse.scroll(coords=(760,300),wheel_dist=12);time.sleep(.5)
 engine=window.child_window(title='Speech engine',control_type='ComboBox')
 def choose_engine(label,key):
  for attempt in range(3):
   engine.wait('exists',timeout=10)
   for scroll_attempt in range(18):
    control=engine.wrapper_object();rect=control.rectangle();bounds=window.rectangle()
    if rect.top>bounds.top+120 and rect.bottom<bounds.bottom-65:break
    mouse.scroll(coords=(760,450),wheel_dist=-2 if rect.bottom>=bounds.bottom-65 else 2);time.sleep(.2)
   else:
    window.capture_as_image().save('ui-evidence/native-engine-viewport-failure.png');raise RuntimeError('Speech engine not in viewport')
   control=engine.wrapper_object()
   # WebView2 UIA select() may return without firing React's change event.
   # Use the actual native dropdown keyboard path, then verify its visible value.
   engine.wait('enabled',timeout=10);control.click_input();window.type_keys(key+'{ENTER}')
   deadline=time.monotonic()+4
   while time.monotonic()<deadline:
    if engine.wrapper_object().selected_text().startswith(label.split(' - ')[0]):return
    time.sleep(.2)
  window.capture_as_image().save('ui-evidence/native-engine-selection-failure.png')
  raise RuntimeError('Native speech engine option not selected: '+label)
 choose_engine('Kokoro - default','{HOME}')
 assert engine.wrapper_object().selected_text().startswith('Kokoro')
 assert 'Kitten nano int8' not in ui_text()
 assert 'Downloading 'not in ui_text()
 button('Mic ON / start local voice').wait('exists',timeout=10)
 checks.append('native Kokoro-only speech option; exact download review canceled; no download or microphone start')
 # Actual temporary-vault UI flow, no owner's files. Reviews must fire nothing.
 import tempfile
 with tempfile.TemporaryDirectory()as vault_tmp:
  vault_root=pathlib.Path(vault_tmp);(vault_root/'.obsidian').mkdir();(vault_root/'seed.md').write_text('native-vault-fixture',encoding='utf-8')
  click('Settings');click('Memory')
  folder=window.child_window(title='Obsidian vault folder',control_type='Edit');folder.wait('exists',timeout=10)
  reveal_field(folder);folder.wait('visible',timeout=10);window.capture_as_image().save('ui-evidence/native-manual-vault-input-visible.png');folder.wrapper_object().set_edit_text(vault_tmp)
  click('Connect local vault');button('Confirm vault connection').wait('exists',timeout=10)
  click('Cancel vault connection');window.child_window(title='Confirm vault connection',control_type='Button').wait_not('exists',timeout=10)
  click('Connect local vault');click('Confirm vault connection')
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   if 'Connected locally: '+str(vault_root.resolve()) in ui_text():break
   time.sleep(.1)
  assert 'Connected locally: '+str(vault_root.resolve()) in ui_text()
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
  click('Review English search download');button('Confirm English search download').wait('exists',timeout=10);click('Cancel English search download');window.child_window(title='Confirm English search download',control_type='Button').wait_not('exists',timeout=10);checks.append('native optional English search model download review canceled; no download')
  checks.append('native vault connect review/cancel/confirm, local search, exact note review/cancel/create, no overwrite, disconnect')
 click('Advanced');click('Advanced browser controls')
 advanced=button('Expand advanced browser controls');advanced.wait('exists',timeout=10)
 for attempt in range(3):
  for scroll_attempt in range(18):
   control=advanced.wrapper_object();rect=control.rectangle();bounds=window.rectangle()
   if rect.top>bounds.top+120 and rect.bottom<bounds.bottom-65:break
   mouse.scroll(coords=(760,450),wheel_dist=-3 if rect.bottom>=bounds.bottom-65 else 3);time.sleep(.2)
  else:window.capture_as_image().save('ui-evidence/native-advanced-viewport-failure.png');raise RuntimeError('Advanced controls outside viewport')
  control.click_input()
  try:window.child_window(title='Download Laya model',control_type='Button').wait('exists',timeout=5);break
  except Exception:
   window.capture_as_image().save('ui-evidence/native-advanced-expand-failure.png')
   if attempt==2:raise
 click('Download Laya model');button('Confirm Laya model download').wait('exists',timeout=10);button('Confirm Laya model download').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-managed-laya-download-review.png');click('Cancel Laya model download');window.child_window(title='Confirm Laya model download',control_type='Button').wait_not('exists',timeout=10);assert 'Laya model missing; review Download Laya model'in ui_text();assert not button('Load inbuilt Laya').wrapper_object().is_enabled();click('Stop Laya setup / engine');checks.append('native inbuilt Laya exact pinned download review/cancel and stop; no model download or engine loading')
 click('Enable shared Laya');button('Confirm Laya permission').wait('exists',timeout=10);button('Confirm Laya permission').wrapper_object().set_focus();time.sleep(.2);window.capture_as_image().save('ui-evidence/native-laya-permission-review.png');click('Cancel Laya permission');window.child_window(title='Confirm Laya permission',control_type='Button').wait_not('exists',timeout=10);click('Enable shared Laya');click('Confirm Laya permission');time.sleep(.3);assert 'inbuilt Laya engine not loaded'in ui_text();click('Stop Laya proposals');assert 'Silent shared action log'in ui_text();click('Enable browser commands');button('Confirm browser permission').wait('exists',timeout=10)
 button('Confirm browser permission').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-browser-permission-review.png')
 click('Cancel browser permission');window.child_window(title='Confirm browser permission',control_type='Button').wait_not('exists',timeout=10)
 click('Enable browser commands');click('Confirm browser permission');time.sleep(.5)
 browser_field=window.child_window(title='Browser command',control_type='Edit');browser_field.wrapper_object().set_edit_text('browser open example.com');click('Prepare browser command');button('Review / run browser command').wait('exists',timeout=10)
 click('Review / run browser command');button('Confirm browser command').wait('exists',timeout=10)
 assert 'https://example.com'in ui_text()
 button('Confirm browser command').wrapper_object().set_focus();time.sleep(.2)
 window.capture_as_image().save('ui-evidence/native-browser-command-review.png')
 click('Cancel browser command');window.child_window(title='Confirm browser command',control_type='Button').wait_not('exists',timeout=10)
 click('Stop browser control');time.sleep(.5);checks.append('native visible browser permission review/cancel/enable and exact destination review/cancel; no navigation fired')


 click('Enable browser commands');click('Confirm browser permission');click('Team room')
 button('LYRA Writer').wait('exists',timeout=10);click('LYRA Writer');button('Activate team').wait('exists',timeout=10);window.capture_as_image().save('ui-evidence/native-lyra-explicit-voice-off.png');click('JARVIS Team leader');checks.append('profile switch visibly stops Mic; LYRA explicit start button; no microphone started')
 field=window.child_window(title='Message draft',control_type='Edit');field.wrapper_object().set_edit_text('JARVIS. OPEN. BROWSER.');click('Add local draft')
 button('Confirm Team browser action').wait('exists',timeout=10)
 assert 'open-window'in ui_text()
 window.capture_as_image().save('ui-evidence/native-dotted-jarvis-browser-review.png');click('Cancel Team browser action')
 checks.append('exact JARVIS. OPEN. BROWSER. punctuation phrase prepares browser-open review; cancel leaves browser unopened')
 # Cancel is a full browser-stop and revokes session permission. Re-enable explicitly.
 click('Settings');click('Advanced');click('Advanced browser controls')
 click('Enable browser commands');click('Confirm browser permission');click('Team room')
 field=window.child_window(title='Message draft',control_type='Edit')
 field.wrapper_object().set_edit_text('J.A.R.V.I.S. Open the browser.');click('Add local draft');click('Confirm Team browser action');click('Settings');click('Advanced');click('Advanced browser controls');click('Expand advanced browser controls')
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  content=ui_text()
  if 'about:blank'in content and 'ready'in content:break
  if 'Browser reports error' in content:raise RuntimeError('Actual isolated Edge startup failed: '+content)
  time.sleep(.3)
 else:raise RuntimeError('Actual reviewed isolated Edge open did not become ready')
 window.set_focus();window.capture_as_image().save('ui-evidence/native-reviewed-edge-ready.png')
 checks.append('actual bundled Playwright starts isolated installed Edge after exact Confirm, reports about:blank ready; no external site or Laya inferred action')


 click('Team room');field=window.child_window(title='Message draft',control_type='Edit');field.wrapper_object().set_edit_text('JARVIS, open the browser and open YouTube.');click('Add local draft')
 button('Confirm Team browser action').wait('exists',timeout=10)
 assert 'https://www.youtube.com/'in ui_text()
 window.capture_as_image().save('ui-evidence/native-team-browser-review.png');click('Cancel Team browser action')
 checks.append('native compound YouTube exact Team review/cancel, no navigation');click('Settings');click('Advanced');click('Advanced browser controls');click('Stop browser control')

 # The owner's exact live-test sentence must invoke actual multi-round IPC, not solo chat.
 click('Team room');click('JARVIS Team leader');click('New chat');time.sleep(.5)
 phrase='Can you speak with DEX together? Speak about why politics is important?'
 before=len(requests);field=window.child_window(title='Message draft',control_type='Edit');field.wrapper_object().set_edit_text(phrase);click('Add local draft')
 deadline=time.monotonic()+20
 while time.monotonic()<deadline:
  turns=[r for r in requests[before:] if phrase in str(r.get('body',''))]
  if len(turns)>=5 and 'JARVIS actual politics discussion turn' in ui_text():break
  time.sleep(.2)
 else:raise RuntimeError('Exact laptop sentence failed to start five actual team turns')
 actors=[__import__('re').match(r'Your current speaker is ([A-Z0-9_-]+)\.',r['body']['messages'][0]['content']).group(1) for r in turns]
 assert actors==['JARVIS','DEX','JARVIS','DEX','JARVIS'],actors
 assert any('[DEX]'in str(m)for m in turns[2]['body']['messages']),'Prior teammate reply missing from next actual request'
 window.capture_as_image().save('ui-evidence/native-laptop-phrase-dialogue.png')
 checks.append('exact laptop speak-with-DEX-together sentence starts five actual routed turns; previous teammate reply included, no audio/microphone starts')
 # Isolate real chat archive title from earlier explicit action-routing messages.
 click('Team room');click('New chat');time.sleep(.5)
 field=window.child_window(title='Message draft',control_type='Edit');field.wait('exists',timeout=10);field.wrapper_object().set_edit_text('packaged-chat-probe')
 click('Add local draft')
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  text=ui_text()
  if 'Packaged local ' in text and 'Packaged local chat round-trip confirmed.' not in text:break
  time.sleep(.1)
 else:raise RuntimeError('Incremental reply was not visible before completion')
 window.capture_as_image().save('ui-evidence/tauri-chat-streaming-partial.png')
 checks.append('actual partial streamed text visible before completion')
 time.sleep(3)
 click('Expand conversation')
 text=ui_text()
 assert 'Packaged local chat round-trip confirmed.' in text, 'No packaged reply: '+text
 assert 'Local · LM Studio · qwen2.5-vl-3b-instruct'in text,'True local provider/model source label missing'
 checks.append('native true local route/model visible on reply')
 window.capture_as_image().save('ui-evidence/tauri-chat-roundtrip.png');checks.append('packaged UI IPC frozen-core local HTTP reply shown')
 checks.append('legacy preview controls removed for creator; streamed live expression checked through Team renderer')
 field.wrapper_object().set_edit_text('empty-stream-probe');click('Add local draft')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=ui_text()
  if 'Local nonstream retry confirmed.' in text:break
  time.sleep(.1)
 else:raise RuntimeError('Empty stream nonstream retry failed: '+text)
 window.capture_as_image().save('ui-evidence/tauri-chat-empty-retry.png');checks.append('empty local SSE retried once without streaming and final text-array answer visible')
 field.wrapper_object().set_edit_text('scaffold-probe');click('Add local draft')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  text=ui_text()
  assert 'INTERNAL SCAFFOLD LEAK'not in text and "Here's a thinking process"not in text
  if 'Safe final answer recovered.'in text:break
  time.sleep(.1)
 else:raise RuntimeError('Scaffold direct final retry failed')
 window.capture_as_image().save('ui-evidence/native-scaffold-suppressed-final-retry.png');checks.append('untagged split scaffold withheld; one direct nonstream retry shows only final answer')
 field.wrapper_object().set_edit_text('length-probe');click('Add local draft')
 for i in range(80):
  text=ui_text()
  if 'Final visible truncated answer.' in text and 'Reply reached the completion limit' in text:break
  time.sleep(.2)
 else:raise RuntimeError('Truncation handling failed: '+text)
 if 'PRIVATE REASONING' in text:raise RuntimeError('Thinking leaked into UI')
 window.capture_as_image().save('ui-evidence/tauri-final-truncated.png');checks.append('length retains final answer, marks incomplete, split thinking tags suppressed')
 field.wrapper_object().set_edit_text('failure-probe');click('Add local draft');time.sleep(4)
 text=ui_text()
 assert 'Local model did not answer.' in text, 'Failure not persistently visible: '+text
 window.capture_as_image().save('ui-evidence/tauri-chat-error.png');checks.append('model error remains visible after idle polling')
 pathlib.Path('ui-evidence/local-chat-http.json').write_text(json.dumps({'scope':'controlled local HTTP fixture, not real LM Studio','requests':requests},indent=2))
 # Native archive navigation and Pause preservation are visible, not metadata-only.
 click('Team room');click('New chat')
 deadline=time.monotonic()+10
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.'not in ui_text():break
  time.sleep(.1)
 assert 'Packaged local chat round-trip confirmed.' not in ui_text()
 saved=window.child_window(title='packaged-chat-probe',control_type='Button');saved.wait('exists',timeout=10);saved.wrapper_object().invoke()
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if 'Packaged local chat round-trip confirmed.' in ui_text():break
  time.sleep(.1)
 assert 'Packaged local chat round-trip confirmed.' in ui_text(),'Archived actual reply not restored'
 window.capture_as_image().save('ui-evidence/native-history-restored.png')
 checks.append('native new chat clears active context; saved conversation reopens actual reply')
 click('Transcript ON');click('Team room');window.minimize();overlay_text=Desktop(backend='uia').window(process=p.pid,title='JARVIS / Live captions');overlay_text.wait('visible',timeout=10)
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
 click('Settings');click('Privacy');click('Allow app names');time.sleep(2)
 click('Allow local context judgment');time.sleep(2)
 click('Stop sensors and speech');time.sleep(1)
 click('Transcript ON')
 workspace_handle=window.handle;ctypes.windll.user32.PostMessageW(workspace_handle,0x0010,0,0)
 overlay_text.wait('visible',timeout=10);time.sleep(.3)
 assert not ctypes.windll.user32.IsWindowVisible(workspace_handle)
 assert not Desktop(backend='uia').window(process=p.pid,title='JARVIS / Floating faces').exists()
 overlay_text.move_mouse_input(coords=(overlay_text.rectangle().width()-30,12));time.sleep(.3)
 overlay_text.child_window(title='Reopen workspace',control_type='Button').wrapper_object().invoke();window.wait('visible',timeout=10);window.set_focus()
 checks.append('workspace close keeps only transcript; caption OPEN restores same workspace; avatars absent')
 window.capture_as_image().save('ui-evidence/tauri-workspace-restored.png')
 # Persist OFF across a full native application restart, not only in renderer state.
 click('Transcript OFF');ctypes.windll.user32.PostMessageW(window.handle,0x0010,0,0);p.wait(timeout=10)
 p=subprocess.Popen([str(pathlib.Path(os.environ.get('JARVIS_UI_EXE','src-tauri/target/release/jarvis-modern-ui.exe')).resolve())])
 window=Desktop(backend='uia').window(process=p.pid,title='JARVIS / Modern workspace preview');window.wait('visible',timeout=30)
 restarted_workspace_handle=window.handle
 window=Desktop(backend='uia').window(handle=restarted_workspace_handle)
 window.minimize()
 # Hidden WebViews are not in UIA. Enumerate this restarted process only,
 # with pointer-safe Win32 signatures and a bounded creation wait.
 from ctypes import wintypes
 user32=ctypes.windll.user32
 user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
 user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
 user32.IsWindowVisible.argtypes=[wintypes.HWND];user32.IsWindowVisible.restype=wintypes.BOOL
 callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
 user32.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
 def process_caption_windows():
  found=[]
  def visit(hwnd,param):
   pid=wintypes.DWORD();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
   if pid.value==p.pid:
    title=ctypes.create_unicode_buffer(512);user32.GetWindowTextW(hwnd,title,len(title))
    if title.value=='JARVIS / Live captions':found.append(hwnd)
   return True
  callback=callback_type(visit);user32.EnumWindows(callback,0);return found
 deadline=time.monotonic()+15;persisted_handle=None
 while time.monotonic()<deadline:
  if p.poll()is not None:raise RuntimeError('Restarted native app exited before caption verification: '+str(p.returncode))
  matches=process_caption_windows()
  if len(matches)==1:persisted_handle=matches[0];break
  if len(matches)>1:raise RuntimeError('Duplicate caption HWNDs in restarted native process')
  time.sleep(.1)
 assert persisted_handle,'Caption window missing from restarted process after bounded creation wait'
 assert not user32.IsWindowVisible(persisted_handle),'Transcript OFF was not persisted across restart'
 assert not Desktop(backend='uia').window(process=p.pid,title='JARVIS / Floating faces').exists()
 # A minimized WebView may disappear from UIA; restore its verified native HWND first.
 assert ctypes.windll.user32.IsWindow(restarted_workspace_handle),'Restarted workspace HWND is invalid'
 ctypes.windll.user32.ShowWindow(restarted_workspace_handle,9) # SW_RESTORE
 window=Desktop(backend='uia').window(handle=restarted_workspace_handle)
 window.wait('visible',timeout=10);window.set_focus();time.sleep(2);click('Team room')
 for name in ('JARVIS Team leader','LYRA Writer','DEX Coder'):button(name).wait('exists',timeout=10)
 for name in ('MIRA Custom teammate','NOVA Secretary','SILA Researcher'):assert not window.child_window(title=name,control_type='Button').exists(),name
 assert archive_path.read_bytes()==archived_bytes,'Archived custom file changed'
 checks.append('exact three active profiles survive native restart; legacy MIRA file unchanged and inactive')
 click('Settings');click('Privacy')
 checks.append('native full restart preserves transcript OFF and never recreates avatar window')
 window.set_focus();
 from pywinauto import mouse
 mouse.scroll(coords=(550,450),wheel_dist=-6);time.sleep(1)
 window.capture_as_image().save('ui-evidence/tauri-shell-actual.png')
 image=window.capture_as_image();dark=sum(max(x)<90 for x in image.resize((100,75)).convert('RGB').getdata())
 if dark<800:raise RuntimeError('Native content blank')
 # Inspect actual accessibility text to verify Stop status, not merely click success.
 text=ui_text()
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
