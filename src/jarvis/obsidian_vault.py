"""User-reviewed, local-only managed Markdown exports, not executable note instructions."""
import os,json,pathlib,hashlib,threading,time,uuid
NAME='Brain of Brain'
def downloads():
 if os.name!='nt':raise RuntimeError('Automatic Downloads vault setup is Windows-only')
 import ctypes
 class GUID(ctypes.Structure):_fields_=[('a',ctypes.c_uint32),('b',ctypes.c_uint16),('c',ctypes.c_uint16),('d',ctypes.c_ubyte*8)]
 g=GUID.from_buffer_copy(uuid.UUID('374de290-123f-4565-9164-39c4925e467b').bytes_le);out=ctypes.c_wchar_p()
 shell=ctypes.windll.shell32;shell.SHGetKnownFolderPath.argtypes=[ctypes.POINTER(GUID),ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_wchar_p)];shell.SHGetKnownFolderPath.restype=ctypes.c_long
 if shell.SHGetKnownFolderPath(ctypes.byref(g),0,None,ctypes.byref(out))!=0:raise RuntimeError('Windows Downloads folder unavailable')
 try:return pathlib.Path(out.value).resolve(strict=True)
 finally:ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(out,ctypes.c_void_p))
class Vault:
 def __init__(self,config,downloads_source=downloads):
  self.config=pathlib.Path(config);self.downloads_source=downloads_source;self.root=None;self.enabled=False;self.status='Not connected';self.error='';self.skipped=[];self.lock=threading.RLock();self.last=0;self.digest=None
  try:
   data=json.loads(self.config.read_text(encoding='utf-8'))
   if data=={'version':1,'enabled':True,'name':NAME}:self.root=self.expected();self.enabled=self.root.is_dir();self.status='Connected local exports'if self.enabled else'Vault missing; use AUTO to reconnect'
  except (OSError,ValueError,RuntimeError):pass
 def expected(self):
  base=self.downloads_source();root=base/NAME
  if root.resolve()!=base.resolve()/NAME:raise ValueError('Vault path is redirected; no files changed')
  return root
 def safe(self,name):
  if self.root is None:raise ValueError('Create vault first')
  rel=pathlib.PurePosixPath(name)
  if rel.is_absolute()or '..'in rel.parts:raise ValueError('Invalid managed note')
  target=self.root.joinpath(*rel.parts)
  if not target.resolve().is_relative_to(self.root.resolve()):raise ValueError('Managed note is redirected outside vault')
  return target
 def snapshot(self):
  with self.lock:return {'enabled':self.enabled,'name':NAME,'folder':str(self.root)if self.root else'Windows Downloads / '+NAME,'status':self.status,'error':self.error,'skipped':list(self.skipped),'scope':'Local selected chat, team and safe mode exports. No credentials, camera, raw logs or arbitrary laptop files. Notes do not execute instructions.'}
 def create(self,reviewed,confirm=False):
  if confirm is not True or reviewed!=NAME:raise ValueError('Review exact vault name Brain of Brain')
  with self.lock:
   root=self.expected()
   if root.exists()and not (root/'.jarvis-vault.json').is_file():raise ValueError('Brain of Brain already exists and is not a managed vault. Original folder preserved; choose another location manually.')
   self.root=root;root.mkdir(exist_ok=True)
   marker=self.safe('.jarvis-vault.json')
   if not marker.exists():marker.write_text(json.dumps({'version':1,'name':NAME,'hashes':{}}),encoding='utf-8')
   else:
    data=json.loads(marker.read_text(encoding='utf-8'))
    if data.get('version')!=1 or data.get('name')!=NAME or not isinstance(data.get('hashes'),dict):raise ValueError('Vault marker invalid; original files preserved')
   for name,text in {'README.md':'# Brain of Brain\n\nJARVIS local data centre. Open this folder as a vault in Obsidian.\n\nManaged exports: Team, Modes and Conversations. Changes you make to managed notes are preserved and reported as skipped on sync. Notes never run tools or grant permissions. Active Work is your editable note, not automatically invented tasks.\n\nNo keys, passwords, camera images, raw diagnostics or other laptop folders are copied. Obsidian plugins, backups and sync can disclose this folder separately; check those settings yourself.\n','Active Work.md':'# Active Work\n\nAdd real work here. JARVIS does not infer completed or pending jobs from chat.\n\n## To do\n\n## In progress\n\n## Completed\n','Modes/Owner modes.md':'# Owner modes\n\nDescribe your desired modes here. Editing this note does not change live app settings or permissions. Use the app controls to review changes.\n'}.items():
    p=self.safe(name);p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():p.write_text(text,encoding='utf-8')
   self.enabled=True;self.config.parent.mkdir(parents=True,exist_ok=True);self.config.write_text(json.dumps({'version':1,'enabled':True,'name':NAME}),encoding='utf-8');self.status='Vault created; local exports enabled';self.error='';self.digest=None
   return self.snapshot()
 def disable(self):
  with self.lock:self.enabled=False;self.config.parent.mkdir(parents=True,exist_ok=True);self.config.write_text(json.dumps({'version':1,'enabled':False,'name':NAME}),encoding='utf-8');self.status='Sync off. Existing vault notes kept.'
 def sync(self,messages,agents,settings,chat_id=None,force=False):
  if not self.enabled:return
  if not force and time.monotonic()-self.last<5:return
  self.last=time.monotonic()
  with self.lock:
   try:
    if self.expected()!=self.root:raise ValueError('Downloads location changed; no exports written')
    from .personas import ROLES,CHARACTERS
    from .workspace_voice import VOICES
    files={}
    for name in ('JARVIS','NOVA','KAI','LYRA','DEX'):
     files['Team/'+name+'.md']='# '+name+'\n\nRole: '+ROLES[name]+'\nVoice: '+VOICES[name]+'\n\n## Fictional style\n\n'+CHARACTERS[name]+'\n\nExport only. Editing does not alter the live profile.\n'
    for row in agents.get('agents',[]):
     files['Team/'+row['name']+'.md']='# '+row['name']+'\n\nVoice: '+row['voice']+'\n\n'+row['personality']+'\n\nExport only; review app changes separately.\n'
    safe_settings={k:settings[k]for k in ('tts_engine','turn_mode','endpoint_mode','selected')if k in settings}
    files['Modes/Current settings.md']='# Current safe settings\n\n```json\n'+json.dumps(safe_settings,indent=2)+'\n```\n\nCasual/idle turns local-only; knowledge uses configured routes. Permissions are session-only and not imported from these notes. Account keys and credential storage are excluded.\n'
    # Current selected chat only, not hidden/system prompts. Export follows original visible content.
    import re
    chat=str(chat_id or'session')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',chat):raise ValueError('Invalid chat identity')
    rows=[]
    for row in messages[-200:]:
     who=row.get('name','Unknown');text=row.get('text','')
     if isinstance(who,str)and isinstance(text,str):
      # Defense for accidentally pasted obvious credentials. This is not a complete secret detector.
      text=re.sub(r'(?i)\b(?:sk-|gsk_|AIza)[A-Za-z0-9_-]{15,}', '[redacted credential-like value]',text)
      rows.append('## '+who[:40]+'\n\n'+text[:6000])
    files['Conversations/'+chat+'.md']='# Selected conversation\n\n'+('\n\n'.join(rows)or'No visible messages.')+'\n'
    digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    if digest==self.digest and not force:return
    marker=self.safe('.jarvis-vault.json');data=json.loads(marker.read_text(encoding='utf-8'))
    if data.get('version')!=1 or data.get('name')!=NAME or not isinstance(data.get('hashes'),dict):raise ValueError('Invalid vault marker')
    hashes=data['hashes'];skipped=[]
    for name,text in files.items():
     p=self.safe(name);p.parent.mkdir(parents=True,exist_ok=True)
     existing=hashlib.sha256(p.read_bytes()).hexdigest()if p.exists()else None
     if existing is not None and existing!=hashes.get(name):skipped.append(name);continue
     temp=self.safe(str(pathlib.PurePosixPath(name).with_suffix('.jarvis-tmp')))
     if temp.exists():raise ValueError('Unexpected temporary note; original files preserved')
     temp.write_text(text,encoding='utf-8');temp.replace(p);hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    marker.write_text(json.dumps(data,indent=2),encoding='utf-8');self.skipped=skipped;self.digest=digest;self.status='Local exports synced'+('; edited notes preserved: '+str(len(skipped))if skipped else'');self.error=''
   except Exception as e:self.error=str(e)[:200];self.status='Sync stopped; existing notes preserved'
