"""Build a no-system-Python portable preview and verify the frozen stdio core."""
import pathlib, shutil, subprocess, json, os, hashlib,queue,threading
root=pathlib.Path(__file__).resolve().parent
out=root/'windows-portable'
if out.exists():shutil.rmtree(out)
out.mkdir()
# Prepared static phone assets only. No listener or automatic network exposure.
shutil.copytree(root/'phone-web',out/'phone-web')
args=['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--exclude-module','pocket_tts','--exclude-module','jarvis.pocket_assets','--exclude-module','jarvis.kitten_assets','--exclude-module','jarvis.experimental.pocket_cpu','--exclude-module','jarvis.experimental.kitten_onnx','--collect-all','lameenc','--collect-all','certifi','--collect-all','cv2','--collect-all','playwright','--collect-all','laya','--collect-all','torch','--collect-all','transformers','--collect-all','tokenizers','--collect-all','huggingface_hub','--collect-all','safetensors','--collect-all','model2vec','--collect-all','tzdata','--add-data',str(root.parent/'src/jarvis/laya-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/experimental/moonshine-assets.json')+';jarvis/experimental','--distpath',str(root/'frozen-dist'),'--workpath',str(root/'frozen-work'),str(root/'frozen-entry.py')]
if os.environ.get('JARVIS_PACKAGE_VOICE')=='1':args[3:3]=['--collect-all','onnxruntime','--collect-all','ctranslate2','--collect-all','faster_whisper','--collect-all','sounddevice','--collect-all','_sounddevice_data','--add-data',str(root/'native-voice')+';native-voice']
subprocess.run(args,check=True)
shutil.copytree(root/'frozen-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
if not (root/'embedding-runtime/jarvis-embedding.exe').is_file():raise RuntimeError('Isolated embedding runtime missing from build; do not silently ship incomplete retrieval')
shutil.copytree(root/'embedding-runtime',out/'embedding-runtime')
(out/'START HERE.txt').write_text("JARVIS WINDOWS - SETUP AND SAFETY\n\n1. Extract the whole ZIP into a folder.\n2. Double-click JARVIS.exe. No Python, Node or build commands are needed.\n3. The main workspace opens first. Floating avatars are removed. Transcript-only mode is ON by default. Minimizing or closing an enabled workspace shows the transparent conversation text on the right. Hover on the transcript for OPEN or Hide. Transcript ON/OFF is saved across launches and OFF never comes back on minimize. Hiding the transcript reopens the workspace so controls remain reachable. When Transcript is OFF, closing the workspace exits. Restoring the workspace hides duplicate transcript text. This never enables microphone or camera.\n4. Bundled core connects automatically. Cloud API setup needs no LM Studio. Optional local fallback can be checked in Settings > Brain & APIs. Camera and microphone start OFF.\n5. For cloud-first: enable API slots, enter keys in the password fields, confirm share-context and free/no-billing access, press Save & test on that account. It saves the entered key and current slot settings before testing. Empty model selects an available approved model when tested. Choose primary slot per persona.\n6. JARVIS leads the exact three-agent team. LYRA writes and chats. DEX handles code and reviewed action support. Retired custom profiles remain archived and inactive. Settings > Tools has four animated feature buttons. Laya activate starts the bounded direct browser/app session. Advanced browser controls retain optional reviewed model download (1.32GB), CPU loading and review mode. No separate Laya app/server. Laya supports reviewed mode and explicit session activation for direct isolated Edge navigation. Active mode also opens Notepad, Calculator and Paint directly; normal mode remains reviewed. No forms, credentials, sending, payments, shell or file changes. Natural-language understanding returns bounded intent data, not executable code. SeveralGB RAM/disk may be needed.\n7. The knowledge workspace shows actual connected local notes and explicit links. Team options in Settings retains manual discussions; custom profile data stays on disk without active roles. Double-click an answer to edit its local visual draft. Team room uses exactly JARVIS, LYRA and DEX and up to3rounds of actual own-profile replies. Text streams as received; completed clauses speak one voice at a time, then Jarvis concludes. Parallel perspectives are a separate option. Requires enabled working APIs for parallel cloud speed. LM Studio last fallback runs one inference at a time.\n8. EmbeddingGemma shared retrieval runtime is bundled separately beside the core, without changing working Laya. Settings > Search engine checks it and offers the reviewed 1.526GB model download. Text/code/image/audio/video candidates stay local in your selected folder; similarity does not authorize actions. Keep exact/text search until quality is checked. First30seconds only for audio/video; no long-video moments claim.\n9. Pause all stops sensors, speech and current work, but keeps chats. New chat starts fresh. Chats save locally in plain text, at most50chats/200messages each; oldest removed at limit. Delete removes local entries, not backups. Cloud consent resets each launch.\n\nKeep the backend folder beside JARVIS.exe. This is unsigned software; Windows may warn about the publisher. Do not disable your antivirus. Windows 10/11 x64 with Microsoft Edge WebView2 is required.\n\nFor local fallback/judgment, open LM Studio, load one model, and start its local server. No model is included. Enabled user-confirmed free APIs are primary for chat/voice; no paid fallback. Local sensing judgment is separate from Proactive team. Proactive team uses loaded LM Studio every10seconds or API around1minute with jitter. It may choose silence and pauses during microphone/busy sessions. Camera support is included and requires your explicit consent. Voice model weights must be downloaded inside the app. Keep your working JARVIS build until laptop acceptance. Account billing cannot be verified by these APIs; do not enable paid/billing accounts.\n",encoding='utf-8')
licenses=out/'licenses';licenses.mkdir()
shutil.copytree(root/'mp3-notices',licenses/'mp3',dirs_exist_ok=True)
# Corresponding application code/build scripts let recipients relink or replace LGPL modules.
import tarfile
with tarfile.open(licenses/'JARVIS-corresponding-application-source.tar.gz','w:gz')as archive:
 for name in subprocess.check_output(['git','ls-files'],cwd=root.parent,text=True).splitlines():
  p=root.parent/name
  if p.is_file():archive.add(p,arcname=name)
shutil.copy2(root.parent/'optional-search/MIT.txt',licenses/'MODEL2VEC-MIT.txt')
(licenses/'MODEL2VEC-SOURCE.txt').write_text('Optional English potion4M model assets15.80MB; MIT official card. https://github.com/MinishLab/model2vec ; https://huggingface.co/minishlab/potion-base-4M . Pinned9b3cff412d30be9ae8603fe10224c224f3401869. No model bundled. Similarity candidates, not factual answers or permissions.\n',encoding='utf-8')
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
shutil.copy2(root.parent/'optional-turn/BSD-2-Clause.txt',licenses/'SMART-TURN-BSD-2-Clause.txt')
(licenses/'SMART-TURN-SOURCE.txt').write_text('Smart Turn runtime retained internally; no Smart Turn setup controls are exposed. https://github.com/pipecat-ai/smart-turn ; https://huggingface.co/pipecat-ai/smart-turn-v3 . No model bundled. Not echo cancellation.\n',encoding='utf-8')
(licenses/'README.txt').write_text('This application uses lameenc1.8.1 under LGPLv3 and LAME3.100 under LGPLv2. Their exact sources, notices and replacement instructions are in licenses/mp3. Third-party license texts retained from bundled distributions. JARVIS source is in the owner repository.\n',encoding='utf-8')
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
 # Real frozen subprocess boundary without any owner indexing/model download.
 p.stdin.write(json.dumps({'command':'embedding2-check','consent':True})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
 import time
 deadline=time.monotonic()+60
 while reply['data']['embedding2']['busy']and time.monotonic()<deadline:
  time.sleep(.2);p.stdin.write(json.dumps({'command':'status'})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30))
 assert not reply['data']['embedding2']['busy']and not reply['data']['embedding2']['error'],reply
 assert reply['data']['embedding2']['details']['model_bytes']==1525787092,reply
 p.stdin.write(json.dumps({'command':'embedding2-stop'})+'\n');p.stdin.flush();assert json.loads(lines.get(timeout=30))['ok']
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
 # Frozen real local-calendar review/save to isolated managed Downloads fixture.
 import tempfile
 # Redirect only the fixture's Windows known-folder provider in-process is not possible across EXE.
 # Use actual runner Downloads managed vault; CI account is isolated, not owner files.
 for req in [{'command':'obsidian-create','reviewed_name':'Brain of Brain','confirm':True},{'command':'calendar-preview','event':{'title':'CI local calendar fixture','start':'2026-10-07T18:00','end':'2026-10-07T19:00','place':'Synthetic place','notes':'Fixture, no appointment or external sync','timezone':'Asia/Kolkata'}}]:
  p.stdin.write(json.dumps(req)+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
  if req['command']=='obsidian-create':
   import time
   for _ in range(100):
    if not reply['data']['obsidian'].get('busy'):break
    time.sleep(.1);p.stdin.write(json.dumps({'command':'status'})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30))
   assert reply['data']['obsidian']['enabled'],reply
 proposal=reply['data']['calendar']['pending'];assert proposal['weekday']=='Wednesday'
 p.stdin.write(json.dumps({'command':'calendar-save','reviewed':proposal,'confirm':False})+'\n');p.stdin.flush();assert not json.loads(lines.get(timeout=30))['ok']
 p.stdin.write(json.dumps({'command':'calendar-save','reviewed':proposal,'confirm':True})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply;assert any(r['title']=='CI local calendar fixture'for r in reply['data']['calendar']['events'])
 (root/'ui-evidence/frozen-local-calendar-checks.json').write_text(json.dumps({'scope':'Actual frozen Windows local note create/review/save/readback, no real event or external calendar','state':reply['data']['calendar']},indent=2),encoding='utf-8')
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
# Exclude only bundled PortAudio upstream CI automation, never runtime/license files.
portaudio_ci=out/'backend/_internal/_sounddevice_data/portaudio-binaries/.github'
if portaudio_ci.exists():shutil.rmtree(portaudio_ci)
# Upstream NumPy hidden test maps are omitted by artifact upload, never needed at runtime.
for p in (out/'backend/_internal/numpy/f2py/tests').rglob('.f2py_f2cmap'):p.unlink()
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file()}
(root/'ui-evidence/portable-manifest.json').write_text(json.dumps(manifest,indent=2))
