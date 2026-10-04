"""Optional local Laya proposal client. No model download, click or authority grant."""
import urllib.request,json
from .browser_proposals import request,propose
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Laya redirects refused')
class LayaLocal:
 def __init__(self,port=8000):
  if type(port)is not int or not 1024<=port<=65535:raise ValueError('Invalid local model port')
  self.url='http://127.0.0.1:'+str(port)+'/v1/systemone'
  self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 def prepare(self,snapshot,goal,hosts,now,current_snapshot_id):
  payload=request(snapshot,goal,hosts,now)
  # Only bounded offered labels + host go to user's explicit local endpoint.
  r=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  with self.http.open(r,timeout=5)as response:raw=response.read(65537)
  if len(raw)>65536:raise ValueError('Oversize local decision')
  return propose(snapshot,goal,hosts,now,normalize(json.loads(raw)),current_snapshot_id)

def normalize(result):
 # Real maintained server metadata is never a command or an authority grant.
 if not isinstance(result,dict)or set(result)-{'model','answers','usage','routing'}or not isinstance(result.get('answers'),dict):raise ValueError('Unexpected Laya response envelope')
 answers={}
 allowed={'type','choice','probabilities','confidence','action','answer_confidence','low_confidence','abstention','abstention_threshold'}
 for key,value in result['answers'].items():
  if not isinstance(value,dict)or set(value)-allowed or value.get('type','choice')!='choice':raise ValueError('Expected bounded choice answer')
  if value.get('low_confidence')is True or value.get('abstention')in ('abstained','unevaluated'):raise ValueError('Laya abstained')
  if 'answer_confidence'in value:
   c=value['answer_confidence']
   if isinstance(c,bool)or not isinstance(c,(int,float))or not .7<=c<=1:raise ValueError('Low calibrated confidence')
  answers[key]={k:value[k]for k in ('choice','probabilities','confidence')if k in value}
 return {'answers':answers}
