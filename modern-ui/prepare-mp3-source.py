"""Retained exact source for LGPLv3 MP3 wrapper, LAME and local build modification."""
import hashlib,pathlib,tarfile,urllib.request
root=pathlib.Path(__file__).resolve().parent;notice=root/'mp3-notices';notice.mkdir(exist_ok=True)
url='https://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz'
raw=urllib.request.urlopen(url,timeout=60).read(3000000)
assert hashlib.sha256(raw).hexdigest()=='ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e'
archive=notice/'lame-3.100.tar.gz';archive.write_bytes(raw)
wrapper=root/'mp3-wrapper';cmake=wrapper/'CMakeLists.txt';text=cmake.read_text();original='https://sourceforge.net/projects/lame/files/lame/3.100/lame-3.100.tar.gz/download';assert text.count(original)==1;cmake.write_text(text.replace(original,archive.resolve().as_uri()))
# Include our sole local build change and all original build files, no .git internals.
with tarfile.open(notice/'lameenc-1.8.1-corresponding-source.tar.gz','w:gz')as t:
 for p in wrapper.rglob('*'):
  if p.is_file()and '.git'not in p.relative_to(wrapper).parts:t.add(p,arcname='lameenc/'+str(p.relative_to(wrapper)))
(notice/'LAMEENC-LGPL-3.0.txt').write_bytes((wrapper/'LICENSE').read_bytes())
with tarfile.open(archive)as t:
 member=t.getmember('lame-3.100/COPYING');(notice/'LAME-LGPL-2.0.txt').write_bytes(t.extractfile(member).read())
# Repository-retained GNU GPLv3 text complements the wrapper's LGPLv3.
(notice/'GNU-GPL-3.0.txt').write_bytes((root/'mp3-GPL-3.0.txt').read_bytes())
(notice/'REBUILD-REPLACE.txt').write_text('JARVIS uses lameenc1.8.1 (LGPLv3) with LAME3.100 (LGPLv2). Wrapper pinned346b9363076cdb4dd1e4bf369a1be1a67ef1cc67. Sole local change makes CMake use the retained checksum-verified LAME archive instead of a network download. Both exact corresponding sources, license texts and build instructions are retained. The separately loaded lameenc.cp312-win_amd64.pyd in backend/_internal may be replaced with a modified interface-compatible build. No signature/hash lock prevents replacement. Rebuild with Windows x64 MSVC and Python3.12, extract the wrapper source, change its LAME archive path as needed, set SETUPTOOLS_SCM_PRETEND_VERSION=1.8.1 and install build/setuptools/setuptools-scm/wheel, then run cmake -S lameenc -B build -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPYTHON_VERSIONS=3.12 then cmake --build build --config Release. The wheel contains the replacement pyd. Keep its filename. Reverse engineering/debugging and relinking library modifications are permitted. JARVIS corresponding application source/build scripts accompany this package.\nhttps://github.com/chrisstaite/lameenc\nhttps://sourceforge.net/projects/lame/files/lame/3.100/\n')
