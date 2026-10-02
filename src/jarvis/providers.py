"""Optional provider presets. No provider is enabled here and models are user-editable."""
import json,urllib.request
from .router import Provider,NoRedirect,RouterError
ENDPOINTS={
 'local':'http://127.0.0.1:1234/v1',
 'gemini':'https://generativelanguage.googleapis.com/v1beta/openai',
 'nim':'https://integrate.api.nvidia.com/v1',
 'grok':'https://api.x.ai/v1'
}
def configured(name,model):
 if name not in ENDPOINTS:raise ValueError('Unknown provider.')
 return Provider(name,ENDPOINTS[name],model,name!='local')
def local_models(timeout=2):
 http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 try:
  with http.open(ENDPOINTS['local']+'/models',timeout=timeout) as response:
   raw=response.read(65537)
   if len(raw)>65536:raise ValueError()
   data=json.loads(raw)['data']
   ids=[x['id'] for x in data if isinstance(x.get('id'),str) and 0<len(x['id'])<200]
   if not ids:raise ValueError()
   return ids[:20]
 except Exception:raise RouterError('LM Studio is not answering. Open LM Studio, load a model, then start its local server.') from None
