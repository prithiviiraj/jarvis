"""Pinned voice assets. Explicit download consent, no pickle or silent fallback."""
from pathlib import Path
import urllib.request
from .models import digest,fetch_verified,TLSRedirect,DownloadError,verified_http
BASE='https://huggingface.co/Shusek00/kokoro-kmp-models/resolve/d0ad239d74749828e04afb5760b30fe4d8c75d5f/'
FILES={'model.onnx': ('models/standard/kokoro-v1.0-fp32.onnx', '6bebb642a6c246f9a0f242d7aa2a1cca282c278b2d6095cd77e989103b95cfcd', 340000000), 'config.json': ('runtime/kokoro-v1.0-config.json', '5abb01e2403b072bf03d04fde160443e209d7a0dad49a423be15196b9b43c17f', 10000), 'am_puck.bin': ('voices/en-us/am_puck.bin','fcf73c989033e9233e0b98713eca600c8c74dcc1614b37009d5450ff4a2274a0',600000), 'af_heart.bin': ('voices/en-us/af_heart.bin', 'd583ccff3cdca2f7fae535cb998ac07e9fcb90f09737b9a41fa2734ec44a8f0b', 600000), 'af_sky.bin': ('voices/en-us/af_sky.bin', '4435255c9744f3f31659e0d714ab7689bf65d9e77ec1cce060f083912614f0b9', 600000), 'am_fenrir.bin': ('voices/en-us/am_fenrir.bin', 'c27989f741f7ee34d273a39d8a595cc0837d35f5ced9a29b7cc162614616df43', 600000), 'am_liam.bin': ('voices/en-us/am_liam.bin', '52403be32fd047c6a44517cb0bcd6b134f2a18baa73e70ef41651e0eab921ade', 600000), 'am_michael.bin': ('voices/en-us/am_michael.bin', '1d1f21dd8da39c30705cd4c75d039d265e9bc4a2a93ed09bc9e1b1225eb95ba1', 600000)}
def ready(root):
 return all((Path(root)/name).is_file() and digest(Path(root)/name)==sha for name,(_,sha,_) in FILES.items())
def download(root,consent=False,cancel=None,notify=lambda *a:None):
 if not consent:raise DownloadError('Approve voice model downloads first.')
 http=verified_http()
 for name,(path,sha,cap) in FILES.items():
  target=Path(root)/name
  if target.is_file() and digest(target)==sha:continue
  fetch_verified(http,BASE+path,target,sha,cap,notify=notify,cancel=cancel)
