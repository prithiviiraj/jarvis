"""Reproducible MIT faster-whisper PCM-only fork, no PyAV/FFmpeg wheel.
Evaluation only until isolated Linux AND Windows regression/real fixture pass.
Preserves source license; changed files explicitly recorded. File decoding is refused.
"""
import base64,csv,hashlib,io,pathlib,re,sys,zipfile
src=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
expected='79a66ad50688c0b794dd501dc340a736992a6342f7f95e5811be60b5224a26a7'
if hashlib.sha256(src.read_bytes()).hexdigest()!=expected:raise RuntimeError('Unpinned input wheel')
z=zipfile.ZipFile(src);files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
audio='faster_whisper/audio.py';s=files[audio].decode();s=s.replace('import av\n','')
start=s.index('    resampler = ');end=s.index('\n\ndef pad_or_trim(')
s=s[:start]+'''    raise ValueError("This JARVIS PCM-only fork accepts float32 microphone arrays, not audio files.")
'''+s[end:];files[audio]=s.encode()
meta=next(n for n in files if n.endswith('.dist-info/METADATA'));s=files[meta].decode();s=re.sub(r'^Requires-Dist: av[^\n]*\n','',s,flags=re.M);files[meta]=s.encode()
files['faster_whisper/JARVIS_PCM_FORK.txt']=b'''Modified from faster-whisper1.2.1 (MIT). Changes: audio.py removes PyAV decoder, refuses file input, retains pad_or_trim; METADATA removes av dependency. ndarray transcription/features/model unchanged. No PyAV/FFmpeg shipped. Source+license in wheel; modifications publicly reproducible.\n'''
record=next(n for n in files if n.endswith('.dist-info/RECORD'));buf=io.StringIO();writer=csv.writer(buf,lineterminator='\n')
for n,data in sorted(files.items()):
 if n!=record:writer.writerow([n,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('='),len(data)])
writer.writerow([record,'','']);files[record]=buf.getvalue().encode()
out=dest/src.name
with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as target:
 for n,data in sorted(files.items()):
  info=zipfile.ZipInfo(n,(2026,10,2,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o644<<16;target.writestr(info,data)
print(out,hashlib.sha256(out.read_bytes()).hexdigest())
