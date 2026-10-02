"""Explicit first-run downloads, pinned bytes and atomic publication. No model bundling."""
import hashlib
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit
WHISPER_REV='ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66'
SILERO_REV='1e261b036686cd0017d500ee96acd1c4ba572a9d'
FILES={
 'whisper-base/config.json':('https://huggingface.co/Systran/faster-whisper-base/resolve/'+WHISPER_REV+'/config.json','56a6d8110d311f19c8f0471e562832c7527f146b567275bfca59fcf7c184da9a',100000),
 'whisper-base/model.bin':('https://huggingface.co/Systran/faster-whisper-base/resolve/'+WHISPER_REV+'/model.bin','d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9',160000000),
 'whisper-base/tokenizer.json':('https://huggingface.co/Systran/faster-whisper-base/resolve/'+WHISPER_REV+'/tokenizer.json','fb7b63191e9bb045082c79fd742a3106a12c99513ab30df4a0d47fa6cb6fd0ab',4000000),
 'whisper-base/vocabulary.txt':('https://huggingface.co/Systran/faster-whisper-base/resolve/'+WHISPER_REV+'/vocabulary.txt','34ce3fe1c5041027b3f8d42912270993f986dbc4bb34cf27f951e34a1e453913',1000000),
 'silero.onnx':('https://raw.githubusercontent.com/snakers4/silero-vad/'+SILERO_REV+'/src/silero_vad/data/silero_vad.onnx','1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3',4000000)
}
class DownloadError(RuntimeError):pass
class TLSRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urlsplit(newurl).scheme!='https':raise DownloadError('Insecure download redirect refused.')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def ready(root):
 return all((Path(root)/name).is_file() and digest(Path(root)/name)==entry[1] for name,entry in FILES.items())
def download(root,consent=False,notify=lambda *a:None,cancel=None):
 if not consent:raise DownloadError('Approve the model download first.')
 root=Path(root);http=urllib.request.build_opener(urllib.request.ProxyHandler({}),TLSRedirect())
 for name,(url,sha,cap) in FILES.items():
  target=root/name
  if target.is_file() and digest(target)==sha:continue
  target.parent.mkdir(parents=True,exist_ok=True);part=target.with_name(target.name+'.part')
  try:
   h=hashlib.sha256();total=0
   with http.open(url,timeout=30) as response,part.open('wb') as f:
    if urlsplit(response.url).scheme!='https':raise DownloadError('Insecure download refused.')
    for chunk in iter(lambda:response.read(1024*256),b''):
     if cancel is not None and cancel.is_set():raise DownloadError('Model download cancelled.')
     total+=len(chunk)
     if total>cap:raise DownloadError('Model download exceeded expected size.')
     f.write(chunk);h.update(chunk);notify(name,total)
   if h.hexdigest()!=sha:raise DownloadError('Model checksum failed. File was not installed.')
   part.replace(target)
  except Exception:
   part.unlink(missing_ok=True)
   raise DownloadError('Model download failed or was cancelled. Check your network and retry. Existing verified files are preserved.') from None
