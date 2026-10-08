$ErrorActionPreference='Stop'
# Import the x64 MSVC tools environment for upstream nmake.
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=(& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath).Trim()
if (-not $vs) { throw 'MSVC x64 tools missing' }
$dev=Join-Path $vs 'Common7/Tools/VsDevCmd.bat'
cmd /c "`"$dev`" -arch=x64 -host_arch=x64 >nul && set" | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1],$matches[2],'Process') } }

# Build the LGPL wrapper and statically linked LAME from retained pinned sources.
# No opaque wheel whose corresponding source/binary configuration is unknown.
python -m pip install build==1.3.0 setuptools==80.9.0 setuptools-scm==9.2.0 wheel==0.45.1
if ($LASTEXITCODE -ne 0) { throw 'MP3 build dependencies failed' }
git clone --branch v1.8.1 --depth 1 https://github.com/chrisstaite/lameenc.git mp3-wrapper
if ($LASTEXITCODE -ne 0) { throw 'MP3 source clone failed' }
$commit=(git -C mp3-wrapper rev-parse HEAD).Trim()
if ($commit -ne '346b9363076cdb4dd1e4bf369a1be1a67ef1cc67') { throw 'MP3 source pin changed' }
$env:SETUPTOOLS_SCM_PRETEND_VERSION='1.8.1'
python prepare-mp3-source.py
if ($LASTEXITCODE -ne 0) { throw 'MP3 source preparation failed' }
# Upstream CMake verifies the retained local LAME tar against its published hash.
cmake -S mp3-wrapper -B mp3-build "-DCMAKE_POLICY_VERSION_MINIMUM=3.5" "-DPYTHON_VERSIONS=3.12"
if ($LASTEXITCODE -ne 0) { throw 'MP3 encoder configure failed' }
cmake --build mp3-build --config Release --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'MP3 encoder build failed' }
$wheel=(Get-ChildItem mp3-build/lameenc-*-cp312*-win_amd64.whl | Select-Object -First 1).FullName
if (-not $wheel) { throw 'Built MP3 wheel missing' }
python -m pip install --force-reinstall --no-deps $wheel
if ($LASTEXITCODE -ne 0) { throw 'Built MP3 encoder install failed' }
python -c "import lameenc; e=lameenc.Encoder(); e.set_bit_rate(64); e.set_in_sample_rate(24000); e.set_channels(1); a=e.encode(b'\x00\x00'*2400)+e.flush(); assert len(a)>100"
if ($LASTEXITCODE -ne 0) { throw 'Actual MP3 encoder check failed' }
