@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run SETUP.cmd first. Python 3.12 is required.
 pause
 exit /b 1
)
set "PYTHONPATH=%~dp0src"
".venv\Scripts\python.exe" -m jarvis --workspace-preview
if errorlevel 1 pause
