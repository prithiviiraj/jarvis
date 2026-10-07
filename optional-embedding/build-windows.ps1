$ErrorActionPreference='Stop'
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'Torch install failed' }
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt pyinstaller==6.16.0
if ($LASTEXITCODE -ne 0) { throw 'Embedding requirements failed' }
& ./.venv/Scripts/python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Embedding dependency check failed' }
& ./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean --onedir --console --name jarvis-embedding --collect-all sentence_transformers --collect-all transformers --collect-all torch --collect-all tokenizers --collect-all safetensors --collect-all huggingface_hub --collect-all sklearn --collect-all scipy --collect-all librosa --collect-all av --collect-all PIL --add-data 'assets.json;.' runtime.py
if ($LASTEXITCODE -ne 0) { throw 'Embedding frozen build failed' }
Copy-Item -Recurse -Force dist/jarvis-embedding embedding-runtime
& ./.venv/Scripts/python.exe distribution-notices.py
if ($LASTEXITCODE -ne 0) { throw 'Embedding third-party notices failed' }
$reply = '{"action":"check","consent":true}' | & ./embedding-runtime/jarvis-embedding.exe
if ($LASTEXITCODE -ne 0) { throw 'Embedding frozen startup failed' }
$data = $reply | ConvertFrom-Json
if ($data.ok -ne $true -or $data.data.model_bytes -ne 1525787092) { throw 'Embedding frozen protocol check failed' }
