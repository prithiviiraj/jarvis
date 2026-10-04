"""Optional local Laya proposal client. No model download, click or authority grant."""
import urllib.request,json
from .browser_proposals import request,propose
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Laya redirects refused')
class LayaLocal:
 def __init__(self,port=8080):
  if type(port)is not int or not 1024<=port<=65535:raise ValueError('Invalid local model port')
  self.url='http://127.0.0.1:'+str(port)+'/v1/systemone'
  self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 def prepare(self,snapshot,goal,hosts,now,current_snapshot_id):
  payload=request(snapshot,goal,hosts,now)
  # Only bounded offered labels + host go to user's explicit local endpoint.
  r=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  with self.http.open(r,timeout=5)as response:raw=response.read(65537)
  if len(raw)>65536:raise ValueError('Oversize local decision')
  return propose(snapshot,goal,hosts,now,json.loads(raw),current_snapshot_id)
