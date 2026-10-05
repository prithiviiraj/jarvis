"""Build a no-system-Python portable preview and verify the frozen stdio core."""
import pathlib, shutil, subprocess, json, os, hashlib,queue,threading
root=pathlib.Path(__file__).resolve().parent
out=root/'windows-portable'
if out.exists():shutil.rmtree(out)
out.mkdir()
args=['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--collect-all','cv2','--collect-all','playwright','--collect-all','laya','--collect-all','torch','--collect-all','transformers','--collect-all','tokenizers','--collect-all','huggingface_hub','--collect-all','safetensors','--add-data',str(root.parent/'src/jarvis/laya-assets.json')+';jarvis','--distpath',str(root/'frozen-dist'),'--workpath',str(root/'frozen-work'),str(root/'frozen-entry.py')]
if os.environ.get('JARVIS_PACKAGE_VOICE')=='1':args[3:3]=['--collect-all','onnxruntime','--collect-all','ctranslate2','--collect-all','faster_whisper','--collect-all','sounddevice','--collect-all','_sounddevice_data','--add-data',str(root/'native-voice')+';native-voice']
subprocess.run(args,check=True)
shutil.copytree(root/'frozen-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
(out/'START HERE.txt').write_text("JARVIS WINDOWS - SETUP AND SAFETY\n\n1. Extract the whole ZIP into a folder.\n2. Double-click JARVIS.exe. No Python, Node or build commands are needed.\n3. The main workspace opens first. Floating avatars are removed. Transcript-only mode is ON by default. Minimizing or closing an enabled workspace shows the transparent conversation text on the right. Hover on the transcript for OPEN or Hide. Transcript ON/OFF is saved across launches and OFF never comes back on minimize. Hiding the transcript reopens the workspace so controls remain reachable. When Transcript is OFF, closing the workspace exits. Restoring the workspace hides duplicate transcript text. This never enables microphone or camera.\n4. Connect core / check brains. Check LM Studio status in Settings > Brain & APIs. Camera and microphone start OFF.\n5. For cloud-first: enable API slots, enter keys in the password fields, confirm share-context and free/no-billing access, press Save & test on that account. It saves the entered key and current slot settings before testing. Empty model selects an available approved model when tested. Choose primary slot per persona.\n6. Reo is a silent text-only action specialist. Settings > Tools includes reviewed Laya model download (1.32GB), CPU loading and stop inside JARVIS; no separate app/server. Laya only proposes observed links/scroll for exact review, never full autonomous agency. SeveralGB RAM/disk may be needed.\n7. Team room generates five voiced perspectives concurrently, shows/speaks them in order, then a real leader conclusion. Requires enabled working APIs for parallel cloud speed. LM Studio last fallback runs one inference at a time.\n8. Pause all stops sensors, speech and current work, but keeps chats. New chat starts fresh. Chats save locally in plain text, at most50chats/200messages each; oldest removed at limit. Delete removes local entries, not backups. Cloud consent resets each launch.\n\nKeep the backend folder beside JARVIS.exe. This is unsigned software; Windows may warn about the publisher. Do not disable your antivirus. Windows 10/11 x64 with Microsoft Edge WebView2 is required.\n\nFor local fallback/judgment, open LM Studio, load one model, and start its local server. No model is included. Enabled user-confirmed free APIs are primary for chat/voice; no paid fallback. Proactive judgment is local-only, needs allowed app/camera events and is suppressed during microphone sessions to avoid echo. Camera support is included and requires your explicit consent. Voice model weights must be downloaded inside the app. Keep your working JARVIS build until laptop acceptance. Account billing cannot be verified by these APIs; do not enable paid/billing accounts.\n",encoding='utf-8')
licenses=out/'licenses';licenses.mkdir()
shutil.copy2(root.parent/'optional-laya/APACHE-2.0.txt',licenses/'LAYA-MODEL-APACHE-2.0.txt')
(licenses/'LAYA-SOURCES.txt').write_text('Laya runtime: https://github.com/NandhaKishorM/laya (Apache2). Model: https://huggingface.co/ichenney/laya-browser-v32b , pinned161d54d6000913ff279b0afd1ac77faef8685a9b; Apache2 model card. Torch/Transformers distribution notices retained. Model weights are not bundled; reviewed in-app download only.\n',encoding='utf-8')
# Preserve upstream distribution license files, including binary third-party notices.
import importlib.metadata as md
for dist in md.distributions():
 name=dist.metadata['Name']
 for f in dist.files or []:
  if any(word in str(f).lower() for word in ('license','copying','notice')):
   src=pathlib.Path(dist.locate_file(f))
   if src.is_file():
    target=licenses/name/str(f);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
(licenses/'README.txt').write_text('Third-party license texts retained from bundled distributions. JARVIS source is in the owner repository.\n',encoding='utf-8')
if os.environ.get('JARVIS_PACKAGE_VOICE')=='1':
 shutil.copytree(root/'speech-notices',licenses/'speech',dirs_exist_ok=True)
 start=out/'START HERE.txt';start.write_text(start.read_text().replace('Voice model weights must be downloaded inside the app.','Local speech runtime is bundled. Click Download local voice models (roughly500MB), then Mic ON. Headphones required. Default voice is half-duplex. Interrupt on headphones is opt-in and experimental; not verified on your hardware. No acoustic echo cancellation (AEC). Microphone starts OFF.'))
core=out/'backend/jarvis-local-core.exe'
env=dict(os.environ);env.pop('PYTHONPATH',None);env['PATH']=str(pathlib.Path(os.environ['WINDIR'])/'System32');env['JARVIS_DATA_DIR']=str(root/'ui-evidence'/'isolated-brain-test')
log=open(root/'ui-evidence/frozen-core-stderr.txt','w')
p=subprocess.Popen([str(core)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,env=env,cwd=out)
lines=queue.Queue()
def drain():
 for line in p.stdout:lines.put(line)
 lines.put(None)
threading.Thread(target=drain,daemon=True).start()
checks=[]
try:
 # Actual OS secret store round-trip under isolated CI app data; never a real API key.
 credential_test='groq/slot5'
 try:
  for req in [{'command':'key-save','slot':'slot5','kind':'groq','secret':'ci-fixture-not-a-real-api-key'}, {'command':'brain-save','slots':[{'id':'slot5','provider':'groq','model':'llama-3.1-8b-instant','enabled':True}],'assignments':{}}]:
   p.stdin.write(json.dumps(req)+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
  assert reply['data']['brains']['slots'][0]['key_present'] is True
  assert 'ci-fixture-not-a-real-api-key' not in json.dumps(reply)
  p.stdin.write(json.dumps({'command':'key-delete','slot':'slot5','kind':'groq'})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok']
  assert reply['data']['brains']['slots'][0]['key_present'] is False
  p.stdin.write(json.dumps({'command':'brain-save','slots':[],'assignments':{}})+'\n');p.stdin.flush();assert json.loads(lines.get(timeout=30))['ok']
 finally:
  import sys
  sys.path.insert(0,str(root.parent/'src'))
  from jarvis.security import WindowsCredentials
  WindowsCredentials().delete('groq/slot5')
 for req in [{'command':'status'},{'command':'select','name':'DEX'},{'command':'apps','enabled':True},{'command':'judgment','enabled':True,'context_consent':True},{'command':'pause'},{'command':'shell'},{'command':'close'}]:
  p.stdin.write(json.dumps(req)+'\n');p.stdin.flush();
  line=lines.get(timeout=30)
  if not line:raise RuntimeError('Frozen core exited: '+str(p.poll()))
  print('Frozen reply:',line.strip(),flush=True);checks.append(json.loads(line))
 assert checks[0]['data']['awareness']['camera']=='off'
 assert checks[1]['data']['selected']=='DEX'
 assert checks[2]['data']['awareness']['app_monitor'] is True
 assert checks[3]['data']['judgment']['enabled'] is True
 assert checks[4]['data']['awareness']['app_monitor'] is False
 assert checks[4]['data']['judgment']['enabled'] is False
 assert checks[5]['ok'] is False and checks[6]['ok'] is True
 p.wait(10)
finally:
 if p.poll() is None:p.kill()
 log.close()
from jarvis.history_acceptance import run as history_acceptance
(root/'ui-evidence/frozen-history-checks.json').write_text(json.dumps(history_acceptance(str(core)),indent=2))
(root/'ui-evidence/frozen-core-checks.json').write_text(json.dumps({'bundled_core':True,'system_python_removed_from_PATH':True,'checks':checks},indent=2))
from jarvis.connectors_acceptance import run as connectors_acceptance
(root/'ui-evidence/frozen-connectors-checks.json').write_text(json.dumps(connectors_acceptance(str(core)),indent=2))
(licenses/'KITTEN-NOTICE.txt').write_text('Optional KittenTTS nano15M int8 weights: KittenML, Apache License2.0. Model assets downloaded only after approval. Source https://github.com/kittenml/kittentts . JARVIS uses its existing MIT native pronunciation, not upstream eSpeak. XTTS weights and upstream package not bundled. Playwright Apache2 notices retained above.\n',encoding='utf-8')
# Exclude only bundled PortAudio upstream CI automation, never runtime/license files.
portaudio_ci=out/'backend/_internal/_sounddevice_data/portaudio-binaries/.github'
if portaudio_ci.exists():shutil.rmtree(portaudio_ci)
# Upstream NumPy hidden test maps are omitted by artifact upload, never needed at runtime.
for p in (out/'backend/_internal/numpy/f2py/tests').rglob('.f2py_f2cmap'):p.unlink()
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file()}
(root/'ui-evidence/portable-manifest.json').write_text(json.dumps(manifest,indent=2))
