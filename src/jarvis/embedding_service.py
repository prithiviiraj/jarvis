"""Local isolated EmbeddingGemma worker. Retrieval never authorizes tools or disclosure."""
import pathlib,subprocess,json,threading,sys,os
class EmbeddingService:
 def __init__(self):self.process=None;self.busy=False;self.status='Optional runtime not loaded';self.error='';self.results=[];self.links=[];self.details={};self.progress={};self.selected_root=None;self.search_query='';self.operation=0;self.lock=threading.Lock();self.generation=0
 def executable(self):
  if getattr(sys,'frozen',False):
   p=pathlib.Path(sys.executable).parent.parent/'embedding-runtime'/'jarvis-embedding.exe'
   if not p.is_file():raise ValueError('Install the separate EmbeddingGemma runtime beside JARVIS first')
   return [str(p)]
  p=pathlib.Path(__file__).resolve().parents[2]/'optional-embedding'/'runtime.py'
  python=os.environ.get('JARVIS_EMBEDDING_PYTHON')
  if not python:raise ValueError('Set JARVIS_EMBEDDING_PYTHON to the separate EmbeddingGemma environment')
  return [python,str(p)]
 def start(self,action,request):
  if self.busy:raise ValueError('Embedding runtime busy; stop first')
  if request.get('consent')is not True:raise ValueError('Allow the local embedding action first')
  if action not in ('check','setup','search','links'):raise ValueError('Unsupported embedding action')
  import copy
  request=copy.deepcopy(request)
  self.operation+=1
  self.search_query=request.get('query','')if action=='search'else''
  self.selected_root=None;self.results=[];self.links=[]
  self.busy=True;self.error='';self.progress={'phase':'starting','percent':None};ticket=self.generation;self.status={'check':'Checking installed search model files','setup':'Starting verified model download','search':'Starting local file search','links':'Looking for similar local files'}[action]
  def run():
   try:
    with self.lock:
     if self.process is None or self.process.poll()is not None:self.process=subprocess.Popen(self.executable(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
     payload=dict(request,action=action);self.process.stdin.write(json.dumps(payload,ensure_ascii=True)+'\n');self.process.stdin.flush()
     while True:
      reply=self.process.stdout.readline()
      if ticket!=self.generation:return
      if not reply:raise ValueError('Search worker stopped without a result')
      event=json.loads(reply)
      if event.get('event')!='progress':break
      progress=event.get('data',{})
      if not isinstance(progress,dict):raise ValueError('Invalid search progress')
      percent=progress.get('percent')
      if percent is not None and(type(percent)not in (int,float)or not 0<=percent<=100):raise ValueError('Invalid search progress percent')
      self.progress=progress;self.status=str(progress.get('status','Working locally'))[:240]
    if ticket!=self.generation:return
    if not reply:raise ValueError('Embedding worker stopped without a result')
    result=json.loads(reply)
    if not result.get('ok'):raise ValueError(result.get('error','Embedding unavailable'))
    data=result['data']
    if action in ('search','links'):self.selected_root=pathlib.Path(request['folder']).resolve()
    self.status=data.get('status','Local retrieval ready');self.results=data.get('results',[]);self.links=data.get('links',[]);self.details=data;self.progress={'phase':'complete','percent':100}
   except Exception as e:
    if ticket==self.generation:self.error=str(e)[:180];self.status='Embedding unavailable; working exact/text search is unchanged'
   finally:
    if ticket==self.generation:self.busy=False
  t=threading.Thread(target=run,daemon=True);t.start();return t
 def search_notes(self,root,query):
  """Explicit owner note query only. No download or silent cloud fallback."""
  if root is None or self.busy:return False
  try:self.executable()
  except ValueError:return False
  self.start('search',{'folder':str(root),'query':query,'encoders':'text','dimensions':256,'consent':True})
  return True
 def stop(self):
  self.generation+=1;self.busy=False
  if self.process is not None:self.process.kill();self.process=None
  self.progress={};self.selected_root=None;self.results=[];self.links=[];self.status='Embedding stopped; installed assets preserved'
 def select_note(self,root,name):
  if self.busy or self.selected_root is None or root is None or pathlib.Path(root).resolve()!=self.selected_root:raise ValueError('Candidate scope is not the connected vault; search that vault first')
  if not isinstance(name,str)or not name.endswith('.md')or not any(x.get('name')==name and x.get('kind')=='text'for x in self.results):raise ValueError('Choose an observed Markdown candidate')
  from .obsidian import Vault
  text=Vault(root).read(name)
  return {'name':name,'preview':text[:1200]}
 def snapshot(self):return {'operation':self.operation,'query':self.search_query,'busy':self.busy,'status':self.status,'error':self.error,'results':self.results,'links':self.links,'details':self.details,'progress':self.progress,'selected_folder':str(self.selected_root)if self.selected_root else None,'scope':'Local candidate similarity, not truth, permission, speech or action routing'}
