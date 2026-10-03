@echo off
cd /d "%~dp0"
REM Optional source dependency only. This does NOT enable camera or send media.
.venv\Scripts\python.exe -m pip install --only-binary=:all: --index-url https://pypi.org/simple opencv-python-headless==4.14.0.94
pause
