"""Local opt-in Markdown vault. Nothing leaves the machine through this connector."""
from pathlib import Path
from urllib.parse import urlencode
import os,time
class Vault:
 def __init__(self,root):
  self.root=Path(root).resolve(strict=True)
  if not self.root.is_dir()or not (self.root/'.obsidian').is_dir():raise ValueError('Choose an Obsidian vault folder')
 def note(self,name,must_exist=True):
  if not isinstance(name,str)or len(name)>240 or '\\'in name or ':'in name or any(x.startswith('.')for x in name.split('/')):raise ValueError('Invalid note path')
  rel=Path(name)
  if rel.is_absolute()or rel.suffix!='.md':raise ValueError('Choose a Markdown note')
  p=self.root/rel
  for item in [p,*p.parents]:
   if item==self.root:break
   if item.is_symlink():raise ValueError('Linked notes are excluded')
  p=p.resolve(strict=must_exist)
  if not p.is_relative_to(self.root):raise ValueError('Note outside vault')
  return p
 def read(self,name):
  p=self.note(name)
  if p.stat().st_size>65536:raise ValueError('Note too large; open it in Obsidian')
  return p.read_text(encoding='utf-8')
 def search(self,query):
  if not isinstance(query,str)or not query.strip()or len(query)>100:raise ValueError('Enter a short search')
  out=[];scanned=0;deadline=time.monotonic()+.75
  for base,dirs,files in os.walk(self.root,followlinks=False):
   dirs[:]=[d for d in dirs if not d.startswith('.') and not (Path(base)/d).is_symlink()]
   for f in files:
    if not f.endswith('.md'):continue
    scanned+=1
    if scanned>500 or time.monotonic()>deadline:return out
    name=(Path(base)/f).relative_to(self.root).as_posix()
    try:text=self.read(name)
    except (ValueError,OSError,UnicodeError):continue
    if query.casefold()in (name+'\n'+text).casefold():out.append({'name':name,'preview':text[:160]})
    if len(out)>=30:return out
  return out
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
