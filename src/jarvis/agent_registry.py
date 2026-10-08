"""Bounded owner-created fictional profiles. No effect/credential authority in personality."""
import json,re,threading
from pathlib import Path
BUILTINS=('JARVIS','LYRA','DEX')
RESERVED=BUILTINS+('NOVA','SILA','REO')
VOICE_IDS=('am_puck','am_michael','af_heart','am_liam','af_sky','am_fenrir')
class AgentRegistry:
 def __init__(self,path):
  self.path=Path(path);self.lock=threading.RLock();self.rows=[];self.error=''
  if self.path.exists():
   try:
    raw=json.loads(self.path.read_text(encoding='utf-8'))
    if not isinstance(raw,dict)or raw.get('version')!=1 or not isinstance(raw.get('agents'),list)or len(raw['agents'])>8:raise ValueError('Invalid agent file')
    for row in raw['agents']:self.rows.append(self.validate(row,{r['name']for r in self.rows}))
   except Exception:self.rows=[];self.error='Custom agent file could not be loaded. Original file preserved; changes are blocked.'
 def validate(self,row,existing=()):
  if not isinstance(row,dict)or set(row)!={'name','personality','voice'}:raise ValueError('Name, personality and installed voice required')
  name=row['name'];text=row['personality'];voice=row['voice']
  if not isinstance(name,str)or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{1,23}',name):raise ValueError('Use2-24letters, digits, underscore or dash for agent name')
  name=name.upper()
  if name in RESERVED or name in existing:raise ValueError('That agent name already exists')
  if not isinstance(text,str)or not text.strip()or len(text)>1500 or any(ord(c)<32 and c!='\n'for c in text):raise ValueError('Use a personality description up to1500characters')
  if voice not in VOICE_IDS:raise ValueError('Choose an installed voice profile')
  return {'name':name,'personality':text.strip(),'voice':voice}
 def create(self,row,reviewed=None,confirm=False):
  raise ValueError('Active team is JARVIS, LYRA and DEX. Saved custom profiles are archived.')
 def snapshot(self):
  with self.lock:return {'agents':[],'archived_agents':[dict(r)for r in self.rows],'error':self.error,'limit':0,'voice_ids':list(VOICE_IDS)}
 def apply(self):
  from .personas import ROLES,CHARACTERS
  from .workspace_voice import VOICES
  from .moderator import ROLES as MODERATOR_ROLES
  # Rebuild only custom names; built-in choices/history stay compatible.
  for name in tuple(ROLES):
   if name not in BUILTINS:ROLES.pop(name,None);CHARACTERS.pop(name,None);VOICES.pop(name,None);MODERATOR_ROLES.pop(name,None)
