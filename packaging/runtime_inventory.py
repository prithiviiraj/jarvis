"""Exact installed Windows inputs and notices. Inventory is evidence, not clearance."""
import importlib.metadata as md,pathlib,hashlib,json,sysconfig,shutil
out=pathlib.Path('runtime-audit');out.mkdir(exist_ok=True);licenses=out/'notices';licenses.mkdir(exist_ok=True)
root=pathlib.Path(sysconfig.get_paths()['purelib']);rows=[];native=[];missing=[]
for d in sorted(md.distributions(),key=lambda x:x.metadata['Name'].lower()):
 name=d.metadata['Name'];version=d.version;notes=[]
 for f in d.files or []:
  p=d.locate_file(f)
  if not p.is_file():continue
  if any(token in p.name.lower() for token in ('license','copying','notice','copyright')):
   dest=licenses/(name+'-'+version)/str(f);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
   notes.append({'path':str(f),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  if p.suffix.lower() in ('.dll','.pyd','.exe'):
   native.append({'distribution':name,'version':version,'path':str(f),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 rows.append({'name':name,'version':version,'license_metadata':d.metadata.get('License'),'classifiers':[x for x in d.metadata.get_all('Classifier',[]) if x.startswith('License')],'notices':notes})
 if not notes:missing.append(name)
for f in [pathlib.Path(sysconfig.get_config_var('installed_base'))/'LICENSE.txt']:
 if f.is_file():shutil.copy2(f,licenses/'PYTHON-LICENSE.txt')
base=pathlib.Path('phonemis-upstream')
for name in ['LICENSE','data/en-us/lexicon_full.json','data/en-us/phonemizer_en_us.bin','data/en-us/tagger.json','build/Release/phonemis_runner.exe']:
 p=base/name
 if p.is_file():native.append({'distribution':'Phonemis pinned source/resources','path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for p in pathlib.Path('packaging/phonemis').rglob('*.txt'):
 dest=licenses/'Phonemis'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
result={'scope':'installed Windows inputs, not necessarily frozen outputs','packages':rows,'native_inputs':native,'packages_without_notice_files':missing,'status':'REVIEW REQUIRED. This manifest does not assert redistribution clearance.'}
(out/'inventory.json').write_text(json.dumps(result,indent=2));print(json.dumps({'packages':len(rows),'native_inputs':len(native),'without_notice_files':missing},indent=2))
