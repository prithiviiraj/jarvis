"""Shared pinned CPU Pocket engine; preset embeddings only, no arbitrary audio inputs."""
import threading,pathlib,copy,os,tempfile
PRESETS={'JARVIS':'michael','NOVA':'anna','LYRA':'alba','KAI':'marius','DEX':'javert'}
class PocketCPU:
 def __init__(self,root,config=None):
  from ..pocket_assets import ready
  self.root=pathlib.Path(root)
  if not ready(self.root):raise RuntimeError('Verified Pocket presets/model missing')
  os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
  import torch
  from pocket_tts import TTSModel
  import yaml
  template=pathlib.Path(config)if config else pathlib.Path(__file__).with_name('pocket_config.yaml')
  cfg=yaml.safe_load(template.read_text());cfg['weights_path']=str(self.root/'model.safetensors');cfg['weights_path_without_voice_cloning']=cfg['weights_path'];cfg['flow_lm']['lookup_table']['tokenizer_path']=str(self.root/'tokenizer.json')
  torch.set_num_threads(2)
  with tempfile.TemporaryDirectory()as temp:
   local=pathlib.Path(temp)/'pocket.yaml';local.write_text(yaml.safe_dump(cfg));self.model=TTSModel.load_model(config=local)
  self.model.has_voice_cloning=False;self.lock=threading.Lock();self.states={}
  for name,preset in PRESETS.items():self.states[name]=self.model.get_state_for_audio_prompt(self.root/(preset+'.safetensors'))
 def profile(self,name):
  if name not in self.states:raise ValueError('Pocket preset unavailable')
  return PocketProfile(self,name)
class PocketProfile:
 def __init__(self,engine,name):self.engine=engine;self.name=name
 def synthesize(self,text):
  if not isinstance(text,str)or not text.strip()or len(text)>500:raise ValueError('Short speech text required')
  with self.engine.lock:
   state=copy.deepcopy(self.engine.states[self.name]);audio=self.engine.model.generate_audio(state,text)
   return audio.detach().cpu().numpy(),self.engine.model.sample_rate
