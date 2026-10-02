"""Opt-in active-model lookup. Production allowlist only; never infer billing."""
import json,ssl,socket,urllib.request,urllib.error
from .providers import ENDPOINTS
from .router import NoRedirect
from .security import WindowsCredentials
# Current documented production chat models. Smaller model first for voice speed.
# Never pick arbitrary/preview/tool/audio IDs returned by the account endpoint.
PREFERRED=('openai/gpt-oss-120b','openai/gpt-oss-20b','llama-3.1-8b-instant','llama-3.3-70b-versatile')
APP_UA='JARVIS-experimental/0.1 (+https://github.com/prithiviiraj/jarvis)'

def listed_ids(data):
    if not isinstance(data,list):raise ValueError('Invalid model response.')
    return {x['id'] for x in data if isinstance(x,dict) and isinstance(x.get('id'),str) and 0<len(x['id'])<=200 and x['id'].isascii() and all(c.isalnum() or c in '-_./' for c in x['id']) and ('active' not in x or x['active'] is True)}
class GroqCheckError(RuntimeError):pass

def error_code(exc):
    if isinstance(exc,urllib.error.HTTPError):
        return {401:'HTTP_401_KEY_REJECTED',403:'HTTP_403_ACCESS_DENIED',400:'HTTP_400_REQUEST_OR_MODEL_REJECTED',404:'HTTP_404_MODEL_OR_ENDPOINT_NOT_FOUND',429:'HTTP_429_RATE_LIMIT'}.get(exc.code,'HTTP_'+str(exc.code))
    reason=exc.reason if isinstance(exc,urllib.error.URLError) else exc
    if isinstance(reason,ssl.SSLCertVerificationError):return 'TLS_CERTIFICATE_VERIFY_FAILED'
    if isinstance(reason,ssl.SSLError):return 'TLS_HANDSHAKE_FAILED'
    if isinstance(reason,socket.gaierror):return 'DNS_FAILED'
    if isinstance(reason,(TimeoutError,socket.timeout)):return 'NETWORK_TIMEOUT'
    return 'NETWORK_OR_RESPONSE_FAILED'

def resolve_model(override='',cloud_consent=False,verified_free=False,key_store=None,opener_factory=urllib.request.build_opener,details=False):
    if not cloud_consent:raise GroqCheckError('Allow Groq for this session first. No request sent.')
    if not verified_free:raise GroqCheckError('Confirm your account is on the Free plan first. No request sent.')
    if not isinstance(override,str) or len(override)>200:raise GroqCheckError('Invalid model override. No request sent.')
    override=override.strip()
    if override and (not override.isascii() or any(not(c.isalnum() or c in '-_./') for c in override)):
        raise GroqCheckError('Invalid model override. No request sent.')
    keys=key_store if key_store is not None else WindowsCredentials()
    try:key=keys.get('groq')
    except Exception:raise GroqCheckError('WINDOWS_CREDENTIAL_STORE_UNAVAILABLE') from None
    if not key:raise GroqCheckError('NO_SAVED_GROQ_KEY: Save a key in Settings first.')
    def load(context):
        http=opener_factory(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=context))
        req=urllib.request.Request(ENDPOINTS['groq']+'/models',headers={'Authorization':'Bearer '+key,'User-Agent':APP_UA,'Accept':'application/json'})
        with http.open(req,timeout=12) as r:
            raw=r.read(65537)
            if len(raw)>65536:raise ValueError()
            data=json.loads(raw)['data']
            if not isinstance(data,list):raise ValueError()
            return listed_ids(data)
    try:
        try:ids=load(ssl.create_default_context())
        except Exception as exc:
            if not error_code(exc).startswith('TLS_'):raise
            import certifi
            ids=load(ssl.create_default_context(cafile=certifi.where()))
    except Exception as exc:raise GroqCheckError('Groq model lookup failed ('+error_code(exc)+'). Run GROQ-DIAG.cmd for codes.') from None
    finally:key=None
    if override:
        if override not in ids:raise GroqCheckError('MODEL_OVERRIDE_NOT_ACTIVE: unlock and choose another ID, or return to Automatic.')
        return (override,ids) if details else override
    for model in PREFERRED:
        if model in ids:return (model,ids) if details else model
    raise GroqCheckError('NO_APPROVED_ACTIVE_CHAT_MODEL: automatic selection stopped. No fallback or greeting sent.')
