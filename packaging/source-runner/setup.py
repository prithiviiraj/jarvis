"""Owner-run dependency installation and verified model downloads. No keys accepted."""
import os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
if sys.version_info[:2]!=(3,12):raise SystemExit('Python 3.12 is required. Install it from python.org and rerun SETUP.cmd.')
VENV=ROOT/'.venv';PY=VENV/'Scripts/python.exe'
def run(args):
 for attempt in range(3):
  result=subprocess.run(args,cwd=ROOT)
  if result.returncode==0:return
  if attempt<2:print('Network/setup step failed. Retrying with certificate checks ON...');time.sleep(3*(attempt+1))
 raise SystemExit('Setup failed. No TLS checks were disabled. Retry SETUP.cmd to resume; if Jio blocks downloads, use another network/hotspot. Never paste keys into chat.')
if not PY.exists():run([sys.executable,'-m','venv',str(VENV)])
run([str(PY),'-m','pip','install','--retries','5','--timeout','60','--index-url','https://pypi.org/simple','-r',str(ROOT/'requirements.txt')])
env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
code="from jarvis import models,voice_assets; from jarvis.paths import ensure_layout; from jarvis.native_frontend import verified_frontend; p=ensure_layout()/'models'; verified_frontend(); models.download(p,consent=True); voice_assets.download(p/'voices',consent=True); print('Verified speech models ready. Microphone and cloud remain OFF.')"
for attempt in range(3):
 result=subprocess.run([str(PY),'-c',code],cwd=ROOT,env=env)
 if result.returncode==0:break
 env['JARVIS_CERTIFI_TRUST']='1'
 if attempt==2:raise SystemExit('Verified model download failed. Rerun SETUP.cmd to resume, or use a different network. TLS stays ON.')
 time.sleep(3*(attempt+1))
(ROOT/'SETUP-OK.txt').write_text('Experimental source runner setup completed. Not hardware/live-provider acceptance.\n')
print('Setup finished. Double-click LAUNCH.cmd. Read README-FIRST.md before enabling microphone or Groq.')
