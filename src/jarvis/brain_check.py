"""Opt-in session connection check. Fixed public greeting, no private conversation."""
import time
from .providers import configured
from .router import BrainRouter
from .security import WindowsCredentials

def check_groq(model,cloud_consent=False,verified_free=False,key_store=None,router_factory=BrainRouter):
    if not cloud_consent:raise ValueError('Allow sending the test greeting to Groq for this session.')
    if not verified_free:raise ValueError('Confirm your Groq account is on the Free plan first.')
    if not isinstance(model,str) or not model.strip() or len(model)>200:raise ValueError('Enter a current Groq model ID.')
    keys=key_store if key_store is not None else WindowsCredentials()
    if not keys.get('groq'):raise ValueError('Save the key securely in Settings first.')
    router=router_factory([configured('groq',model.strip())],key_store=keys)
    started=time.monotonic();pieces=[];first=None
    for delta in router.stream([{'role':'system','content':'Reply briefly. No actions or tool calls.'},{'role':'user','content':'Say hello in one short sentence.'}],cloud_consent=True,verified_free_providers=('groq',)):
        if first is None:first=time.monotonic()-started
        pieces.append(delta['text'])
    if not pieces:raise RuntimeError('Groq returned no text.')
    return {'provider':'groq','model':model.strip(),'reply':''.join(pieces)[:400],'first_text_s':first,'total_s':time.monotonic()-started,'scope':'text connection check, not voice or audible latency'}
