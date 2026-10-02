"""CPU-only evaluation environment trimming, not license clearance or shipping.
Deletes only known optional GPU/ASIO/other-architecture binaries under installed packages.
Run before any audio import. Preserve required Intel OpenMP DLL for CPU.
"""
import pathlib,sysconfig,json,hashlib
root=pathlib.Path(sysconfig.get_paths()['purelib']).resolve()
allowed={
 'ctranslate2/cudnn64_9.dll',
 '_sounddevice_data/portaudio-binaries/libportaudio32bit.dll',
 '_sounddevice_data/portaudio-binaries/libportaudio32bit-asio.dll',
 '_sounddevice_data/portaudio-binaries/libportaudio64bit-asio.dll',
 '_sounddevice_data/portaudio-binaries/libportaudioarm64.dll',
 '_sounddevice_data/portaudio-binaries/libportaudioarm64-asio.dll',
}
rows=[]
for name in sorted(allowed):
 p=root/name
 if p.is_file():
  rows.append({'relative_path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size});p.unlink()
assert (root/'ctranslate2/libiomp5md.dll').is_file(),'Required CPU OpenMP DLL missing'
assert (root/'_sounddevice_data/portaudio-binaries/libportaudio64bit.dll').is_file(),'Required x64 non-ASIO DLL missing'
result={'removed':rows,'reason':'CPU-only x64/non-ASIO evaluation','not_claimed':'not redistribution/license acceptance or physical mic proof'}
pathlib.Path('native-trim-evaluation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
