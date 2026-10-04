"""CPU synthesis software acceptance, no microphone or playback proof."""
import sys,pathlib,json,time,hashlib,numpy as np
root=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(root.parent/'src'))
from jarvis import kitten_assets
from jarvis.experimental.kokoro import NativeG2P
from jarvis.experimental.kitten_onnx import KittenONNX
assets=root/'kitten-test-assets';kitten_assets.download(assets,consent=True)
g2p=NativeG2P(root/'native-voice/phonemis_runner.exe',root/'native-voice/en-us');results=[]
try:
 for voice in ['Jasper','Luna','Bruno','Rosie','Hugo']:
  synth=KittenONNX(assets,g2p,voice);t=time.perf_counter();audio,sr=synth.synthesize('Hello, I am ready to help you. What should we do next?');seconds=time.perf_counter()-t
  assert np.sqrt(np.mean(audio**2))>.01
  results.append({'voice':voice,'synthesis_s':seconds,'audio_s':len(audio)/sr,'sha256':hashlib.sha256(audio.tobytes()).hexdigest()})
 assert len({r['sha256']for r in results})==5
finally:g2p.close()
(root/'ui-evidence/kitten-CPU-checks.json').write_text(json.dumps({'scope':'actual local CPU software synthesis, no physical playback or real API response','frontend':'existing MIT native, not upstream espeak','results':results},indent=2))
