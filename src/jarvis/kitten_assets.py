"""Optional pinned Kitten15M int8 weights, ~28MB including eight voice styles."""
from pathlib import Path
from .models import digest,fetch_verified,DownloadError,verified_http
BASE='https://huggingface.co/KittenML/kitten-tts-nano-0.8-int8/resolve/84781d74e29ee25217551556398b42f80593a813/'
FILES={'model.onnx':('kitten_tts_nano_v0_8.onnx','f7b0afcbee92870b32b8e0276d855b954dc25470c9f051b376ac7eee537c76fc',25000000),'voices.npz':('voices.npz','8aa7cee235abb0739cb51e6559685f65a4dacd95568833d05699b1633f519b3f',3400000),'config.json':('config.json','b66006ccbeccd4de5fc3c9272059c47f5725df7215fd889785c03602652fab64',2000)}
def ready(root):return all((Path(root)/n).is_file()and digest(Path(root)/n)==sha for n,(_,sha,_)in FILES.items())
def download(root,consent=False,cancel=None,notify=lambda *a:None):
 if consent is not True:raise DownloadError('Review Kitten model download first')
 http=verified_http()
 for name,(path,sha,cap)in FILES.items():
  target=Path(root)/name
  if target.is_file()and digest(target)==sha:continue
  fetch_verified(http,BASE+path,target,sha,cap,notify=notify,cancel=cancel)
