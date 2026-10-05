"""Separate reviewed Windows local proposal runtime, never an executor."""
import pathlib,sys,json,os,hashlib,urllib.request,tempfile,threading,http.server
ROOT=pathlib.Path(sys.executable).parent if getattr(sys,'frozen',False)else pathlib.Path(__file__).resolve().parent
ASSETS=json.loads((ROOT/'assets.json').read_text())
CACHE=pathlib.Path(os.environ.get('LOCALAPPDATA',str(pathlib.Path.home()))) / 'JarvisLocal' / 'models' / 'laya-browser-v32b-161d54d'
def valid(path,asset):
 if not path.is_file()or path.stat().st_size!=asset['bytes']:return False
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()==asset['sha256']
def install():
 print('Downloading 1,322,020,017 bytes of pinned Apache2 model assets to '+str(CACHE),flush=True)
 for asset in ASSETS:
  path=CACHE/asset['name'];path.parent.mkdir(parents=True,exist_ok=True)
  if valid(path,asset):continue
  part=path.with_suffix(path.suffix+'.part')
  try:
   with urllib.request.urlopen(asset['url'],timeout=60)as r,part.open('wb')as f:
    size=0
    while True:
     b=r.read(1024*1024)
     if not b:break
     size+=len(b)
     if size>asset['bytes']:raise ValueError('Oversize asset')
     f.write(b)
   if not valid(part,asset):raise ValueError('Asset integrity check failed')
   part.replace(path)
  finally:part.unlink(missing_ok=True)
 print('Assets verified. No server, browser, microphone or actions started.',flush=True)
def serve():
 if not all(valid(CACHE/a['name'],a)for a in ASSETS):raise RuntimeError('Use the reviewed model setup first. No automatic download.')
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['USE_TF']='0';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
 import laya,torch
 torch.set_num_threads(min(4,os.cpu_count()or 1))
 agent=laya.load(str(CACHE),device='cpu',expected_sha256={a['name']:a['sha256']for a in ASSETS})
 if 'head_max_len_train'in agent.cfg:agent.cfg['head_max_len']=agent.cfg['head_max_len_train']
 lock=threading.Lock()
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def reply(self,status,obj):
   b=json.dumps(obj,ensure_ascii=True).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  def do_GET(self):self.reply(200,{'status':'ready','engine':'Laya','checkpoint':'161d54d','actions':False})if self.path=='/health'else self.reply(404,{'error':'unsupported'})
  def do_POST(self):
   if self.path!='/v1/systemone':self.reply(404,{'error':'unsupported'});return
   if not lock.acquire(blocking=False):self.reply(503,{'error':'busy'});return
   try:
    size=int(self.headers.get('Content-Length','0'))
    if not 0<size<=16384:raise ValueError('size')
    body=json.loads(self.rfile.read(size))
    if set(body)!={'state','questions'}or not isinstance(body['state'],dict)or not isinstance(body['questions'],dict)or set(body['questions'])-{'operation','target'}or 'operation'not in body['questions']:raise ValueError('schema')
    for q in body['questions'].values():
     if not isinstance(q,dict)or set(q)!={'type','instructions','criteria'}or q['type']!='choice'or not isinstance(q['instructions'],str)or len(q['instructions'])>2000 or not isinstance(q['criteria'],dict)or not 1<=len(q['criteria'])<=20 or any(not isinstance(k,str)or not isinstance(v,str)or len(v)>300 for k,v in q['criteria'].items()):raise ValueError('questions')
    result=agent.predict(body['state'],body['questions']);self.reply(200,{'answers':result['answers']})
   except Exception:self.reply(400,{'error':'proposal unavailable'})
   finally:lock.release()
 print('Laya ready on127.0.0.1:8000. No browser executor. Close this window to stop.',flush=True)
 http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
if __name__=='__main__':
 try:
  if '--install-reviewed'in sys.argv:install()
  elif '--serve'in sys.argv:serve()
  elif '--version'in sys.argv:print(json.dumps({'engine':'Laya','models_bundled':False,'model_bytes':sum(a['bytes']for a in ASSETS),'actions':False}))
  else:print('Use SETUP MODELS.cmd to review assets, then START LAYA.cmd. No effect started.')
 except Exception as e:print(type(e).__name__+': '+str(e),flush=True);raise SystemExit(1)
