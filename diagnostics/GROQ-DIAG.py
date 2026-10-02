"""Owner-run Groq diagnostic. Run from extracted JARVIS folder. Never prints keys."""
import argparse,json,pathlib,ssl,socket,time,urllib.request,urllib.error,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'src'))

def classify(exc):
 if isinstance(exc,urllib.error.HTTPError):
  code=exc.code
  return {401:'HTTP_401_KEY_REJECTED',403:'HTTP_403_ACCESS_DENIED',400:'HTTP_400_REQUEST_OR_MODEL_REJECTED',404:'HTTP_404_MODEL_OR_ENDPOINT_NOT_FOUND',429:'HTTP_429_RATE_LIMIT',500:'HTTP_500_PROVIDER_ERROR',502:'HTTP_502_PROVIDER_ERROR',503:'HTTP_503_PROVIDER_ERROR'}.get(code,'HTTP_'+str(code))
 reason=exc.reason if isinstance(exc,urllib.error.URLError) else exc
 if isinstance(reason,ssl.SSLCertVerificationError):return 'TLS_CERTIFICATE_VERIFY_FAILED'
 if isinstance(reason,ssl.SSLError):return 'TLS_HANDSHAKE_FAILED'
 if isinstance(reason,socket.gaierror):return 'DNS_FAILED'
 if isinstance(reason,(TimeoutError,socket.timeout)):return 'NETWORK_TIMEOUT'
 if isinstance(reason,(ConnectionError,OSError)):return 'NETWORK_CONNECTION_FAILED'
 return 'CHECK_FAILED'

def probe(key,model,context,opener_factory=urllib.request.build_opener):
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):return None
 http=opener_factory(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=context))
 req=urllib.request.Request('https://api.groq.com/openai/v1/chat/completions',headers={'Content-Type':'application/json','Authorization':'Bearer '+key},data=json.dumps({'model':model,'messages':[{'role':'user','content':'Say hello in one short sentence.'}],'stream':False,'max_tokens':32}).encode())
 try:
  started=time.monotonic()
  with http.open(req,timeout=20) as response:
   data=json.loads(response.read(65537))
   text=data['choices'][0]['message']['content']
   if not isinstance(text,str) or not text.strip():return {'code':'EMPTY_REPLY'}
   return {'code':'OK_GROQ_REPLY_RECEIVED','seconds':round(time.monotonic()-started,3)}
 except Exception as exc:return {'code':classify(exc)}

def main():
 parser=argparse.ArgumentParser(description='Uses your saved local Groq key. Prints error codes only, never key or response body.')
 parser.add_argument('--model',required=True);parser.add_argument('--free-plan',action='store_true');parser.add_argument('--consent',action='store_true');args=parser.parse_args()
 if not args.free_plan or not args.consent:raise SystemExit('Requires --free-plan and --consent after you verify Free plan and approve sending a fixed greeting to Groq. No request sent.')
 if not args.model.strip() or len(args.model)>200:raise SystemExit('Invalid model ID. No request sent.')
 from jarvis.security import WindowsCredentials
 from jarvis.paths import ensure_layout
 try:key=WindowsCredentials().get('groq')
 except Exception:key=None;rows=[{'trust':'not-used','code':'WINDOWS_CREDENTIAL_STORE_UNAVAILABLE'}]
 else:
  if not key:rows=[{'trust':'not-used','code':'NO_SAVED_GROQ_KEY'}]
  else:
   rows=[dict(trust='windows-default',**probe(key,args.model,ssl.create_default_context()))]
   if rows[0]['code'].startswith('TLS_'):
    try:
     import certifi
     rows.append(dict(trust='certifi',**probe(key,args.model,ssl.create_default_context(cafile=certifi.where()))))
    except Exception:rows.append({'trust':'certifi','code':'CERTIFI_TRUST_UNAVAILABLE'})
 key=None
 # No key, username, request body, response body or provider error body in file.
 path=ensure_layout()/'logs'/'groq-diagnostic.json';path.write_text(json.dumps({'checks':rows,'tls_verification':'ON'},indent=2),encoding='utf-8')
 print(json.dumps({'checks':rows,'tls_verification':'ON'},indent=2));print('Diagnostic saved to %LOCALAPPDATA%\\JARVIS\\logs\\groq-diagnostic.json')
if __name__=='__main__':main()
