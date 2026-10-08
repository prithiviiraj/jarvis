"""Local isolated EmbeddingGemma worker. Retrieval never authorizes tools or disclosure."""
import pathlib,subprocess,json,threading,sys,os
class EmbeddingService:
 def __init__(self):self.process=None;self.busy=False;self.status='Optional runtime not loaded';self.error='';self.results=[];self.links=[];self.details={};self.selected_root=None;self.lock=threading.Lock();self.generation=0
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
  self.selected_root=None;self.results=[];self.links=[]
  self.busy=True;self.error='';ticket=self.generation;self.status='EmbeddingGemma '+action
  def run():
   try:
    with self.lock:
     if self.process is None or self.process.poll()is not None:self.process=subprocess.Popen(self.executable(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
     payload=dict(request,action=action);self.process.stdin.write(json.dumps(payload,ensure_ascii=True)+'\n');self.process.stdin.flush();reply=self.process.stdout.readline()
    if ticket!=self.generation:return
    if not reply:raise ValueError('Embedding worker stopped without a result')
    result=json.loads(reply)
    if not result.get('ok'):raise ValueError(result.get('error','Embedding unavailable'))
    data=result['data']
    if action in ('search','links'):self.selected_root=pathlib.Path(request['folder']).resolve()
    self.status=data.get('status','Local retrieval ready');self.results=data.get('results',[]);self.links=data.get('links',[]);self.details=data
   except Exception as e:
    if ticket==self.generation:self.error=str(e)[:180];self.status='Embedding unavailable; working exact/text search is unchanged'
   finally:
    if ticket==self.generation:self.busy=False
  t=threading.Thread(target=run,daemon=True);t.start();return t
 def stop(self):
  self.generation+=1;self.busy=False
  if self.process is not None:self.process.kill();self.process=None
  self.selected_root=None;self.results=[];self.links=[];self.status='Embedding stopped; installed assets preserved'
 def select_note(self,root,name):
  if self.busy or self.selected_root is None or root is None or pathlib.Path(root).resolve()!=self.selected_root:raise ValueError('Candidate scope is not the connected vault; search that vault first')
  if not isinstance(name,str)or not name.endswith('.md')or not any(x.get('name')==name and x.get('kind')=='text'for x in self.results):raise ValueError('Choose an observed Markdown candidate')
  from .obsidian import Vault
  text=Vault(root).read(name)
  return {'name':name,'preview':text[:1200]}
 def snapshot(self):return {'busy':self.busy,'status':self.status,'error':self.error,'results':self.results,'links':self.links,'details':self.details,'selected_folder':str(self.selected_root)if self.selected_root else None,'scope':'Local candidate similarity, not truth, permission, speech or action routing'}
