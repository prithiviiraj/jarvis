"""Native iteration only. Not a shipping build or voice/model acceptance."""
import pathlib,shutil,subprocess,json
root=pathlib.Path(__file__).resolve().parent
out=root/'native-diagnostic'
if out.exists():shutil.rmtree(out)
out.mkdir()
subprocess.run(['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','jarvis-local-core','--paths',str(root.parent/'src'),'--collect-submodules','jarvis','--collect-all','certifi','--collect-all','cv2','--collect-all','playwright','--collect-all','tzdata','--exclude-module','torch','--exclude-module','transformers','--exclude-module','onnxruntime','--exclude-module','ctranslate2','--exclude-module','pocket_tts','--add-data',str(root.parent/'src/jarvis/laya-assets.json')+';jarvis','--add-data',str(root.parent/'src/jarvis/experimental/moonshine-assets.json')+';jarvis/experimental','--distpath',str(root/'diagnostic-dist'),'--workpath',str(root/'diagnostic-work'),str(root/'frozen-entry.py')],check=True)
shutil.copytree(root/'diagnostic-dist/jarvis-local-core',out/'backend')
shutil.copy2(root/'src-tauri/target/release/jarvis-modern-ui.exe',out/'JARVIS.exe')
(out/'DIAGNOSTIC ONLY.txt').write_text('UI/native iteration only. Real frozen core and Win32/WebView2/Edge boundaries. Heavy speech/Laya/embedding runtimes excluded. No shipping, voice, model quality or complete package claim. Full modern-voice baseline remains required.')
