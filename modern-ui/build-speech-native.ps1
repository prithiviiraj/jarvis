$ErrorActionPreference='Stop'
git clone --branch v4.8.2 --depth 1 --recurse-submodules --shallow-submodules https://github.com/OpenNMT/CTranslate2.git ct2-cpu
if ($LASTEXITCODE -ne 0) { throw 'Pinned CPU source clone failed' }
$prefix = Join-Path (Get-Location) 'ct2-install'
cmake -S ct2-cpu -B ct2-cpu/build -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_INSTALL_PREFIX="$prefix" -DBUILD_CLI=OFF -DBUILD_TESTS=OFF -DWITH_MKL=OFF -DWITH_DNNL=OFF -DWITH_CUDA=OFF -DWITH_CUDNN=OFF -DWITH_RUY=ON -DOPENMP_RUNTIME=COMP
if ($LASTEXITCODE -ne 0) { throw 'CPU configure failed' }
cmake --build ct2-cpu/build --config Release --target install --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'CPU build failed' }
Copy-Item "$prefix/bin/ctranslate2.dll" ct2-cpu/python/ctranslate2/
$env:CTRANSLATE2_ROOT=$prefix
python -m pip install pybind11==2.11.1 wheel setuptools
Push-Location ct2-cpu/python
python setup.py bdist_wheel
if ($LASTEXITCODE -ne 0) { throw 'CPU wheel failed' }
$wheel = (Get-ChildItem dist/*.whl | Select-Object -First 1).FullName
python -m pip install --force-reinstall --no-deps $wheel
if ($LASTEXITCODE -ne 0) { throw 'CPU wheel install failed' }
Pop-Location
python -m pip download --no-deps faster-whisper==1.2.1 --dest pcm-input
python ../packaging/stt/build_pcm_fork.py pcm-input/faster_whisper-1.2.1-py3-none-any.whl pcm-wheel
python -m pip install onnxruntime==1.23.2 sounddevice==0.5.6 numpy==2.2.6 pyyaml==6.0.3 pcm-wheel/faster_whisper-1.2.1-py3-none-any.whl
if ($LASTEXITCODE -ne 0) { throw 'Speech dependencies failed' }
# Do not ship optional ASIO or other architecture audio binaries.
python -c "import pathlib,sounddevice; p=pathlib.Path(sounddevice.__file__).parent/'_sounddevice_data/portaudio-binaries'; [x.unlink() for x in p.glob('*.dll') if x.name!='libportaudio64bit.dll']; import importlib.util; assert importlib.util.find_spec('av') is None; import ctranslate2; assert not list(pathlib.Path(ctranslate2.__file__).parent.glob('libiomp*')); assert not list(pathlib.Path(ctranslate2.__file__).parent.glob('*cudnn*'))"
if ($LASTEXITCODE -ne 0) { throw 'CPU-only runtime check failed' }
git clone https://github.com/IgorSwat/Phonemis.git phonemis-upstream
Push-Location phonemis-upstream
git checkout 71eb1ce33bd586d38cbac037843b8539d7829c3b
git apply ../../packaging/phonemis/evaluation-fixes.patch
if ($LASTEXITCODE -ne 0) { throw 'Native speech patch failed' }
Copy-Item ../../packaging/phonemis/runner.cpp src/phonemis/main.cpp -Force
Pop-Location
cmake -S phonemis-upstream -B phonemis-upstream/build -DBUILD_RUNNER=ON -DBUILD_TESTS=ON -DCMAKE_CXX_FLAGS="/utf-8 /EHsc"
cmake --build phonemis-upstream/build --config Release --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Native frontend build failed' }
Push-Location phonemis-upstream
& ./build/Release/phonemis_test.exe
if ($LASTEXITCODE -ne 0) { throw 'Native frontend tests failed' }
Pop-Location
python prepare-speech-resources.py
if ($LASTEXITCODE -ne 0) { throw 'Native resources failed' }
