"""Actual optional checkpoint acceptance. Synthetic fixture only, no browser effects."""
import json,time,resource,pathlib,sys
from laya import Router
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.experimental.browser_proposals import Snapshot,Element,request,propose
from jarvis.experimental.laya_local import normalize
revision='7b928d828b7b0e022f929d9bd2e44165aa270148'
digest='891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c'
router=Router(device='cpu',max_loaded=1,default='english',revision=revision,sha256_digests={'english':{'model.safetensors':digest}})
fixtures=[('Read the next page about example domains',Snapshot('s','https://example.com',1,(Element('1','Learn more about example domains','link',True),))),('Wait for the page to finish loading',Snapshot('s','https://example.com',1,()))]
results=[]
try:
 for goal,snapshot in fixtures:
  payload=request(snapshot,goal,{'example.com'},2);t=time.perf_counter();raw=router.predict(payload['state'],payload['questions'],model='english',max_len=512,min_confidence=.7);elapsed=time.perf_counter()-t
  try:
   result=propose(snapshot,goal,{'example.com'},2,normalize(raw),'s');outcome={'operation':result.operation,'executed':result.executed,'needs_review':result.needs_review}
  except ValueError:outcome={'abstained':True,'executed':False}
  results.append({'goal':goal,'elapsed_s':elapsed,'answers':raw['answers'],'proposal':outcome})
  assert outcome['executed']is False
finally:router.unload()
pathlib.Path('optional-engine-evidence').mkdir(exist_ok=True)
report={'scope':'actual pinned English Laya CPU checkpoint over synthetic fixtures, no browser effects or owner data','revision':revision,'model_sha256':digest,'maxrss_platform_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'results':results,'physical_mic':False,'browser_autonomy':False}
pathlib.Path('optional-engine-evidence/laya-CPU.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
