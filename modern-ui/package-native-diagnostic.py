"""Native iteration only. Not a shipping build or voice/model acceptance."""
import pathlib,shutil,subprocess,json,hashlib,sys
root=pathlib.Path(__file__).resolve().parent
out=root/'native-diagnostic'
def source_fingerprint():
 files=[]
 for base in (root.parent/'src',root/'src',root/'src-tauri/src'):
  files.extend(p for p in base.rglob('*') if p.is_file() and p.suffix not in ('.pyc',) and '__pycache__' not in str(p))
 files.extend(root/p for p in ('frozen-entry.py','package-lock.json','src-tauri/Cargo.lock','src-tauri/tauri.conf.json'))
 h=hashlib.sha256()
 for p in sorted(files):h.update(str(p.relative_to(root.parent)).encode());h.update(p.read_bytes())
 return h.hexdigest()
if '--verify-reuse' in sys.argv:
 assert (out/'source-fingerprint.txt').read_text()==source_fingerprint(),'Product sources changed; build a new diagnostic core'
 print('Diagnostic artifact source fingerprint matches current product sources');sys.exit(0)
if out.exists():shutil.rmtree(out)
out.mkdir()
subprocess.run(['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--collect-all','certifi','--collect-all','cv2','--collect-all','playwright','--collect-all','tzdata','--exclude-module','torch','--exclude-module','transformers','--exclude-module','onnxruntime','--exclude-module','ctranslate2','--exclude-module','pocket_tts','--add-data',str(root.parent/'src/jarvis/laya-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/experimental/moonshine-assets.json')+';jarvis/experimental','--distpath',str(root/'diagnostic-dist'),'--workpath',str(root/'diagnostic-work'),str(root/'frozen-entry.py')],check=True)
shutil.copytree(root/'diagnostic-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
(out/'DIAGNOSTIC ONLY.txt').write_text('UI/native iteration only. Real frozen core and Win32/WebView2/Edge boundaries. Heavy speech/Laya/embedding runtimes excluded. No shipping, voice, model quality or complete package claim. Full modern-voice baseline remains required.')

(out/'source-fingerprint.txt').write_text(source_fingerprint())
