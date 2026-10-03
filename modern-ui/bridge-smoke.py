"""Actual stdio process verification, no model/sensors/network."""
import subprocess,pathlib,json,sys,os
exe=pathlib.Path('src-tauri/target/release/jarvis-modern-ui.exe').resolve();target=exe.parent/'backend'/'src'
import shutil
shutil.copytree('../src',target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
env=dict(os.environ,PYTHONPATH=str(target));p=subprocess.Popen([sys.executable,'-u','-m','jarvis.ui_bridge'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env=env)
checks=[]
try:
 for req in [{'command':'status'},{'command':'select','name':'DEX'},{'command':'pause'},{'command':'shell'},{'command':'close'}]:
  p.stdin.write(json.dumps(req)+'\n');p.stdin.flush();r=json.loads(p.stdout.readline());checks.append(r)
 assert checks[0]['data']['awareness']['camera']=='off';assert checks[1]['data']['selected']=='DEX';assert not checks[2]['data']['messages'];assert not checks[3]['ok'];assert checks[4]['ok'];p.wait(5)
 pathlib.Path('ui-evidence/bridge-checks.json').write_text(json.dumps({'actual_stdio_process':True,'checks':['off start','persona select','pause clear','arbitrary shell rejected','orderly close'],'model_requests':0},indent=2))
finally:
 if p.poll() is None:p.terminate()
