"""Five fast evidence questions. This is NOT an authority, action or probability gate."""
import re,time
from .action_intent import parse,goal
from .desktop_actions import prepare
from .vault_voice import parse_voice
from .intent_routing import casual
from .multi_address import addressed

def assess(text,source='typed',endpoint=None,retrieval=None):
 start=time.perf_counter()
 if not isinstance(text,str)or not text.strip():return {'state':'unknown','lane':'unknown','confidence':None,'scope':'No usable request; no action authorized'}
 text=text.strip();action=None
 try:action=parse_voice(text)
 except ValueError:pass
 browser=parse(text)or goal(text);app=prepare(text)
 external=bool(re.search(r'\b(send|email|mail|invoice|book|pay|buy|purchase|delete|publish|post|upload|transfer|invite|subscribe|call)\b',text,re.I))
 lane='local retrieval'if action else'app'if app else'browser'if browser else'external workflow'if external else'local casual'if casual(text)else'conversation'
 # Recognize exactly named addressees only. A mentioned third party is not one.
 names=list(addressed(text))
 if not names:
  from .personas import ROLES
  m=re.match(r'^\s*(?:(?:hey|hi|hello)\s+)?('+ '|'.join(re.escape(x)for x in ROLES)+r')\b',text,re.I)
  if m:names=[m.group(1).upper()]
 if source=='typed':completion='typed submission, not a speech decision'
 elif isinstance(endpoint,dict)and endpoint.get('complete')is True:completion='observed endpoint complete'
 elif isinstance(endpoint,dict)and endpoint.get('complete')is False:completion='observed endpoint incomplete'
 else:completion='unknown; endpoint evidence missing'
 stakes='local read only'if action else'bounded navigation/app launch'if browser or app else'external effect or ambiguity; exact scope/review required'if external else'no effect inferred'
 # Retrieval must be the exact query and carry actual scan metadata. Empty is
 # evidence only within that scope, never proof of absence or permission.
 coverage='unknown until exact-query retrieval';count=None
 if isinstance(retrieval,dict)and retrieval.get('query')==text and isinstance(retrieval.get('results'),list):
  data=retrieval.get('coverage')
  if isinstance(data,dict)and type(data.get('complete'))is bool and type(data.get('scanned'))is int:
   count=len(retrieval['results']);coverage=('complete within selected local text scope'if data['complete']else'partial local text scope')+'; '+str(count)+' candidates, not answer confidence'
 return {'state':'measured rule evidence','lane':lane,'source':source,'addressed':names,'speech_complete':completion,'action_stakes':stakes,'vault_coverage':coverage,'candidate_count':count,'confidence':None,'elapsed_ms':round((time.perf_counter()-start)*1000,3),'scope':'Deterministic evidence only. Never grants consent, chooses accounts, executes effects, or replaces model reasoning.'}
