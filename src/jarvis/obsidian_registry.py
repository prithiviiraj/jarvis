"""Preserve Obsidian registry. Never edit it while Obsidian is running."""
import json,os,pathlib,uuid,time,subprocess
from urllib.parse import urlencode,quote
def registry_path():
 if os.name!='nt':raise RuntimeError('Obsidian registration is Windows-only')
 base=os.environ.get('APPDATA')
 if not base:raise RuntimeError('Windows AppData is unavailable')
 return pathlib.Path(base)/'obsidian'/'obsidian.json'
def running():
 if os.name!='nt':raise RuntimeError('Obsidian process check is Windows-only')
 result=subprocess.run(['tasklist','/FI','IMAGENAME eq Obsidian.exe','/FO','CSV','/NH'],capture_output=True,text=True,timeout=10)
 if result.returncode:raise RuntimeError('Could not verify Obsidian process state')
 return 'obsidian.exe' in result.stdout.lower()
def read(path):
 path=pathlib.Path(path)
 if path.is_symlink():raise ValueError('Obsidian config is redirected')
 if not path.exists():return {},None
 raw=path.read_bytes()
 if len(raw)>1048576:raise ValueError('Obsidian config exceeds safe size')
 obj=json.loads(raw)
 if not isinstance(obj,dict)or not isinstance(obj.get('vaults',{}),dict):raise ValueError('Obsidian config invalid; preserved')
 return obj,raw
def lookup(obj,root):
 matches=[key for key,row in obj.get('vaults',{}).items()if isinstance(row,dict)and isinstance(row.get('path'),str)and pathlib.Path(row['path']).resolve()==pathlib.Path(root).resolve()]
 if len(matches)>1:raise ValueError('Multiple registered IDs for this folder; preserved')
 return matches[0]if matches else None
def register(root,path=None,is_running=running):
 root=pathlib.Path(root).resolve(strict=True)
 if not(root/'.jarvis-vault.json').is_file():raise ValueError('Only reviewed managed vault can register')
 path=pathlib.Path(path)if path else registry_path();obj,original=read(path);ident=lookup(obj,root)
 if ident:return ident,False
 if is_running():raise RuntimeError('Close Obsidian, then retry setup so it can load the new vault registration. Existing vaults and app session are preserved.')
 path.parent.mkdir(parents=True,exist_ok=True)
 ident=uuid.uuid4().hex[:16];obj.setdefault('vaults',{})[ident]={'path':str(root),'ts':int(time.time()*1000),'open':False}
 # unique backup and optimistic check guard concurrent external writes
 if original is not None:
  backup=path.with_name('obsidian.json.jarvis-backup-'+uuid.uuid4().hex[:8]);backup.write_bytes(original)
 if is_running():raise RuntimeError('Obsidian started during registration; original config preserved')
 if (path.read_bytes()if path.exists()else None)!=original:raise RuntimeError('Obsidian config changed; retry after it is closed')
 temp=path.with_name('obsidian.json.jarvis-'+uuid.uuid4().hex+'.tmp')
 try:
  temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
  if is_running():raise RuntimeError('Obsidian started during registration; original config preserved')
  if (path.read_bytes()if path.exists()else None)!=original:raise RuntimeError('Obsidian config changed; retry after it is closed')
  os.replace(temp,path)
 finally:
  if temp.exists():temp.unlink()
 checked,_=read(path)
 if lookup(checked,root)!=ident:raise RuntimeError('Vault registration could not be verified')
 return ident,True
def uri(root,note,path=None):
 path=pathlib.Path(path)if path else registry_path();obj,_=read(path);ident=lookup(obj,root)
 if not ident:raise RuntimeError('Vault is not registered. Close Obsidian and retry AUTO setup, or use Open folder as vault.')
 return 'obsidian://open?'+urlencode({'vault':ident,'file':note},quote_via=quote)
