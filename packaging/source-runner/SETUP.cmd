@echo off
cd /d "%~dp0"
echo JARVIS EXPERIMENTAL - setup installs packages and downloads about 500 MB.
echo TLS checks stay ON. No API key is requested by this script.
py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if errorlevel 1 goto python
py -3.12 setup.py
goto done
:python
python setup.py
:done
if errorlevel 1 (
 echo Setup failed. Read the error above. Retry or use another network.
 pause
 exit /b 1
)
echo Ready: run LAUNCH.cmd
pause
