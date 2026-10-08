"""Local opt-in Markdown vault. Nothing leaves the machine through this connector."""
from pathlib import Path
from urllib.parse import urlencode
import os,time
class Vault:
 def __init__(self,root):
  if not isinstance(root,(str,Path)):raise ValueError('Choose a full Obsidian vault folder path')
  raw=str(root).strip()
  if len(raw)>=2 and raw[0]==raw[-1]and raw[0]in ('"',"'"):raw=raw[1:-1].strip()
  if not raw:raise ValueError('Choose a full Obsidian vault folder path')
  self.root=Path(raw).expanduser().resolve(strict=True)
  managed=False
  marker=self.root/'.jarvis-vault.json'
  if marker.is_file()and not marker.is_symlink()and marker.stat().st_size<=1048576:
   try:
    import json
    data=json.loads(marker.read_text(encoding='utf-8'));managed=data.get('version')==1 and data.get('name')=='Brain of Brain'and isinstance(data.get('hashes'),dict)
   except (OSError,ValueError):pass
  if not self.root.is_dir()or not((self.root/'.obsidian').is_dir()or managed):raise ValueError('Choose an Obsidian vault folder containing .obsidian, or the reviewed managed Brain of Brain folder')
 def note(self,name,must_exist=True):
  if not isinstance(name,str)or len(name)>240 or '\\'in name or ':'in name or any(x.startswith('.')for x in name.split('/')):raise ValueError('Invalid note path')
  rel=Path(name)
  if rel.anchor or rel.suffix!='.md':raise ValueError('Choose a Markdown note')
  p=self.root/rel
  for item in [p,*p.parents]:
   if item==self.root:break
   if item.is_symlink():raise ValueError('Linked notes are excluded')
  if p.is_absolute() and not p.is_relative_to(self.root):raise ValueError('Note outside connected vault')
  try:p=p.resolve(strict=must_exist)
  except (OSError,RuntimeError):raise ValueError('Note missing or inaccessible')from None
  if not p.is_relative_to(self.root):raise ValueError('Note outside vault')
  return p
 def read(self,name):
  p=self.note(name)
  if p.stat().st_size>65536:raise ValueError('Note too large; open it in Obsidian')
  return p.read_text(encoding='utf-8')
 def search(self,query):
  return self.search_details(query)['results']
 def search_details(self,query):
  if not isinstance(query,str)or not query.strip()or len(query)>100:raise ValueError('Enter a short search')
  out=[];scanned=0;skipped=0;reason='complete';deadline=time.monotonic()+.75
  def report():
   return {'results':out,'scanned':scanned,'skipped':skipped,'complete':reason=='complete'and skipped==0,'reason':reason if reason!='complete'or skipped==0 else 'unreadable-notes','scope':'visible non-linked Markdown notes only; local search, no model context'}
  def failed(error):
   nonlocal skipped
   skipped+=1
  for base,dirs,files in os.walk(self.root,followlinks=False,onerror=failed):
   dirs[:]=sorted(d for d in dirs if not d.startswith('.') and not (Path(base)/d).is_symlink())
   for f in sorted(files):
    if f.startswith('.')or not f.endswith('.md')or(Path(base)/f).is_symlink():continue
    if scanned>=500:reason='note-limit';return report()
    if time.monotonic()>deadline:reason='time-limit';return report()
    scanned+=1;name=(Path(base)/f).relative_to(self.root).as_posix()
    try:text=self.read(name)
    except (ValueError,OSError,UnicodeError):skipped+=1;continue
    if query.casefold()in (name+'\n'+text).casefold():out.append({'name':name,'preview':text[:160]})
    if len(out)>=30:reason='result-limit';return report()
  return report()
 def create(self,name,text,confirmed=False):
  if confirmed is not True:raise ValueError('Review note name and text first')
  if not isinstance(text,str)or len(text.encode('utf-8'))>65536:raise ValueError('Note text too large')
  p=self.note(name,False)
  if not p.parent.is_dir():raise ValueError('Choose an existing note folder')
  # Exclusive create: never overwrite or append to an existing note.
  with p.open('x',encoding='utf-8')as f:f.write(text)
  return self.uri(name)
 def uri(self,name):
  return 'obsidian://open?'+urlencode({'path':str(self.note(name))})
