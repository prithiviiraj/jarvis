"""Actual frozen CPU Laya model acceptance; no browser or microphone."""
import json,pathlib,time,importlib.util
from .laya_assets import LayaSetup,cache,TOTAL_BYTES
from .laya_engine import LayaEngine
from .experimental.browser_proposals import Snapshot,Element
from .laya_browser import prepare

def run():
 start=time.monotonic();
 assert importlib.util.find_spec('laya') is not None,'Laya runtime missing from frozen package'
 assert importlib.util.find_spec('torch') is not None,'CPU Torch missing from frozen package'
 setup=LayaSetup();t=setup.start(consent=True);t.join(600)
 if t.is_alive()or not setup.ready:raise RuntimeError('Managed Laya model setup failed: '+setup.status+' '+setup.error)
 installed=time.monotonic();e=LayaEngine();t=e.load(consent=True);t.join(180)
 if t.is_alive()or e.agent is None:raise RuntimeError('Managed Laya engine load failed: '+e.error)
 loaded=time.monotonic();state={'state':'ready','url':'https://example.com/','links':[{'id':'1','label':'Documentation','url':'https://www.iana.org/help/example-domains'}]}
 from .experimental.browser_proposals import ProposalError
 abstained=False
 try:step,detail=prepare(state,'Open the documentation link',client=e)
 except (ProposalError,ValueError):
  step=None;detail='Actual model response was rejected by the proposal boundary; no action accepted';abstained=True
 decided=time.monotonic()
 # Actual model may abstain or choose wait/done; it is never required to act.
 if step is not None:
  assert set(step)<= {'command','value','expected_url'}
  assert step['command']in ('open','scroll-down','scroll-up')
  if step['command']=='open':assert step['value']==state['links'][0]['url']
  assert step['expected_url']==state['url']
 e.stop();assert e.agent is None
 report={'actual_frozen_inbuilt_laya_cpu':True,'model_bytes':TOTAL_BYTES,'model_cache':str(cache()),'install_s':round(installed-start,3),'load_s':round(loaded-installed,3),'decision_s':round(decided-loaded,3),'proposal':step,'boundary_rejected':abstained,'status':detail,'executed':False,'browser_or_microphone_started':False,'stop_discards_engine':True,'scope':'synthetic public fixture; no real website task, mic/audio, Tamil or laptop timing proof'}
 path=pathlib.Path.cwd()/'ui-evidence'/'managed-laya-acceptance.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
