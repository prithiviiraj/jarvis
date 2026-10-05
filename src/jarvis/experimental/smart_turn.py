"""Optional offline Smart Turn3.2 CPU adapter. No automatic fetch or microphone."""
from pathlib import Path
import math
REV='f766f81d3cfdf7737ac64aad813d91bbfd56bf93'
SHA='2bb026316b14a660486a75b1733cd3fbab8c2fd0314dc9af7be49f8cca967e4f'
SIZE=8679182
URL='https://huggingface.co/pipecat-ai/smart-turn-v3/resolve/'+REV+'/smart-turn-v3.2-cpu.onnx'
def ready(path):
 from ..models import digest
 path=Path(path);return path.is_file()and path.stat().st_size==SIZE and digest(path)==SHA
class SmartTurn:
 def __init__(self,path):
  if not ready(path):raise ValueError('Verified Smart Turn3.2 assets missing')
  import numpy as np
  import onnxruntime as ort
  self.np=np
  opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
  self.session=ort.InferenceSession(str(path),sess_options=opts,providers=['CPUExecutionProvider'])
 def complete(self,frames):
  from .turn_features import features
  input_features=features(self.np.concatenate(frames))
  probability=float(self.session.run(None,{'input_features':input_features})[0][0].item())
  if not math.isfinite(probability)or not 0<=probability<=1:raise ValueError('Invalid Smart Turn output')
  return probability>.5

def download(path,consent=False,cancel=None):
 if consent is not True:raise ValueError('Review Smart Turn download first')
 from ..models import fetch_verified,verified_http
 if not ready(path):fetch_verified(verified_http(),URL,path,SHA,SIZE,cancel=cancel)
class TurnSetup:
 def __init__(self):
  import threading
  self.busy=False;self.status='Not checked';self.error='';self.cancel=threading.Event()
 def start(self,consent=False,check=False):
  if self.busy:raise ValueError('Turn model setup is busy')
  if not check and consent is not True:raise ValueError('Review turn model download')
  import threading
  from ..paths import data_root
  self.busy=True;self.error='';self.cancel.clear()
  def run():
   try:
    path=data_root()/'models'/'smart-turn.onnx'
    if not check:download(path,consent=True,cancel=self.cancel)
    self.status='Verified model ready; mic OFF'if ready(path)else'Verified model missing'
   except Exception as e:self.error=str(e)[:160];self.status='Setup stopped; installed assets preserved'
   finally:self.busy=False
  worker=threading.Thread(target=run,daemon=True);worker.start();return worker
 def stop(self):self.cancel.set()
 def snapshot(self):return {'busy':self.busy,'status':self.status,'error':self.error,'model_bytes':SIZE}
