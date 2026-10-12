"""CI-only real pinned Windows model/runtime diagnostic. Not an owner download."""
import pathlib,sys,os,json,time,threading,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.local_models import CATALOG,detect_hardware
from jarvis.local_model_files import download_checked,extract_runtime
from jarvis.managed_runtime import ManagedRuntime
from jarvis.model_probe import ModelProbe
root=pathlib.Path('managed-proof-data').resolve();evidence=pathlib.Path('managed-proof-evidence');evidence.mkdir(exist_ok=True)
report={'scope':'Real Windows pinned llama.cpp/Qwen4B synthetic text/image diagnostic. Not owner GPU/mic/desktop/control/concurrency acceptance.','started':time.time(),'hardware':detect_hardware(root),'runtime':CATALOG['runtime'],'model':CATALOG['models'][0],'result':'not completed'}
runtime=None;runtime_log=None;runtime_token=None;runtime_token_2=None;latency_probe=None
try:
 if os.name!='nt':raise RuntimeError('Actual Windows runtime proof requires Windows')
 cancel=threading.Event();model=CATALOG['models'][0];archive=root/'downloads'/CATALOG['runtime']['name'];dest=root/'runtime'/CATALOG['runtime']['tag']
 for item,target in [(CATALOG['runtime'],archive),*[(f,root/'models'/model['id']/f['name'])for f in model['files']]]:
  print('Verifying pinned asset',item['name'],flush=True);download_checked(item,target,cancel)
 if not dest.exists():extract_runtime(archive,dest,cancel)
 import subprocess
 help_result=subprocess.run([str(dest/'llama-server.exe'),'--help'],capture_output=True,text=True,timeout=30,cwd=dest)
 (evidence/'llama-server-help.txt').write_text(help_result.stdout+help_result.stderr,encoding='utf-8');report['help_exit']=help_result.returncode
 if help_result.returncode:raise RuntimeError('Pinned llama-server --help failed')
 required=['--api-key','--alias','--mmproj','--ctx-size','--parallel','--n-gpu-layers','--fit','--no-webui','--no-repack']
 missing=[flag for flag in required if flag not in help_result.stdout+help_result.stderr]
 if missing:raise RuntimeError('Pinned runtime flags not verified: '+', '.join(missing))
 runtime_log=(evidence/'owned-runtime.log').open('w',encoding='utf-8');runtime=ManagedRuntime(root,log=runtime_log);runtime.start(model['id'],True);runtime_token=runtime.endpoint['key'];deadline=time.monotonic()+300
 while time.monotonic()<deadline:
  state=runtime.check()
  if state['state']=='loaded':break
  if state['state']=='failed':raise RuntimeError(state['error'])
  time.sleep(1)
 else:raise RuntimeError('Owned llama health did not become loaded in five minutes')
 report['runtime_state']=runtime.snapshot();probe=ModelProbe(runtime);probe.start(True);probe.worker.join(70);report['probe']=probe.snapshot()
 if report['probe']['busy']:probe.stop();raise RuntimeError('Synthetic probe exceeded deadline')
 if any(report['probe'][kind]!='passed'for kind in ('text','image')):raise RuntimeError('Synthetic text/image probe did not pass')
 from jarvis.model_latency import ModelLatency
 latency_probe=ModelLatency(runtime);report['latency']=latency_probe.run(True,cancel)
 report['latency_profiles']={'baseline_8192':report['latency']}
 # Compare a bounded alternate context with identical images/prompts/output limits.
 # This changes only diagnostic process args, not product defaults.
 runtime.stop();report['baseline_stop_state']=runtime.snapshot()
 from jarvis.latency_profiles import DiagnosticProfile
 runtime=ManagedRuntime(root,spawn=DiagnosticProfile(4096),log=runtime_log);runtime.start(model['id'],True);runtime_token_2=runtime.endpoint['key'];deadline=time.monotonic()+300
 while time.monotonic()<deadline:
  state=runtime.check()
  if state['state']=='loaded':break
  if state['state']=='failed':raise RuntimeError(state['error'])
  time.sleep(1)
 else:raise RuntimeError('Comparison profile did not load in five minutes')
 latency_probe=ModelLatency(runtime);report['latency_profiles']['diagnostic_4096']=latency_probe.run(True,cancel)
 report['profile_scope']='Only context size differs. Short synthetic quality has not been graded; do not select a product profile from speed alone. CPU CI is not 6GB owner laptop.'
 report['result']='passed'
except Exception as error:
 report['partial_latency']={'rows':latency_probe.rows,'current':latency_probe.current}if latency_probe else None
 report['result']='failed';report['error']=type(error).__name__+': '+str(error);raise
finally:
 if runtime:runtime.stop();report['stop_state']=runtime.snapshot()
 if runtime_log:
  runtime_log.close();log_path=evidence/'owned-runtime.log';raw=log_path.read_text(encoding='utf-8',errors='replace')
  if runtime_token:raw=raw.replace(runtime_token,'[owned runtime token removed]')
  if runtime_token_2:raw=raw.replace(runtime_token_2,'[owned runtime token removed]')
  log_path.write_text(raw,encoding='utf-8')
 report['finished']=time.time();(evidence/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
