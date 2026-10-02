"""Windows candidate: real MIT native frontend -> direct Apache ONNX. No physical sound."""
import pathlib,urllib.request,hashlib,json,time,wave
import numpy as np
from jarvis.experimental.kokoro import NativeG2P,KokoroSynth
ROOT=pathlib.Path('tts-eval-models');ROOT.mkdir(exist_ok=True)
BASE='https://huggingface.co/Shusek00/kokoro-kmp-models/resolve/d0ad239d74749828e04afb5760b30fe4d8c75d5f/'
FILES={
 'model.onnx':('models/standard/kokoro-v1.0-fp32.onnx','6bebb642a6c246f9a0f242d7aa2a1cca282c278b2d6095cd77e989103b95cfcd',340000000),
 'voice.bin':('voices/en-us/af_heart.bin','d583ccff3cdca2f7fae535cb998ac07e9fcb90f09737b9a41fa2734ec44a8f0b',600000),
 'config.json':('runtime/kokoro-v1.0-config.json','5abb01e2403b072bf03d04fde160443e209d7a0dad49a423be15196b9b43c17f',10000)
}
for name,(path,expected,cap) in FILES.items():
 out=ROOT/name;h=hashlib.sha256();total=0
 with urllib.request.urlopen(BASE+path,timeout=30) as response,out.open('wb') as f:
  if not response.url.startswith('https://'):raise RuntimeError('Non-TLS redirect')
  while True:
   chunk=response.read(262144)
   if not chunk:break
   total+=len(chunk)
   if total>cap:raise RuntimeError('Oversize asset')
   f.write(chunk);h.update(chunk)
 assert h.hexdigest()==expected,'Asset checksum failed: '+name
base=pathlib.Path('phonemis-upstream');exe=base/'build/Release/phonemis_runner.exe'
t=time.perf_counter();g=NativeG2P(exe,base/'data/en-us');k=KokoroSynth(ROOT/'model.onnx',ROOT/'voice.bin',ROOT/'config.json',g);load=time.perf_counter()-t;rows=[]
try:
 for i,text in enumerate(['Hello. I am ready when you are.','Your meeting starts in ten minutes.','I found three useful ideas, and one needs your decision.','Would you like me to repeat that more slowly?','Take your time. We can work through this together.']):
  t=time.perf_counter();audio,sr=k.synthesize(text);elapsed=time.perf_counter()-t;out=pathlib.Path(f'candidate-voice-{i+1}.wav')
  with wave.open(str(out),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((audio*32767).astype('<i2').tobytes())
  rows.append({'sentence':text,'synthesis_s':elapsed,'audio_s':len(audio)/sr,'rtf':elapsed/(len(audio)/sr),'sample':str(out)})
 result={'host':'Windows cloud runner, not owner hardware','test':'Actual native G2P -> direct Kokoro FP32 ONNX -> WAV','load_s':load,'results':rows,'unrun':['physical audio playback/mic','echo/noise/barge-in','blind preference','Indian accent accuracy','end-to-first-audio','laptop gaming'],'status':'Candidate evidence only, not shipping app/installer'}
 pathlib.Path('kokoro-windows.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
finally:g.close()
