"""Optional English Moonshine tiny adapter. Windows native notices audit pending.
No automatic download; verified model directory required. No microphone opened.
"""
import json,threading
from pathlib import Path
from ..speech import SpeechCancelled,UnclearSpeech
FILES=json.loads(Path(__file__).with_name('moonshine-assets.json').read_text())
def ready(root):
 from ..models import digest
 return all((Path(root)/r['name']).is_file()and (Path(root)/r['name']).stat().st_size==r['size']and digest(Path(root)/r['name'])==r['sha256']for r in FILES)
def download(root,consent=False,cancel=None):
 if consent is not True:raise ValueError('Review Moonshine44MB English model download first')
 from ..models import fetch_verified,verified_http,digest
 http=verified_http()
 for r in FILES:
  path=Path(root)/r['name']
  if path.is_file()and digest(path)==r['sha256']:continue
  fetch_verified(http,r['url'],path,r['sha256'],r['size'],cancel=cancel)
class MoonshineSTT:
 def __init__(self,root,language='en'):
  if language!='en':raise ValueError('Moonshine tiny adapter supports English only; use Whisper for Tamil')
  if not ready(root):raise ValueError('Verified Moonshine tiny English assets missing')
  from moonshine_voice import Transcriber,ModelArch
  self.model=Transcriber(Path(root),model_arch=ModelArch.TINY);self.lock=threading.RLock()
 def transcribe(self,audio):return self.transcribe_cancellable(audio)
 def transcribe_cancellable(self,audio,cancel=None):
  def check():
   if cancel is not None and cancel.is_set():raise SpeechCancelled('Speech recognition cancelled')
  check()
  with self.lock:
   check();result=self.model.transcribe_without_streaming(audio.tolist(),sample_rate=16000);check()
   text=' '.join(line.text for line in result.lines).strip()
   if not text or len(text)>2000:raise UnclearSpeech('No reliable short English transcript')
   return text
 def close(self):self.model.close()
