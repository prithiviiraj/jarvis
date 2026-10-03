"""Optional provider presets. No provider is enabled here and models are user-editable."""
import json,urllib.request
from .router import Provider,NoRedirect,RouterError,local_http
ENDPOINTS={
 'local':'http://127.0.0.1:1234/v1',
 'gemini':'https://generativelanguage.googleapis.com/v1beta/openai',
 'nim':'https://integrate.api.nvidia.com/v1',
 'groq':'https://api.groq.com/openai/v1',
 'grok':'https://api.x.ai/v1' # legacy optional endpoint; never the owner's default intent
}
def configured(name,model):
 if name not in ENDPOINTS:raise ValueError('Unknown provider.')
 return Provider(name,ENDPOINTS[name],model,name!='local',requires_free_plan=name=='groq')
def local_models(timeout=2):
 """Prefer loaded LLM instances; downloaded embeddings are not chat choices."""
 http=local_http();base=ENDPOINTS['local'].removesuffix('/v1')
 def read(url):
  with http.open(url,timeout=timeout) as response:
   raw=response.read(262145)
   if len(raw)>262144:raise ValueError('Model list too large')
   return json.loads(raw)
 def valid(value):return isinstance(value,str) and 0<len(value)<200
 try:
  metadata=read(base+'/api/v1/models')
  if isinstance(metadata.get('models'),list):
   llms=[x for x in metadata['models'] if isinstance(x,dict) and x.get('type')=='llm' and valid(x.get('key'))]
   loaded=list(dict.fromkeys(i['id'] for x in llms for i in x.get('loaded_instances',[]) if isinstance(i,dict) and valid(i.get('id'))))
   if loaded:return loaded
   return list(dict.fromkeys(x['key'] for x in llms))
 except Exception:pass # Older LM Studio exposes only the OpenAI-compatible list.
 try:
  data=read(ENDPOINTS['local']+'/models')['data']
  ids=list(dict.fromkeys(x['id'] for x in data if isinstance(x,dict) and valid(x.get('id')) and x.get('type') not in ('embedding','embeddings') and not x['id'].lower().startswith(('text-embedding-','nomic-embed-','embedding-'))))
  if not ids:raise ValueError('No chat model')
  return ids[:20]
 except Exception:raise RouterError('LM Studio is not answering with a chat model. Open LM Studio, load a model, then start its local server.') from None
