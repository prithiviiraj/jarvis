"""Owner-run Groq diagnostic v2. Never prints keys, response text or error messages."""
import argparse,json,pathlib,ssl,socket,time,urllib.request,urllib.error,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'src'))
UA='JARVIS-experimental/diagnostic-v2 (+https://github.com/prithiviiraj/jarvis)'
KNOWN={'model_permission_blocked_org':'MODEL_PERMISSION_BLOCKED_ORG','model_permission_blocked_project':'MODEL_PERMISSION_BLOCKED_PROJECT','invalid_api_key':'INVALID_API_KEY','model_not_found':'MODEL_NOT_FOUND'}

def classify(exc):
 if isinstance(exc,urllib.error.HTTPError):
  result={'code':{401:'HTTP_401_KEY_REJECTED',403:'HTTP_403_ACCESS_DENIED',400:'HTTP_400_REQUEST_OR_MODEL_REJECTED',404:'HTTP_404_MODEL_OR_ENDPOINT_NOT_FOUND',429:'HTTP_429_RATE_LIMIT'}.get(exc.code,'HTTP_'+str(exc.code))}
  try:
   raw=exc.read(8193)
   if len(raw)>8192:result['detail']='ERROR_BODY_TOO_LARGE'
   else:
    try:data=json.loads(raw)
    except (ValueError,UnicodeDecodeError):
     result['detail']='NON_JSON_EDGE_OR_PROXY_REJECTION' if exc.code==403 else 'NON_JSON_ERROR';return result
    error=data.get('error') if isinstance(data,dict) else None
    if isinstance(error,dict):
     code=error.get('code');kind=error.get('type')
     result['detail']=KNOWN.get(code,'PERMISSIONS_ERROR_UNSPECIFIED' if kind=='permissions_error' else 'STRUCTURED_ERROR_UNCLASSIFIED') if isinstance(code,(str,type(None))) else 'STRUCTURED_ERROR_UNCLASSIFIED'
    else:result['detail']='JSON_ERROR_UNCLASSIFIED'
  except Exception:result['detail']='ERROR_BODY_UNAVAILABLE'
  return result
 reason=exc.reason if isinstance(exc,urllib.error.URLError) else exc
 if isinstance(reason,ssl.SSLCertVerificationError):return {'code':'TLS_CERTIFICATE_VERIFY_FAILED'}
 if isinstance(reason,ssl.SSLError):return {'code':'TLS_HANDSHAKE_FAILED'}
 if isinstance(reason,socket.gaierror):return {'code':'DNS_FAILED'}
 if isinstance(reason,(TimeoutError,socket.timeout)):return {'code':'NETWORK_TIMEOUT'}
 if isinstance(reason,(ConnectionError,OSError)):return {'code':'NETWORK_CONNECTION_FAILED'}
 return {'code':'CHECK_FAILED'}

def probe(key,model,context,opener_factory=urllib.request.build_opener):
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):return None
 http=opener_factory(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=context))
 headers={'Content-Type':'application/json','Authorization':'Bearer '+key,'User-Agent':UA,'Accept':'application/json'}
 rows=[]
 def request(path,payload=None):
  req=urllib.request.Request('https://api.groq.com/openai/v1/'+path,headers=headers,data=json.dumps(payload).encode() if payload else None)
  started=time.monotonic()
  with http.open(req,timeout=20) as response:
   raw=response.read(65537)
   if len(raw)>65536:raise ValueError()
   return json.loads(raw),round(time.monotonic()-started,3)
 try:
  data,seconds=request('models');items=data['data']
  if not isinstance(items,list):raise ValueError()
  ids={x['id'] for x in items if isinstance(x,dict) and isinstance(x.get('id'),str) and x.get('active') is True}
  rows.append({'step':'models','code':'OK_MODELS_KEY_ACCEPTED_FOR_LIST','requested_model_active':model in ids,'seconds':seconds})
 except Exception as exc:
  rows.append(dict(step='models',**classify(exc)));return rows
 if model not in ids:
  rows.append({'step':'greeting','code':'SKIPPED_REQUESTED_MODEL_NOT_ACTIVE'});return rows
 try:
  data,seconds=request('chat/completions',{'model':model,'messages':[{'role':'user','content':'Say hello in one short sentence.'}],'stream':False,'max_tokens':32})
  text=data['choices'][0]['message']['content']
  rows.append({'step':'greeting','code':'OK_GROQ_REPLY_RECEIVED' if isinstance(text,str) and text.strip() else 'EMPTY_REPLY','seconds':seconds})
 except Exception as exc:rows.append(dict(step='greeting',**classify(exc)))
 return rows

def main():
 parser=argparse.ArgumentParser(description='v2: saved local key, models-list check, then at most one greeting. Outputs fixed categories only.')
 parser.add_argument('--model',default='llama-3.3-70b-versatile');parser.add_argument('--free-plan',action='store_true');parser.add_argument('--consent',action='store_true');args=parser.parse_args()
 if not args.free_plan or not args.consent:raise SystemExit('Confirm Free plan and approve models lookup plus one greeting first. No request sent.')
 if not args.model.strip() or len(args.model)>200:raise SystemExit('Invalid model ID. No request sent.')
 from jarvis.security import WindowsCredentials
 from jarvis.paths import ensure_layout
 try:key=WindowsCredentials().get('groq')
 except Exception:key=None;rows=[{'code':'WINDOWS_CREDENTIAL_STORE_UNAVAILABLE'}]
 else:
  if not key:rows=[{'code':'NO_SAVED_GROQ_KEY'}]
  else:
   rows=[dict(trust='windows-default',**r) for r in probe(key,args.model.strip(),ssl.create_default_context())]
   # Retry trust roots only when the models lookup failed TLS before any greeting.
   if len(rows)==1 and rows[0]['code'].startswith('TLS_'):
    try:
     import certifi
     rows += [dict(trust='certifi',**r) for r in probe(key,args.model.strip(),ssl.create_default_context(cafile=certifi.where()))]
    except Exception:rows.append({'trust':'certifi','code':'CERTIFI_TRUST_UNAVAILABLE'})
 key=None
 result={'diagnostic_version':2,'checks':rows,'tls_verification':'ON','client':'JARVIS-experimental','billing_verified_by_api':False}
 path=ensure_layout()/'logs'/'groq-diagnostic.json';path.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,indent=2));print('Diagnostic saved to %LOCALAPPDATA%\\JARVIS\\logs\\groq-diagnostic.json')
if __name__=='__main__':main()
