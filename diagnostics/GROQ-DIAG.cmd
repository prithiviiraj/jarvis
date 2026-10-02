@echo off
cd /d "%~dp0"
echo JARVIS Groq diagnostic v3 uses the key saved in Windows Credential Manager.
echo It checks active models, then sends at most one fixed greeting.
echo No key, response text or raw error body is printed or logged.
echo Only continue if your Groq account is on the Free plan.
set /p "confirm=Type YES to approve models lookup and one greeting: "
if /I not "%confirm%"=="YES" exit /b 1
if not exist ".venv\Scripts\python.exe" (
 echo Place both diagnostic files beside LAUNCH.cmd after setup.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" GROQ-DIAG.py --free-plan --consent
pause
