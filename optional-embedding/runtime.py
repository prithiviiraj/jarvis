"""Separate interpreter for Transformers5. No network except explicit verified model setup."""
import pathlib,sys,json,os,hashlib,urllib.request
ROOT=pathlib.Path(sys._MEIPASS)if getattr(sys,'frozen',False)else pathlib.Path(__file__).resolve().parent
CACHE=pathlib.Path(os.environ.get('JARVIS_DATA_DIR',str(pathlib.Path(os.environ.get('LOCALAPPDATA',pathlib.Path.home()))/'JARVIS')))/'models'/'embeddinggemma-2-914f7f8'
ASSETS=json.loads((ROOT/'assets.json').read_text());MODEL=None;MODE=None
TYPES={'.md':'text','.txt':'text','.py':'code','.ts':'code','.tsx':'code','.js':'code','.json':'code','.jpg':'image','.jpeg':'image','.png':'image','.webp':'image','.mp4':'video','.mov':'video','.wav':'audio','.mp3':'audio','.flac':'audio'}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def verified():return all((CACHE/a['name']).is_file()and(CACHE/a['name']).stat().st_size==a['bytes']and digest(CACHE/a['name'])==a['sha256']for a in ASSETS)
def setup():
 for a in ASSETS:
  p=CACHE/a['name'];p.parent.mkdir(parents=True,exist_ok=True)
  if p.is_file()and p.stat().st_size==a['bytes']and digest(p)==a['sha256']:continue
  part=p.with_suffix(p.suffix+'.part')
  try:
   with urllib.request.urlopen(a['url'],timeout=60)as r,part.open('wb')as f:
    size=0
    while True:
     b=r.read(1024*1024)
     if not b:break
     size+=len(b)
     if size>a['bytes']:raise ValueError('Oversize model asset')
     f.write(b)
   if size!=a['bytes']or digest(part)!=a['sha256']:raise ValueError('Model checksum mismatch')
   part.replace(p)
  finally:part.unlink(missing_ok=True)
 return {'status':'Verified EmbeddingGemma assets ready; no owner files indexed'}
def load(mode):
 global MODEL,MODE
 if MODEL is not None and MODE==mode:return MODEL
 if mode not in ('text','vision','audio','all'):raise ValueError('Unsupported encoder set')
 if not verified():raise ValueError('Run the reviewed1.526GB model setup first')
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',USE_TF='0')
 import torch
 from sentence_transformers import SentenceTransformer
 configs={'text':{'vision_config':None,'audio_config':None},'vision':{'audio_config':None},'audio':{'vision_config':None},'all':{}}
 device='cuda'if torch.cuda.is_available()else'cpu';dtype=torch.bfloat16 if device=='cuda'and torch.cuda.is_bf16_supported()else torch.float32
 torch.set_num_threads(min(4,os.cpu_count()or 1))
 MODEL=None
 import gc;gc.collect()
 if torch.cuda.is_available():torch.cuda.empty_cache()
 MODEL=SentenceTransformer(str(CACHE),config_kwargs=configs[mode],model_kwargs={'torch_dtype':dtype},device=device,local_files_only=True,trust_remote_code=False);MODE=mode;return MODEL
def records(folder,mode):
 root=pathlib.Path(folder).resolve(strict=True)
 if not root.is_dir():raise ValueError('Choose a local folder')
 result=[];seen=0
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if not d.startswith('.')and not(pathlib.Path(base)/d).is_symlink())
  for name in sorted(files):
   seen+=1
   if seen>2000 or len(result)>=100:return result,True
   p=pathlib.Path(base)/name;kind=TYPES.get(p.suffix.lower())
   if name.startswith('.')or not kind or p.is_symlink()or not p.resolve().is_relative_to(root):continue
   if kind in ('text','code'):
    if p.stat().st_size>100000:continue
    try:text=p.read_text(encoding='utf-8')
    except(UnicodeError,OSError):continue
    # Bounded context chunks; no claim that the whole file was represented.
    for i in range(0,min(len(text),24000),6000):result.append({'name':p.relative_to(root).as_posix(),'kind':kind,'chunk':i//6000,'input':text[i:i+6000]})
   elif mode!='text'and(kind=='image'and mode in ('vision','all')or kind=='video'and mode in ('vision','all')or kind=='audio'and mode in ('audio','all')):
    if p.stat().st_size<=100*1024*1024:result.append({'name':p.relative_to(root).as_posix(),'kind':kind,'chunk':0,'input':{kind:str(p)}})
   if len(result)>=100:return result[:100],True
 return result,False
def media_input(row):
 if row['kind']=='audio':
  import librosa,numpy as np
  data,sr=librosa.load(row['input']['audio'],sr=16000,mono=True,duration=30)
  if not len(data)or not np.isfinite(data).all():raise ValueError('Invalid audio sample')
  return {'audio':data}
 if row['kind']=='video':
  import av
  from PIL import Image
  frames=[];last=-1
  with av.open(row['input']['video'])as container:
   for frame in container.decode(video=0):
    stamp=float(frame.time or 0)
    if stamp>=30:break
    if int(stamp)>last:frames.append(frame.to_image());last=int(stamp)
    if len(frames)>=29:break
  if not frames:raise ValueError('No video frames decoded')
  # Interleaved visual sample, not an invented timestamp-level answer.
  return {'text':'Video sample: '+' '.join('<|image|>'for _ in frames),'image':frames}
 return row['input']
def retrieve(request,model=None):
 import numpy as np
 mode=request.get('encoders','text');dims=request.get('dimensions',768)
 if dims not in (768,512,256,128):raise ValueError('Supported dimensions:768,512,256,128')
 query=request.get('query','')
 if request['action']=='search'and(not isinstance(query,str)or not query.strip()or len(query)>1000):raise ValueError('Enter a short retrieval query')
 rows,truncated=records(request['folder'],mode)
 if not rows:return {'status':'No supported files in the selected scope','results':[],'links':[]}
 model=model or load(mode);vectors=[]
 if len(rows)>100:raise ValueError('Retrieval scope exceeded')
 for r in rows:
  kwargs={'truncate_dim':dims,'normalize_embeddings':True,'convert_to_numpy':True}
  if r['kind']in ('text','code'):kwargs['prompt_name']='Document'
  vector=np.asarray(model.encode(media_input(r)if r['kind']in ('audio','video')else r['input'],**kwargs),dtype='float32').reshape(-1)
  if vector.shape!=(dims,)or not np.isfinite(vector).all()or np.linalg.norm(vector)==0:raise ValueError('Invalid document embedding')
  vectors.append(vector/np.linalg.norm(vector))
 matrix=np.asarray(vectors);base={'status':'Local similarity candidates ready','truncated':truncated,'chunks':len(rows),'dimensions':dims,'model_revision':'914f7f89142e33e77833254d9c9b90c3cef7303b','scope':'Similarity is not truth. Text first24kchars in6kchunks; audio first30seconds mono16kHz; video first30seconds up to29frames; not full long-video coverage. No files changed or context sent.'}
 if request['action']=='links':
  scores=matrix@matrix.T;links=[]
  for i,r in enumerate(rows):
   for j in np.argsort(-scores[i]):
    if i<int(j)and r['name']!=rows[int(j)]['name']:links.append({'source':r['name'],'target':rows[int(j)]['name'],'score':float(scores[i,j]),'type':'suggested similarity'});break
  return dict(base,links=sorted(links,key=lambda x:-x['score'])[:30],results=[])
 q=np.asarray(model.encode(query,prompt_name='SearchQuery',truncate_dim=dims,normalize_embeddings=True,convert_to_numpy=True),dtype='float32').reshape(-1)
 if q.shape!=(dims,)or not np.isfinite(q).all()or np.linalg.norm(q)==0:raise ValueError('Invalid query embedding')
 scores=matrix@(q/np.linalg.norm(q));order=np.argsort(-scores,kind='stable')[:10]
 return dict(base,results=[{k:rows[int(i)][k]for k in ('name','kind','chunk')}|{'score':float(scores[i])}for i in order],links=[])
def execute(r):
 if r.get('consent')is not True:raise ValueError('Local scope consent required')
 if r['action']=='setup':return setup()
 if r['action']=='check':return {'status':'Verified assets ready'if verified()else'Model assets missing or unverified','model_bytes':sum(a['bytes']for a in ASSETS),'license':'Apache2 per official card'}
 if r['action']in ('search','links'):return retrieve(r)
 raise ValueError('Unsupported action')
if __name__=='__main__':
 for line in sys.stdin:
  try:result={'ok':True,'data':execute(json.loads(line))}
  except Exception as e:result={'ok':False,'error':type(e).__name__+': '+str(e)[:160]}
  print(json.dumps(result,ensure_ascii=True),flush=True)
