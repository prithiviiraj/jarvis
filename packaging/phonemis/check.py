"""Synthetic native bridge test only. No microphone, owner audio or app adoption."""
import subprocess,pathlib,time,json,sys
base=pathlib.Path('phonemis-upstream');exe=next(base.glob('build/**/phonemis_runner.exe'));data=base/'data/en-us'
t=time.perf_counter();p=subprocess.Popen([str(exe),str(data/'lexicon_full.json'),str(data/'phonemizer_en_us.bin'),str(data/'tagger.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
try:
 assert p.stdout.readline().strip()=='READY','Native bridge did not start'
 load=time.perf_counter()-t;rows=[]
 for text in ['Hello. I am ready when you are.','The FBI and CIA are in the USA.','Your meeting starts in ten minutes.','Jarvis checks extraordinary names and abbreviations.']:
  t=time.perf_counter();p.stdin.write(text+'\n');p.stdin.flush();phones=p.stdout.readline().strip();elapsed=time.perf_counter()-t
  assert phones and phones!='ERROR','Native bridge returned no phonemes'
  rows.append({'text':text,'phonemes':phones,'seconds':elapsed})
 assert rows[1]['phonemes'].startswith('ði '),'Acronym vowel context regressed'
 p.stdin.close();p.wait(timeout=5);assert p.returncode==0,'Native bridge failed'
 result={'host':'Windows cloud runner, no owner hardware','native_load_s':load,'results':rows,'limits':['No TTS audio','No physical playback','No owner accent','Not app integration or installer','No full binary/model redistribution clearance']}
 pathlib.Path('phonemis-windows.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
finally:
 if p.poll() is None:p.terminate();p.wait(timeout=5)
