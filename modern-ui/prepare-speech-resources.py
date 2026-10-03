"""Pinned native speech resources and retained binary source notices."""
import pathlib,shutil,json,hashlib,urllib.request,sys
root=pathlib.Path(__file__).resolve().parent
native=root/'native-voice';(native/'en-us').mkdir(parents=True,exist_ok=True)
base=root/'phonemis-upstream'
shutil.copy2(base/'build/Release/phonemis_runner.exe',native/'phonemis_runner.exe')
for name in ['lexicon_full.json','phonemizer_en_us.bin','tagger.json']:shutil.copy2(base/'data/en-us'/name,native/'en-us'/name)
rows={name:hashlib.sha256((native/name).read_bytes()).hexdigest() for name in ['phonemis_runner.exe','en-us/lexicon_full.json','en-us/phonemizer_en_us.bin','en-us/tagger.json']}
(native/'manifest.json').write_text(json.dumps(rows,indent=2))
notices=root/'speech-notices';notices.mkdir(exist_ok=True)
for name in ['LICENSE','third_party/spdlog/LICENSE','third_party/cpu_features/LICENSE','third_party/cxxopts/LICENSE','third_party/ruy/LICENSE','third_party/ruy/third_party/cpuinfo/LICENSE','third_party/ruy/third_party/cpuinfo/deps/clog/LICENSE']:
 src=root/'ct2-cpu'/name;target=notices/'CTranslate2'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
shutil.copytree(root.parent/'packaging/phonemis',notices/'Phonemis',ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
shutil.copy2(base/'LICENSE',notices/'PHONEMIS-UPSTREAM-LICENSE.txt')
pylicense=pathlib.Path(sys.base_prefix)/'LICENSE.txt'
if pylicense.exists():shutil.copy2(pylicense,notices/'PYTHON-LICENSE.txt')
url='https://www.portaudio.com/license.html'
with urllib.request.urlopen(url,timeout=30) as response:(notices/'PORTAUDIO-LICENSE.html').write_bytes(response.read(200000))
(notices/'BUILD-NOTES.txt').write_text('CTranslate2 4.8.2 built CPU-only from pinned tag, Ruy backend, compiler OpenMP; no Intel MKL/OpenMP/CUDA DLLs. faster-whisper PCM-only fork: ndarray microphone input only, no PyAV. Phonemis pinned MIT native frontend and retained transitive notices. Models download by explicit user button and checksum verification; no weight files bundled. PortAudio x64 non-ASIO only.\n')
