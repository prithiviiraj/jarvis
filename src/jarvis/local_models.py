"""Managed chat/vision catalog. No process/download/microphone on construction.

Adapted from Bigfoot95f7ffdb local/catalog.js and hardware.js, GPL-3.0-or-later.
"""
import json,math,pathlib,shutil,os
from .paths import data_root
CATALOG=json.loads(pathlib.Path(__file__).with_name('chat-assets.json').read_text())
GB=1024**3

def recommendations(hw):
 ram=float(hw.get('ram_gb',0));vram=float(hw.get('vram_gb',0)) if hw.get('dedicated') else 0
 if not all(math.isfinite(x)and x>=0 for x in (ram,vram)):raise ValueError('Invalid hardware readings')
 disk=hw.get('free_disk_gb');models=CATALOG['models'];usable=max(0,ram-3)*.8
 pick='qwen3-vl-30b'if vram>=20 else'qwen3-vl-8b'if vram>=7 else'qwen3-vl-4b'
 runs=lambda m:vram+usable>=m['memoryGB']
 chosen=next(m for m in models if m['id']==pick)
 if not runs(chosen):pick=next((m['id']for m in reversed(models)if runs(m)),'qwen3-vl-4b')
 options=[];index=next(i for i,m in enumerate(models)if m['id']==pick)
 for i,m in enumerate(models):
  total=CATALOG['runtime']['size']+sum(f['size']for f in m['files']);fits=vram+max(0,ram-3.5)>=m['memoryGB']
  note='Recommended'if m['id']==pick else'Requires more memory'if not fits else'Faster / lighter'if i<index else'Tight on memory, may be slow'if not runs(m)else'Higher quality'if vram>=m['memoryGB']else'Higher quality, slower'
  if disk is not None and float(disk)*GB<=total*1.05:fits=False;note='Not enough disk space'
  options.append({'id':m['id'],'label':m['label'],'bytes':total,'recommended':m['id']==pick,'available':fits,'note':note,'scope':'Estimated fit, not measured inference speed or quality'})
 return {'pick':pick,'options':options}

def detect_hardware(directory=None):
 directory=pathlib.Path(directory or data_root());directory.mkdir(parents=True,exist_ok=True)
 ram=None;gpu='Not checked';vram=0;dedicated=False;error=''
 if os.name=='nt':
  import ctypes,winreg
  class Memory(ctypes.Structure):_fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong)for n in ('total','available','page','available_page','virtual','available_virtual','extended')]
  s=Memory();s.length=ctypes.sizeof(s)
  if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):ram=s.total/GB
  adapters=[]
  try:
   key=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}')
   with key:
    for i in range(winreg.QueryInfoKey(key)[0]):
     try:
      with winreg.OpenKey(key,winreg.EnumKey(key,i))as k:
       name=winreg.QueryValueEx(k,'DriverDesc')[0]
       if any(x in name.lower()for x in ('basic display','remote display','virtual','hyper-v')):continue
       try:size=winreg.QueryValueEx(k,'HardwareInformation.qwMemorySize')[0]
       except OSError:size=winreg.QueryValueEx(k,'HardwareInformation.MemorySize')[0]
       if isinstance(size,bytes):size=int.from_bytes(size,'little')
       adapters.append((size/GB,name))
     except OSError:continue
   if adapters:vram,gpu=max(adapters);dedicated=vram>=2
   else:gpu='No dedicated GPU confirmed'
  except OSError:error='GPU memory unavailable; recommendation is conservative'
 else:
  try:ram=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/GB
  except (ValueError,OSError):pass
  error='Windows GPU scan unavailable on this host'
 return {'gpu':gpu,'vram_gb':round(vram,1),'dedicated':dedicated,'ram_gb':round(ram or 0,1),'free_disk_gb':round(shutil.disk_usage(directory).free/GB,1),'error':error,'scope':'Current local system read, not model readiness'}
