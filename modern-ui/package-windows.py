"""Build a no-system-Python portable preview and verify the frozen stdio core."""
import pathlib, shutil, subprocess, json, os, hashlib
root=pathlib.Path(__file__).resolve().parent
out=root/'windows-portable'
if out.exists():shutil.rmtree(out)
out.mkdir()
subprocess.run(['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--collect-all','cv2','--distpath',str(root/'frozen-dist'),'--workpath',str(root/'frozen-work'),str(root/'frozen-entry.py')],check=True)
shutil.copytree(root/'frozen-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
(out/'START HERE.txt').write_text("JARVIS MODERN WINDOWS PREVIEW\n\n1. Extract the whole ZIP into a folder.\n2. Double-click JARVIS.exe. No Python, Node or build commands are needed.\n3. Faces appear first. Right-click them and choose Open workspace.\n4. Connect local core. Camera and microphone start OFF.\n\nKeep the backend folder beside JARVIS.exe. This is an unsigned preview; Windows may warn about the publisher. Do not disable your antivirus. Windows 10/11 x64 with Microsoft Edge WebView2 is required.\n\nFor chat/judgment, open LM Studio, load one model, and start its local server. No model is included. Cloud is disabled. Camera support is included and requires your explicit consent. Voice/audio assets and optional speech dependencies are NOT included in this preview. Keep your working JARVIS build; this preview does not replace it.\n",encoding='utf-8')
licenses=out/'licenses';licenses.mkdir()
# Preserve upstream distribution license files, including binary third-party notices.
import importlib.metadata as md
for name in ['numpy','opencv-python','pyinstaller','pyinstaller-hooks-contrib']:
 dist=md.distribution(name)
 for f in dist.files or []:
  if any(word in str(f).lower() for word in ('license','copying','notice')):
   src=pathlib.Path(dist.locate_file(f))
   if src.is_file():
    target=licenses/name/str(f);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
(licenses/'README.txt').write_text('Third-party license texts retained from bundled distributions. JARVIS source is in the owner repository.\n',encoding='utf-8')
core=out/'backend/jarvis-local-core.exe'
env=dict(os.environ);env.pop('PYTHONPATH',None);env['PATH']=str(pathlib.Path(os.environ['WINDIR'])/'System32')
p=subprocess.Popen([str(core)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env=env,cwd=out)
checks=[]
try:
 for req in [{'command':'status'},{'command':'select','name':'DEX'},{'command':'apps','enabled':True},{'command':'judgment','enabled':True,'context_consent':True},{'command':'pause'},{'command':'shell'},{'command':'close'}]:
  p.stdin.write(json.dumps(req)+'\n');p.stdin.flush();checks.append(json.loads(p.stdout.readline()))
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
(root/'ui-evidence/frozen-core-checks.json').write_text(json.dumps({'bundled_core':True,'system_python_removed_from_PATH':True,'checks':checks},indent=2))
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file()}
(root/'ui-evidence/portable-manifest.json').write_text(json.dumps(manifest,indent=2))
