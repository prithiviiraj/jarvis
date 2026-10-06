"""Actual preset-only CPU synthesis on Windows; no clone, microphone or playback claim."""
import pathlib,sys,json,time,hashlib,numpy as np
root=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(root.parent/'src'))
from jarvis import pocket_assets
from jarvis.experimental.pocket_cpu import PocketCPU,PRESETS
assets=root/'pocket-test-assets';pocket_assets.download(assets,consent=True);engine=PocketCPU(assets);rows=[]
for name in PRESETS:
 t=time.monotonic();audio,sr=engine.profile(name).synthesize('Hello master. I am here with the team.');elapsed=time.monotonic()-t
 assert np.sqrt(np.mean(audio**2))>.001 and sr==24000
 rows.append({'profile':name,'preset':PRESETS[name],'generation_s':elapsed,'audio_s':len(audio)/sr,'sha256':hashlib.sha256(audio.tobytes()).hexdigest()})
assert len({r['sha256']for r in rows})==5;assert engine.model.has_voice_cloning is False
(root/'ui-evidence/pocket-CPU-checks.json').write_text(json.dumps({'scope':'Actual preset-only CPU synthesis, not owner5800H/game/audio playback','threads':2,'cloning':False,'rows':rows},indent=2))
print('Pocket preset CPU synthesis passed')
