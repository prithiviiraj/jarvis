"""Build a no-system-Python portable preview and verify the frozen stdio core."""
import pathlib, shutil, subprocess, json, os, hashlib,queue,threading
root=pathlib.Path(__file__).resolve().parent
out=root/'windows-portable'
if out.exists():shutil.rmtree(out)
out.mkdir()
args=['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--collect-all','cv2','--distpath',str(root/'frozen-dist'),'--workpath',str(root/'frozen-work'),str(root/'frozen-entry.py')]
if os.environ.get('JARVIS_PACKAGE_VOICE')=='1':args[3:3]=['--collect-all','onnxruntime','--collect-all','ctranslate2','--collect-all','faster_whisper','--collect-all','sounddevice','--collect-all','_sounddevice_data','--add-data',str(root/'native-voice')+';native-voice']
subprocess.run(args,check=True)
shutil.copytree(root/'frozen-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
(out/'START HERE.txt').write_text("JARVIS MODERN WINDOWS PREVIEW\n\n1. Extract the whole ZIP into a folder.\n2. Double-click JARVIS.exe. No Python, Node or build commands are needed.\n3. Faces appear first. Right-click them and choose Open workspace.\n4. Connect local core. Camera and microphone start OFF.\n\nKeep the backend folder beside JARVIS.exe. This is an unsigned preview; Windows may warn about the publisher. Do not disable your antivirus. Windows 10/11 x64 with Microsoft Edge WebView2 is required.\n\nFor chat/judgment, open LM Studio, load one model, and start its local server. No model is included. Cloud is disabled. Camera support is included and requires your explicit consent. Voice/audio assets and optional speech dependencies are NOT included in this preview. Keep your working JARVIS build; this preview does not replace it.\n",encoding='utf-8')
licenses=out/'licenses';licenses.mkdir()
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
 start=out/'START HERE.txt';start.write_text(start.read_text().replace('Voice/audio assets and optional speech dependencies are NOT included in this preview.','Local speech runtime is bundled. Click Download local voice models (roughly500MB), then Mic ON. Headphones required for this first half-duplex test. No AEC/barge-in yet. Microphone starts OFF.'))
core=out/'backend/jarvis-local-core.exe'
env=dict(os.environ);env.pop('PYTHONPATH',None);env['PATH']=str(pathlib.Path(os.environ['WINDIR'])/'System32')
log=open(root/'ui-evidence/frozen-core-stderr.txt','w')
p=subprocess.Popen([str(core)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,env=env,cwd=out)
lines=queue.Queue()
def drain():
 for line in p.stdout:lines.put(line)
 lines.put(None)
threading.Thread(target=drain,daemon=True).start()
checks=[]
try:
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
(root/'ui-evidence/frozen-core-checks.json').write_text(json.dumps({'bundled_core':True,'system_python_removed_from_PATH':True,'checks':checks},indent=2))
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file()}
(root/'ui-evidence/portable-manifest.json').write_text(json.dumps(manifest,indent=2))
