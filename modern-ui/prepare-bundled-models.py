"""Build-time downloads only. Copies pinned verified weights, never owner data."""
import pathlib,sys,json,shutil
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'src'))
from jarvis.models import FILES,digest,fetch_verified,verified_http
from jarvis.voice_assets import FILES as VOICES,BASE
from jarvis.laya_assets import ASSETS as LAYA
OUT=ROOT/'modern-ui'/'bundled-models';OUT.mkdir(exist_ok=True)
rows=[{'name':name,'url':url,'sha256':sha,'cap':cap}for name,(url,sha,cap)in FILES.items()]
rows += [{'name':'voices/'+name,'url':BASE+url,'sha256':sha,'cap':cap}for name,(url,sha,cap)in VOICES.items()]
rows += [{'name':'laya-browser-v32b-161d54d/'+a['name'],'url':a['url'],'sha256':a['sha256'],'cap':a['bytes'],'bytes':a['bytes']}for a in LAYA]
rows += [{'name':'embeddinggemma-2-914f7f8/'+a['name'],'url':a['url'],'sha256':a['sha256'],'cap':a['bytes'],'bytes':a['bytes']}for a in json.loads((ROOT/'optional-embedding/assets.json').read_text())]
http=verified_http()
for a in rows:
 target=OUT/a['name']
 if not target.is_file()or digest(target)!=a['sha256']:
  fetch_verified(http,a['url'],target,a['sha256'],a['cap'],notify=lambda n,b:print(n,b,flush=True))
 if 'bytes'in a and target.stat().st_size!=a['bytes']:raise RuntimeError('Unexpected bundled file size: '+a['name'])
 a['bytes']=target.stat().st_size
(OUT/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
notices=OUT/'licenses';notices.mkdir(exist_ok=True);shutil.copy2(ROOT/'optional-laya/APACHE-2.0.txt',notices/'APACHE-2.0.txt')
shutil.copy2(ROOT/'modern-ui/node_modules/3d-force-graph/LICENSE',notices/'3D-FORCE-GRAPH-MIT.txt')
for notice in (ROOT/'modern-ui/bundle-notices').glob('*.txt'):shutil.copy2(notice,notices/notice.name)
(notices/'SOURCES.txt').write_text('Pinned source model notices:\nKokoro and exported ONNX/voice assets: Apache 2.0. https://huggingface.co/Shusek00/kokoro-kmp-models\nWhisper model and CTranslate2 export: MIT. https://huggingface.co/Systran/faster-whisper-base\nSilero VAD: MIT. https://github.com/snakers4/silero-vad\nLaya browser checkpoint: Apache 2.0. https://huggingface.co/ichenney/laya-browser-v32b\nEmbeddingGemma 2: Apache 2.0 per official Google documentation. Official model card also says deployments must adhere to Gemma Prohibited Use Policy. https://huggingface.co/google/embeddinggemma-2 ; https://ai.google.dev/gemma/docs/embeddinggemma ; https://ai.google.dev/gemma/prohibited_use_policy\nSource URLs, hashes and revisions are retained in manifest.json. No user conversations or keys are bundled.\n',encoding='utf-8')
print('Verified bundled model bytes:',sum(a['bytes']for a in rows),flush=True)
