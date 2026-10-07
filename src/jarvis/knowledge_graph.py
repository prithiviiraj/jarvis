"""Bounded local visual index. Markdown is data, never executable instructions."""
import os,re,time,pathlib
class KnowledgeGraph:
 def __init__(self):self.cached={'nodes':[],'edges':[],'state':'disconnected','scope':'Local note names and links only'};self.last=-1e20;self.root=None
 def snapshot(self,root):
  if root is None:self.root=None;return {'nodes':[],'edges':[],'state':'disconnected','scope':'Connect a local vault to see real nodes'}
  base=pathlib.Path(root).resolve()
  if base==self.root and time.monotonic()-self.last<10:return self.cached
  self.root=base;self.last=time.monotonic();nodes=[];edges=[];truncated=False;scanned=0;skipped=0;deadline=time.monotonic()+.15
  try:
   if not base.is_dir():raise OSError('Selected vault is unavailable')
   for folder,dirs,files in os.walk(base,followlinks=False):
    dirs[:]=sorted(d for d in dirs if not d.startswith('.')and not(pathlib.Path(folder)/d).is_symlink())
    for f in sorted(files):
     if not f.endswith('.md')or f.startswith('.'):continue
     if len(nodes)>=240 or scanned>=500 or time.monotonic()>deadline:truncated=True;break
     scanned+=1;p=pathlib.Path(folder)/f
     if not p.resolve().is_relative_to(base)or p.is_symlink()or p.stat().st_size>100000:skipped+=1;continue
     try:text=p.read_text(encoding='utf-8')
     except(OSError,UnicodeError):skipped+=1;continue
     name=p.relative_to(base).as_posix();category=name.split('/')[0]if '/'in name else'Notes';title=next((l[2:].strip()for l in text.splitlines()if l.startswith('# ')),p.stem)
     nodes.append({'id':name,'label':title[:80],'category':category,'preview':re.sub(r'^---.*?---\s*','',text,flags=re.S)[:1200]})
     for target in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]',text)[:50]:edges.append({'source':name,'target':target.split('#')[0]})
    if truncated:break
   ids={n['id']for n in nodes};stems={}
   for n in nodes:stems.setdefault(pathlib.Path(n['id']).stem,[]).append(n['id'])
   clean=[]
   for e in edges:
    t=e['target'];t=t if t.endswith('.md')else t+'.md'
    local=(pathlib.Path(e['source']).parent/t).as_posix();resolved=t if t in ids else local if local in ids else stems.get(pathlib.Path(t).stem,[None])[0]if len(stems.get(pathlib.Path(t).stem,[]))==1 else None
    if resolved:clean.append({'source':e['source'],'target':resolved})
   self.cached={'nodes':nodes,'edges':clean,'state':'ready','truncated':truncated,'skipped':skipped,'scope':'Local Markdown and explicit wiki links; no invented knowledge'}
  except OSError:self.cached={'nodes':[],'edges':[],'state':'unavailable','scope':'Vault unavailable; no invented replacement nodes'}
  return self.cached
