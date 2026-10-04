"""Optional Apache2 Kitten ONNX weights plus existing MIT native pronunciation.
No upstream Kitten package, eSpeak/GPL or Torch/CUDA dependencies bundled.
Different frontend from upstream: quality must be compared before changing default.
"""
import json,threading,re
from pathlib import Path
from .kokoro import VoiceError
_LOCK=threading.RLock();_SESSIONS={}
SYMBOLS="$"+';:,.!?¡¿—…"«»"" '+ 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'+"ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊˋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"
# Keep the exact published token vocabulary, including duplicate symbols.
SYMBOLS=SYMBOLS.replace('ˋ','ʋ')
class KittenONNX:
 def __init__(self,root,g2p,voice='Jasper'):
  import numpy as np,onnxruntime as ort
  self.np=np;self.g2p=g2p;self.root=Path(root);self.voice=voice
  self.config=json.loads((self.root/'config.json').read_text());self.vocab={c:i for i,c in enumerate(SYMBOLS)}
  opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
  with _LOCK:
   key=str(self.root/'model.onnx')
   if key not in _SESSIONS:_SESSIONS[key]=ort.InferenceSession(key,sess_options=opts,providers=['CPUExecutionProvider'])
   self.session=_SESSIONS[key]
  self.voices=np.load(self.root/'voices.npz',allow_pickle=False)
  if voice not in self.config['voice_aliases']:raise VoiceError('Unknown Kitten voice')
 def synthesize(self,text):
  if not isinstance(text,str)or not text or len(text)>400 or any('\u0b80'<=c<='\u0bff'for c in text):raise VoiceError('Kitten voice needs a short English clause; Tamil not supported')
  np=self.np;voice=self.config['voice_aliases'][self.voice]
  with _LOCK:
   phones=self.g2p.phonemize(text)
   phones=' '.join(re.findall(r'\w+|[^\w\s]',phones))
   if any(c not in self.vocab for c in phones):raise VoiceError('Kitten pronunciation contains unsupported tokens')
   tokens=[self.vocab[c]for c in phones]
   style=self.voices[voice][min(len(text),self.voices[voice].shape[0]-1):][:1]
   audio=self.session.run(None,{'input_ids':np.array([[0,*tokens,10,0]],np.int64),'style':style,'speed':np.array([self.config['speed_priors'].get(voice,1.)],np.float32)})[0].reshape(-1)
   audio=audio[:-5000]
   if not 0<len(audio)<=24000*40 or not np.isfinite(audio).all():raise VoiceError('Kitten voice output invalid')
   return np.clip(audio,-1,1).astype(np.float32),24000
