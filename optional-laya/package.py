import pathlib,subprocess,shutil,importlib.metadata as md,json,hashlib
root=pathlib.Path(__file__).resolve().parent;out=root/'portable'
subprocess.run(['python','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','JARVIS-Laya','--collect-all','laya','--collect-all','torch','--collect-all','transformers','--collect-all','tokenizers','--collect-all','huggingface_hub','--collect-all','safetensors','--collect-all','numpy','--distpath',str(root/'dist'),'--workpath',str(root/'work'),str(root/'runtime.py')],check=True)
if out.exists():shutil.rmtree(out)
shutil.copytree(root/'dist/JARVIS-Laya',out);shutil.copy2(root/'assets.json',out/'assets.json')
(out/'SETUP MODELS.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\necho EXPERIMENTAL LAYA MODEL SETUP\r\necho Download 1,322,020,017 bytes (about1.32GB) from Hugging Face.\r\necho Apache2 browser checkpoint161d54d. Local model use can need severalGB RAM.\r\necho Files saved in %%LOCALAPPDATA%%\\JarvisLocal\\models\\laya-browser-v32b-161d54d\r\necho No browser, microphone, server or autonomous action starts.\r\necho Review model license in licenses. Allow this download?\r\nchoice /C YN /N /M "Y=yes N=cancel: "\r\nif errorlevel 2 exit /b\r\nJARVIS-Laya.exe --install-reviewed\r\npause\r\n')
(out/'START LAYA.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\necho Starts a local CPU proposal server on127.0.0.1:8000.\r\necho No model download and no browser execution. Close window to stop.\r\nJARVIS-Laya.exe --serve\r\npause\r\n')
(out/'START HERE.txt').write_text('EXPERIMENTAL OPTIONAL LAYA CPU RUNTIME\n\nExtract this whole ZIP. No Python installation needed.\n1. SETUP MODELS.cmd reviews the1.32GB model download. Cancel changes nothing.\n2. START LAYA.cmd loads verified local assets and serves127.0.0.1:8000 only. No model download during startup. Close that window to stop.\n3. In JARVIS Settings > Tools, enable browser control and experimental Laya separately. Open a reviewed page, read links, enter a goal, ask ONE proposal. Every link or scroll still requires exact Confirm review.\n\nA proposal is not permission or completion. The model can be wrong. No typing, forms, payment, upload, arbitrary site clicking or unattended execution. CPU timings are hardware-specific. No Tamil quality or fast-laptop promise. SeveralGB of runtime/model disk and RAM may be needed. Keep the working JARVIS build.\n\nThis optional runtime is unsigned Windowsx64 software. Do not disable antivirus. Model assets are not inside the runtimeZIP. No private chat history or account keys are sent to this server by the reviewed JARVIS bridge. Manually entered goals and observed link labels can contain information you chose to provide.\n')
licenses=out/'licenses';licenses.mkdir()
for dist in md.distributions():
 for f in dist.files or []:
  if any(x in str(f).lower()for x in ('license','copying','notice')):
   src=pathlib.Path(dist.locate_file(f))
   if src.is_file():
    dst=licenses/dist.metadata['Name']/str(f);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
shutil.copy2(root/'APACHE-2.0.txt',licenses/'MODEL-APACHE-2.0.txt')
(licenses/'SOURCES.txt').write_text('Laya runtime: https://github.com/NandhaKishorM/laya (Apache2).\nModel: https://huggingface.co/ichenney/laya-browser-v32b (model card declares Apache2), pinned161d54d6000913ff279b0afd1ac77faef8685a9b.\nTorch: https://github.com/pytorch/pytorch . Transformers: https://github.com/huggingface/transformers . Distribution notices retained alongside.\n')
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in out.rglob('*')if p.is_file()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
subprocess.run([str(out/'JARVIS-Laya.exe'),'--version'],check=True)
