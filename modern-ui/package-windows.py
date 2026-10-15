"""Build a no-system-Python portable preview and verify the frozen stdio core."""
import pathlib, shutil, subprocess, json, os, hashlib,queue,threading
root=pathlib.Path(__file__).resolve().parent
out=root/'windows-portable'
if out.exists():shutil.rmtree(out)
out.mkdir()
# Prepared static phone assets only. No listener or automatic network exposure.
shutil.copytree(root/'phone-web',out/'phone-web')
args=['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--exclude-module','pocket_tts','--exclude-module','jarvis.pocket_assets','--exclude-module','jarvis.kitten_assets','--exclude-module','jarvis.experimental.pocket_cpu','--exclude-module','jarvis.experimental.kitten_onnx','--collect-all','lameenc','--collect-all','certifi','--collect-all','cv2','--collect-all','playwright','--collect-all','laya','--collect-all','torch','--collect-all','transformers','--collect-all','tokenizers','--collect-all','huggingface_hub','--collect-all','safetensors','--collect-all','model2vec','--collect-all','tzdata','--add-data',str(root.parent/'src/jarvis/chat-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/embedding-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/laya-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/experimental/moonshine-assets.json')+';jarvis/experimental','--distpath',str(root/'frozen-dist'),'--workpath',str(root/'frozen-work'),str(root/'frozen-entry.py')]
if os.environ.get('JARVIS_PACKAGE_VOICE')=='1':args[3:3]=['--collect-all','onnxruntime','--collect-all','ctranslate2','--collect-all','faster_whisper','--collect-all','sounddevice','--collect-all','_sounddevice_data','--add-data',str(root/'native-voice')+';native-voice']
subprocess.run(args,check=True)
shutil.copytree(root/'frozen-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
if os.environ.get('JARVIS_BUNDLE_MODELS')=='1':
 if not(root/'bundled-models/manifest.json').is_file():raise RuntimeError('Verified bundled asset manifest missing')
 shutil.copytree(root/'bundled-models',out/'bundled-models')
 subprocess.run([str(out/'backend/jarvis-local-core.exe'),'--bundle-self-test'],check=True,timeout=900)
if not (root/'embedding-runtime/jarvis-embedding.exe').is_file():raise RuntimeError('Isolated embedding runtime missing from build; do not silently ship incomplete retrieval')
shutil.copytree(root/'embedding-runtime',out/'embedding-runtime')
(out/'START HERE.txt').write_text("JARVIS FIRST CANDIDATE - FEATURES AND LIMITS\n\nKeep your accepted working build. Extract this whole folder and open JARVIS.exe. Windows10/11x64 and WebView2 required. Unsigned app: never disable antivirus.\n\nThis candidate has the unified FIRST workspace, managed local Qwen chat/vision setup, explicit screen capture and reviewed desktop safeguards, local English speech software, and the installed-model --real-speed-test command. No claim of ownerGPU speed, physical microphone/speaker acceptance, natural Tanglish output or complete autonomous desktop control.\n\nFIRST SETUP\nSettings > Choose connection: Check this computer, review the recommended managed model download, then review Start and test. Pinned files are checksum verified. Chat works after the model is loaded; no LM Studio is needed for the managed route. Models and runtime download separately and use severalGB of disk/RAM. The included speech assets are verified/imported on first use; microphone starts OFF.\nStart listening on Home is continuous without holding Alt: it pauses for replies and resumes until Stop. Optional Ctrl+Alt interrupt/listen cancels the current reply and resumes the same consented microphone session. Legacy hold mode is separate and local-only.\nBrowserOS neo remains a separate unmodified pinned installer, with its own local MCP server. Settings > Explore tools has the own-tab Start, exact HTTPS, bounded scroll, current JPEG view, current-page news capture, and Stop adapter. Numbered YouTube selection works only with verified desktop-result anchor bindings; unsupported layouts fail closed. No arbitrary clicks, forms, sends or account imports. Disable BrowserOS telemetry first. Installer: https://github.com/browseros-ai/BrowserOS/releases/download/browserclaw/v0.51.1.2/BrowserOS_neo_v0.51.1.2_x64_installer.exe SHA256 7f3734afd6dbeb237023caab8028641a1c94868d5a244bfcfe95530cb810b191 . Run the separate installer yourself; the adapter does not install it automatically.\n\nVoice: Test Microphone is a five-second LOCAL level test, not speech accuracy acceptance. Local speech input is the default. Automatic language detection is available but base Tamil/Tanglish accuracy failed diagnostics. Kokoro English voices work in prerecorded software tests, not proof that your physical audio device works. Use headphones; speaker echo cancellation is not implemented.\n\nOPTIONAL GROQ RECOGNITION\nCreate your own Free-tier Groq account/key. Save the key locally in the password field in Settings > Connections, slot1 set to Groq (Windows Credential Manager). Do not paste keys into chat. Select Settings > Set up voice > Recognition route > Groq and review the session-only audio-sharing notice. Each microphone speech segment goes to Groq whisper-large-v3 only for transcription. No screen/history is sent by that adapter. There is no silent local-to-cloud fallback, no retry, and no saved microphone file. Actual quotas/billing are your account's responsibility; JARVIS cannot prove the account is free. Live Tanglish quality is NOT verified while keyless. Legacy global hold-to-talk stays local-only; current-session Ctrl+Alt interrupt/listen keeps the selected recognition route. Stop prevents later transcript use but cannot retract an already sent request. Speech output remains local Kokoro; no Gemini cloud TTS or voice cloning is included.\n\nSCREEN AND CONTROL\nOnly explicit selected-screen/window capture. Ordinary conversation does not open a visual popup. Desktop input is reviewed against an exact target window, with cancellation and source readback. This is not continuous video understanding, game coaching, Maya editing, split-second painting, or simultaneous live conversation plus autonomous control acceptance.\n\nOWNER SPEED TEST\nAfter installing exactly one managed model, run backend\\jarvis-local-core.exe --real-speed-test from this extracted folder. It checks installed assets only, never downloads from that command and never opens mic/camera/screen/cloud. Fixed synthetic text/exact-image/changed-image timings are kept separate. First voice Start prepares27short local feedback clips before opening the microphone; later starts reuse bounded RAM clips. Its cost has not yet been accepted on the owner laptop. Output is saved to the local JARVIS diagnostics real-speed.json path printed by the command. This is not a full app acceptance result. Large-label synthetic images do not prove dense desktop reading.\n\nSAFETY AND DATA\nMic/camera/screen/cloud routes start OFF or require explicit review. Existing chat/API routes are separate from the Groq audio-only adapter. Local chat history is plain text with bounds; deletion does not erase external backups. No live Telegram send, invoice issuance/payment, automatic file opening, voice cloning or paid API activation is part of this candidate. Existing advanced tools remain bounded and reviewed. Optional features needing accounts, models or peripherals are not assumed ready.\n\nKeep backend, licenses, bundled-models and other folders together. Report any setup/voice/model error instead of replacing your accepted build. This is a first candidate, not all features completed.\n",encoding='utf-8')
licenses=out/'licenses';licenses.mkdir()
shutil.copytree(root/'bundle-notices',licenses/'bundled-models',dirs_exist_ok=True)
shutil.copy2(root.parent/'optional-laya/APACHE-2.0.txt',licenses/'EMBEDDING-APACHE-2.0.txt')
shutil.copy2(root/'node_modules/3d-force-graph/LICENSE',licenses/'FORCE-GRAPH-MIT.txt')
(licenses/'BUNDLED-MODELS.txt').write_text('Pinned model sources and hashes are in bundled-models/manifest.json. Whisper and Silero: MIT. Kokoro: Apache2. Laya: Apache2. EmbeddingGemma2: Apache2, subject to Google Prohibited Use Policy https://ai.google.dev/gemma/prohibited_use_policy ; source https://huggingface.co/google/embeddinggemma-2 . Do not describe this as unrestricted use. LM Studio chat and vision weights are separate and not included.\n',encoding='utf-8')
shutil.copytree(root/'mp3-notices',licenses/'mp3',dirs_exist_ok=True)
shutil.copy2(root.parent/'LICENSE',licenses/'JARVIS-GPL-3.0.txt')
shutil.copytree(root.parent/'third-party/bigfoot',licenses/'bigfoot',dirs_exist_ok=True)
shutil.copytree(root.parent/'third-party/beautiful-ui',licenses/'beautiful-ui',dirs_exist_ok=True)
# Corresponding application code/build scripts let recipients relink or replace LGPL modules.
import tarfile
with tarfile.open(licenses/'JARVIS-corresponding-application-source.tar.gz','w:gz')as archive:
 for name in subprocess.check_output(['git','ls-files'],cwd=root.parent,text=True).splitlines():
  p=root.parent/name
  if p.is_file():archive.add(p,arcname=name)
shutil.copy2(root.parent/'optional-search/MIT.txt',licenses/'MODEL2VEC-MIT.txt')
(licenses/'MODEL2VEC-SOURCE.txt').write_text('Optional English potion4M model assets15.80MB; MIT official card. https://github.com/MinishLab/model2vec ; https://huggingface.co/minishlab/potion-base-4M . Pinned9b3cff412d30be9ae8603fe10224c224f3401869. No model bundled. Similarity candidates, not factual answers or permissions.\n',encoding='utf-8')
shutil.copy2(root.parent/'optional-laya/APACHE-2.0.txt',licenses/'LAYA-MODEL-APACHE-2.0.txt')
(licenses/'LAYA-SOURCES.txt').write_text('Laya runtime: https://github.com/NandhaKishorM/laya (Apache2). Model: https://huggingface.co/ichenney/laya-browser-v32b , pinned161d54d6000913ff279b0afd1ac77faef8685a9b; Apache2 model card. Torch/Transformers distribution notices retained. Pinned model weights are included only in the verified bundled-model build; other builds use the reviewed download.\n',encoding='utf-8')
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
 start=out/'START HERE.txt';start.write_text(start.read_text().replace('Verified bundled speech weights are imported into the local cache on first launch; other builds need the reviewed download.','Local speech runtime and verified weights are bundled when the bundle verification is enabled, otherwise use the reviewed download. Microphone starts OFF. Headphones required. Default voice is half-duplex. Interrupt on headphones is opt-in and experimental; not verified on your hardware. No acoustic echo cancellation (AEC). Microphone starts OFF.'))
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
 # Actual frozen news URL dialogue remains an inert source review.
 for phrase in ('Lyra show news with pictures from https://example.com/news',):
  p.stdin.write(json.dumps({'command':'chat','text':phrase})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
 assert reply['data']['news']['pending']['value']=='https://example.com/news'and not reply['data']['news']['observed_url']and reply['data']['news']['text_preview']is None,reply
 assert reply['data']['neural']['row']['kind']=='news'and reply['data']['neural']['picture']is None and reply['data']['browser']['status']['state']=='off',reply
 (root/'ui-evidence/frozen-news-source-dialogue.json').write_text(json.dumps({'scope':'Actual frozen supplied news source draft, no external page/model/speech','news':reply['data']['news']},indent=2),encoding='utf-8')
 p.stdin.write(json.dumps({'command':'news-cancel'})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok']and reply['data']['news']['pending']is None and reply['data']['neural']['row']is None,reply
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
 # Actual frozen conversational unsaved date move; no save/open/model call.
 original=reply['data']['calendar']['pending']
 for phrase in ('show calendar appointment','calendar title Move fixture','calendar start 2026-10-11T23:30','calendar end 2026-10-12T00:30','calendar timezone Asia/Kolkata','move calendar draft to 2026-10-13'):
  p.stdin.write(json.dumps({'command':'chat','text':phrase})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
 moved=reply['data']['calendar']['draft'];assert moved['start']=='2026-10-13T23:30'and moved['end']=='2026-10-14T00:30'and moved['weekday']=='Tuesday',moved
 assert reply['data']['calendar']['pending']is None and not reply['data']['calendar']['events'] and not reply['data']['calendar']['result'],reply
 assert reply['data']['neural']['row']['kind']=='calendar'and '2026-10-13'in reply['data']['neural']['row']['text'],reply
 (root/'ui-evidence/frozen-calendar-move-draft.json').write_text(json.dumps({'scope':'Actual frozen conversational date move, unsaved draft only, no external calendar/app/model','draft':moved},indent=2),encoding='utf-8')
 p.stdin.write(json.dumps({'command':'calendar-cancel'})+'\n');p.stdin.flush();assert json.loads(lines.get(timeout=30))['ok']
 p.stdin.write(json.dumps({'command':'calendar-preview','event':{k:original[k]for k in ('title','start','end','place','notes','timezone')}})+'\n');p.stdin.flush();reply=json.loads(lines.get(timeout=30));assert reply['ok'],reply
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
def file_digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':file_digest(p)} for p in out.rglob('*') if p.is_file()}
(root/'ui-evidence/portable-manifest.json').write_text(json.dumps(manifest,indent=2))
