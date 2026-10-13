"""Windows actual frozen owner command diagnostic, not a shipping candidate."""
import pathlib,sys,os,threading,subprocess,json,traceback,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.local_models import CATALOG
from jarvis.local_model_files import download_checked,extract_runtime
from jarvis.paths import data_root
root=data_root()/'managed-local';cancel=threading.Event();model=CATALOG['models'][0];archive=root/'downloads'/CATALOG['runtime']['name'];dest=root/'runtime'/CATALOG['runtime']['tag']
for item,target in [(CATALOG['runtime'],archive),*[(f,root/'models'/model['id']/f['name'])for f in model['files']]]:download_checked(item,target,cancel)
if not dest.exists():extract_runtime(archive,dest,cancel)
# One actual frozen command process. Only synthetic inputs; no application UI or sensors.
exe=pathlib.Path(os.environ.get('JARVIS_CORE_EXE','owner-speed-dist/jarvis-local-core/jarvis-local-core.exe')).resolve()
started=time.monotonic();result=subprocess.run([str(exe),'--real-speed-test'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200)
out=pathlib.Path('owner-speed-evidence');out.mkdir(exist_ok=True)
(out/'command-output.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
report_path=data_root()/'diagnostics'/'real-speed.json'
if report_path.exists():
 raw=json.loads(report_path.read_text(encoding='utf-8'));(out/'real-speed.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
else:raise RuntimeError('Actual frozen command produced no report')
(out/'proof.json').write_text(json.dumps({'frozen_command':'jarvis-local-core.exe --real-speed-test','exit_code':result.returncode,'elapsed_s':time.monotonic()-started,'scope':'Actual frozen Windows synthetic speed command. Not owner3060, physicalvoice or fullcandidate. No command-side downloads/mic/screen/cloud.'},indent=2))
if result.returncode:raise RuntimeError('Frozen owner command failed')
if raw['result']!='measured'or not raw['all_fixture_quality_pass']or raw['stop_state']['state']!='off':raise RuntimeError('Frozen owner command quality/stop failed')
