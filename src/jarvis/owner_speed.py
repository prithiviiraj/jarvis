"""Explicit owner hardware timing; installed assets only, no mic/screens/cloud/downloads."""
import os,pathlib,time,json,platform
from .local_models import CATALOG,detect_hardware
from .paths import data_root
from .local_model_files import verified
from .managed_runtime import ManagedRuntime
from .changed_image_latency import ImageProfile,run_changed

def installed(root):
 return [m for m in CATALOG['models']if all(verified(pathlib.Path(root)/'models'/m['id']/f['name'],f)for f in m['files'])]
def run(confirm=False,root=None,output=None):
 if confirm is not True:raise ValueError('Run the reviewed installed-model timing explicitly')
 if os.name!='nt':raise RuntimeError('Windows installed-model speed test required')
 root=pathlib.Path(root or data_root()/'managed-local');models=installed(root)
 if not models:raise ValueError('No verified installed model. Install a model in JARVIS first; this test downloads nothing.')
 if len(models)!=1:raise ValueError('Multiple verified models installed. Select one in JARVIS before a model-specific speed test is supported.')
 out=pathlib.Path(output or data_root()/'diagnostics'/'real-speed.json');out.parent.mkdir(parents=True,exist_ok=True)
 runtime=ManagedRuntime(root,spawn=ImageProfile(),log=None)
 # Native process output cannot use StringIO. Temporary local log holds own-process metadata;
 # discard it after extracting only safe offload/timing lines.
 import tempfile,re
 report={'scope':'Explicit fixed synthetic text-panel timing, no private screen, mic, camera, cloud or download. Legacy text and exact-image repeats are labeled separately; changed frames follow a warmed runtime. Cold model load is separate. Includes transport/prefill/generation. Not conversation-control concurrency.','hardware':detect_hardware(root),'logical_cpus':os.cpu_count(),'platform':platform.system(),'model':models[0]['id'],'image_min_tokens':1024,'image_max_tokens':2048,'result':'incomplete'}
 temp=None
 try:
  temp=tempfile.TemporaryFile(mode='w+',encoding='utf-8');runtime.log=temp
  runtime.start(models[0]['id'],True);deadline=time.monotonic()+300
  while time.monotonic()<deadline:
   s=runtime.check()
   if s['state']=='loaded':break
   if s['state']=='failed':raise RuntimeError(s['error'])
   time.sleep(.5)
  else:raise RuntimeError('Installed model health timeout')
  from .model_latency import ModelLatency
  report['synthetic_text_exact_image_rows']=ModelLatency(runtime).run(True)
  report['changed_image_rows']=run_changed(runtime)
  report['all_fixture_quality_pass']=all(r['quality_pass']for r in report['changed_image_rows']);report['result']='measured'
 except Exception as e:report['result']='failed';report['error']=type(e).__name__+': '+str(e);raise
 finally:
  report['stop_state']=runtime.stop()
  if temp:
   temp.seek(0);raw=temp.read();temp.close()
   # Preserve numeric measurements and actual GPU offload count, never entire log paths.
   report['offloaded_layers']=re.findall(r'offloaded (\d+/\d+) layers to GPU',raw)
   report['image_batch_tokens']=re.findall(r'n_tokens_batch = (\d+)',raw)
   report['runtime_timings_ms']=re.findall(r'(prompt eval|eval) time\s*=\s*([\d.]+) ms',raw)
  report['hardware'].pop('error',None)
  out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('Local speed report saved:',out,flush=True)
 return report
