"""All retained renderer safety/regression fixtures. No native acceptance claim."""
import json,pathlib,socket,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent
checks=sorted(p.name for p in root.glob('*smoke.mjs') if p.name!='native-smoke.mjs')
checks += ['owner-current-preview.mjs','owner-news-preview.mjs','owner-bigfoot-preview.mjs','narrow-pixels.mjs','conductor-handoff.mjs','news-handoff.mjs','calendar-handoff.mjs','orientation-handoff.mjs']
checks += ['bigfoot-'+name+'-preview.mjs' for name in ['shell','model-session','shortcut','microphone','responsive','speech-setup','desktop','live-voice']]
assert len(checks)==len(set(checks))
out=root/'ui-evidence';out.mkdir(exist_ok=True)
# Generate exact Bridge fixtures instead of relying on a prior local test run.
subprocess.run([sys.executable,'night-fix-bridge-state.py'],cwd=root,check=True)
subprocess.run([sys.executable,'polish-state.py'],cwd=root,check=True)
server=subprocess.Popen([sys.executable,'-m','http.server','8765','--bind','127.0.0.1','--directory',str(root/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
rows=[]
try:
 for attempt in range(100):
  if server.poll() is not None:raise RuntimeError('Fixture HTTP server exited; do not use an unknown existing server')
  try:
   with socket.create_connection(('127.0.0.1',8765),timeout=.2):break
  except OSError:time.sleep(.05)
 else:raise RuntimeError('Fixture HTTP server never became ready')
 for name in checks:
  started=time.monotonic()
  try:
   result=subprocess.run(['node',name],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
   code=result.returncode;text=result.stdout
  except subprocess.TimeoutExpired as error:
   code=124;text=error.stdout.decode()if isinstance(error.stdout,bytes)else error.stdout or ''
  rows.append({'test':name,'code':code,'seconds':round(time.monotonic()-started,3),'output':text})
  (out/'renderer-regression.json').write_text(json.dumps({'scope':'Synthetic Chromium renderer only, not native/model/device acceptance','checks':rows},indent=2),encoding='utf-8')
  print(name,code,rows[-1]['seconds'],flush=True)
  if code:print(text,flush=True)
 assert all(row['code']==0 for row in rows),'Renderer regression failures: '+', '.join(row['test']for row in rows if row['code'])
 print(str(len(rows))+' fresh renderer checks passed. No native/device acceptance claim.',flush=True)
finally:
 server.terminate();server.wait(10)
