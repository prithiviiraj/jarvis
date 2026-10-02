@echo off
cd /d "%~dp0"
echo This test uses the Groq key saved in Windows Credential Manager.
echo It sends a fixed greeting. No key or reply text is printed or logged.
echo Only continue if your Groq account is on the Free plan.
set /p "confirm=Type YES to approve this greeting test: "
if /I not "%confirm%"=="YES" exit /b 1
if not exist ".venv\Scripts\python.exe" (
 echo Put GROQ-DIAG.py and GROQ-DIAG.cmd beside LAUNCH.cmd after setup.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" GROQ-DIAG.py --model llama-3.3-70b-versatile --free-plan --consent
pause
