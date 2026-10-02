"""Source-only runner plus licensed native frontend. Never include venv or owner state."""
import pathlib,shutil,json,hashlib,zipfile
root=pathlib.Path('source-runner/JARVIS-EXPERIMENTAL');root.mkdir(parents=True,exist_ok=True)
for folder in ['src','docs']:shutil.copytree(folder,root/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
for p in pathlib.Path('packaging/source-runner').iterdir():shutil.copy2(p,root/p.name)
shutil.copy2('THIRD_PARTY.md',root/'THIRD_PARTY.md')
base=pathlib.Path('phonemis-upstream');native=root/'native-voice';native.mkdir(exist_ok=True)
shutil.copy2(base/'build/Release/phonemis_runner.exe',native/'phonemis_runner.exe');(native/'en-us').mkdir(exist_ok=True)
for name in ['lexicon_full.json','phonemizer_en_us.bin','tagger.json']:shutil.copy2(base/'data/en-us'/name,native/'en-us'/name)
manifest={name:hashlib.sha256((native/name).read_bytes()).hexdigest() for name in ['phonemis_runner.exe','en-us/lexicon_full.json','en-us/phonemizer_en_us.bin','en-us/tagger.json']};(native/'manifest.json').write_text(json.dumps(manifest,indent=2))
licenses=root/'licenses';licenses.mkdir(exist_ok=True)
shutil.copy2(base/'LICENSE',licenses/'PHONEMIS-UPSTREAM-LICENSE.txt')
for p in pathlib.Path('packaging/phonemis').rglob('*.txt'):shutil.copy2(p,licenses/p.name)
# Include changed native source and pinned upstream pointer for reproducibility.
shutil.copytree('packaging/phonemis',root/'native-source',dirs_exist_ok=True)
print(root)
