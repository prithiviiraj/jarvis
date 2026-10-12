"""Explicit checked model-file preparation; no automatic download or model deletion.

The catalog is adapted from Bigfoot GPL-3.0-or-later. Downloader enforces exact
size/hash and ZIP boundaries before any future managed runtime can execute.
"""
import hashlib,json,os,pathlib,shutil,threading,urllib.request,zipfile
from .local_models import CATALOG

def verified(path,item,cancel=None):
 p=pathlib.Path(path)
 if not p.is_file()or p.is_symlink()or p.stat().st_size!=item['size']:return False
 h=hashlib.sha256()
 with p.open('rb')as f:
  while True:
   if cancel and cancel.is_set():raise InterruptedError('Stopped')
   b=f.read(4*1024*1024)
   if not b:break
   h.update(b)
 return h.hexdigest()==item['sha256']

def download_checked(item,target,cancel,notify=lambda *x:None,opener=None):
 """Call only after reviewing the model/total/source/free-space. Keeps .part on Stop."""
 target=pathlib.Path(target);target.parent.mkdir(parents=True,exist_ok=True)
 if target.is_symlink():raise ValueError('Unsafe model path')
 if verified(target,item,cancel):return target
 if cancel.is_set():raise InterruptedError('Stopped')
 part=target.with_name(target.name+'.part')
 if part.is_symlink():raise ValueError('Unsafe partial file')
 start=part.stat().st_size if part.exists()else 0
 if start>item['size']:raise ValueError('Partial file exceeds expected size')
 if start==item['size']:
  if not verified(part,item,cancel):raise ValueError('Partial file checksum failed; remove only this partial file after review')
  os.replace(part,target);return target
 if shutil.disk_usage(target.parent).free<item['size']-start+128*1024*1024:raise ValueError('Not enough free disk space')
 url=item['url']
 if not url.startswith(('https://huggingface.co/','https://github.com/ggml-org/llama.cpp/releases/download/')):raise ValueError('Unapproved model source')
 request=urllib.request.Request(url,headers={'Range':f'bytes={start}-'}if start else{})
 opening=opener or urllib.request.urlopen
 with opening(request,timeout=30)as r:
  status=getattr(r,'status',200);append=False
  if start and status==206:
   value=r.headers.get('Content-Range','');append=value.startswith(f'bytes {start}-')
   if not append:raise ValueError('Wrong resumed download offset')
  elif status!=200:raise ValueError('Unexpected download response')
  done=start if append else 0
  with part.open('ab'if append else'wb')as f:
   while True:
    if cancel.is_set():raise InterruptedError('Stopped; partial file kept')
    b=r.read(min(1024*1024,item['size']-done+1))
    if not b:break
    if done+len(b)>item['size']:raise ValueError('Download exceeded pinned size')
    f.write(b);done+=len(b);notify('download',{'done':done,'total':item['size']})
 if not verified(part,item,cancel):raise ValueError('Downloaded file failed pinned size/checksum; never installed')
 os.replace(part,target);notify('verified',{'bytes':item['size']});return target

def extract_runtime(archive,destination,cancel,max_bytes=256*1024*1024):
 """Extract only regular runtime files within an owned staging directory."""
 destination=pathlib.Path(destination)
 if destination.exists():raise ValueError('Runtime destination must be new; installed runtime preserved')
 stage=destination.with_name(destination.name+'.staging')
 if stage.exists():raise ValueError('Runtime staging already exists')
 with zipfile.ZipFile(archive)as z:
  entries=z.infolist()
  if not 1<=len(entries)<=2000 or sum(x.file_size for x in entries)>max_bytes:raise ValueError('Runtime archive exceeds limits')
  names=set()
  for x in entries:
   name=x.filename.replace('\\','/');p=pathlib.PurePosixPath(name)
   if p.is_absolute()or '..'in p.parts or ':'in name or name in names or (x.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe runtime archive path')
   names.add(name)
   if not x.is_dir()and p.suffix.lower()not in ('.exe','.dll','.txt','.md','.json','.html')and name!='LICENSE-LLVM-OpenMP':raise ValueError('Unexpected runtime file')
  if not any(pathlib.PurePosixPath(n).name=='llama-server.exe'for n in names):raise ValueError('Runtime server missing')
  if not verified(archive,CATALOG['runtime'],cancel):raise ValueError('Runtime archive checksum not verified')
  stage.mkdir(parents=True)
  try:
   for x in entries:
    if cancel.is_set():raise InterruptedError('Runtime install stopped')
    out=stage/pathlib.PurePosixPath(x.filename.replace('\\','/'))
    if x.is_dir():out.mkdir(parents=True,exist_ok=True);continue
    out.parent.mkdir(parents=True,exist_ok=True)
    with z.open(x)as src,out.open('wb')as dst:shutil.copyfileobj(src,dst)
   receipt={'archive_sha256':CATALOG['runtime']['sha256'],'files':{str(p.relative_to(stage)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()for p in stage.rglob('*')if p.is_file()}}
   (stage/'verified-files.json').write_text(json.dumps(receipt))
   os.replace(stage,destination)
  except BaseException:shutil.rmtree(stage);raise
 return destination

def verify_runtime_receipt(directory):
 directory=pathlib.Path(directory)
 try:
  receipt=json.loads((directory/'verified-files.json').read_text());files=receipt['files']
  if receipt.get('archive_sha256')!=CATALOG['runtime']['sha256']or not isinstance(files,dict)or'llama-server.exe'not in files:return False
  for name,digest in files.items():
   relative=pathlib.PurePosixPath(name);p=directory/relative
   if relative.is_absolute()or '..'in relative.parts or '\\'in name or ':'in name or not isinstance(digest,str)or len(digest)!=64 or p.is_symlink()or not p.is_file():return False
   if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:return False
  actual={str(p.relative_to(directory)).replace('\\','/')for p in directory.rglob('*')if p.is_file()and p.suffix.lower()in('.exe','.dll')}
  expected={n for n in files if pathlib.PurePosixPath(n).suffix.lower()in('.exe','.dll')}
  return actual==expected
 except (OSError,ValueError,KeyError,TypeError):return False
