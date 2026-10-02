"""Five legitimate account slots and per-profile routing. No automatic calls."""
from dataclasses import dataclass,replace
from .providers import configured
from .personas import ROLES
from .router import BrainRouter
KINDS=('groq','gemini','nim','local')
SLOT_IDS=('slot1','slot2','slot3','slot4','slot5')
@dataclass(frozen=True)
class Slot:
    id:str
    provider:str
    model:str
    label:str=''
    def __post_init__(self):
        if self.id not in SLOT_IDS or self.provider not in KINDS:raise ValueError('Unknown slot or provider')
        if not isinstance(self.model,str) or not self.model or len(self.model)>200 or not self.model.isascii() or any(not(c.isalnum() or c in '-_./') for c in self.model):raise ValueError('Model ID required')
        if not isinstance(self.label,str) or len(self.label)>60:raise ValueError('Account label too long')
    @property
    def key_target(self):return self.provider+'/'+self.id
class SlotKeys:
    def __init__(self,store,slots):self.store=store;self.slots={s.id:s for s in slots}
    def get(self,name):return self.store.get(self.slots[name].key_target)
class ProviderPool:
    def __init__(self,slots,routes):
        if len(slots)>5 or len({s.id for s in slots})!=len(slots):raise ValueError('At most five unique slots')
        self.slots={s.id:s for s in slots};self.routes={}
        for name,ids in routes.items():
            if name not in ROLES or not ids or len(ids)!=len(set(ids)) or any(i not in self.slots for i in ids):raise ValueError('Invalid profile route')
            self.routes[name]=tuple(ids)
    def router(self,name,store,consented=(),free_confirmed=(),transport=None):
        if name not in self.routes:raise ValueError('Configure this profile route first')
        slots=[self.slots[i] for i in self.routes[name]]
        for s in slots:
            if s.provider!='local' and (s.id not in consented or s.id not in free_confirmed):raise ValueError('Confirm disclosure and free account status for each cloud slot')
        providers=[replace(configured(s.provider,s.model),name=s.id,requires_free_plan=s.provider!='local') for s in slots]
        return PoolSessionRouter(BrainRouter(providers,transport=transport,key_store=SlotKeys(store,slots)),tuple(s.id for s in slots if s.provider!='local'))
class PoolSessionRouter:
    def __init__(self,router,verified):self.router=router;self.verified=verified
    def ask(self,*args,**kw):return self.router.ask(*args,verified_free_providers=self.verified,**kw)
    def stream(self,*args,**kw):return self.router.stream(*args,verified_free_providers=self.verified,**kw)
