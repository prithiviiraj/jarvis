"""Actual frozen runtime with synthetic public labels; no browser or owner data."""
import subprocess,pathlib,json,time,urllib.request,os
root=pathlib.Path(__file__).resolve().parent;exe=root/'portable/JARVIS-Laya.exe';env=dict(os.environ);env.pop('PYTHONPATH',None);env['PATH']=str(pathlib.Path(os.environ['WINDIR'])/'System32');env['LOCALAPPDATA']=str(root/'isolated-data')
t=time.monotonic();subprocess.run([str(exe),'--install-reviewed'],env=env,check=True);install=time.monotonic()-t
log=(root/'server.log').open('w');p=subprocess.Popen([str(exe),'--serve'],env=env,stdout=log,stderr=log);t=time.monotonic()
try:
 deadline=time.monotonic()+120
 while True:
  if p.poll()is not None:raise RuntimeError('Frozen runtime exited; inspect server.log')
  try:
   with urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2)as r:health=json.load(r)
   break
  except OSError:
   if time.monotonic()>deadline:raise
   time.sleep(.2)
 load=time.monotonic()-t
 import sys
 sys.path.insert(0,str(root.parent/'src'))
 from jarvis.laya_browser import prepare
 state={'state':'ready','url':'https://example.com/','links':[{'id':'1','label':'Learn more about example domains','url':'https://www.iana.org/help/example-domains'}]}
 t=time.monotonic();proposal,status=prepare(state,'Open the example domains documentation');elapsed=time.monotonic()-t
 report={'actual_frozen_cpu_runtime':True,'system_python_removed_from_PATH':True,'model_bundled':False,'install_s':install,'load_s':load,'decision_s':elapsed,'health':health,'proposal':proposal,'status':status,'executed':False,'matches_requested_link':bool(proposal and proposal.get('value')==state['links'][0]['url'])}
 (root/'acceptance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:p.terminate();p.wait(20);log.close()
