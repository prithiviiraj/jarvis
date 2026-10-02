"""Synthetic SAPI file synthesis on cloud runner, no physical output device claim."""
import subprocess,tempfile,pathlib,json
# Constant code; only a temporary synthetic-test output path supplied over stdin.
script="""
[Console]::InputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
$s=New-Object -ComObject SAPI.SpVoice
$v=$s.GetVoices()
if ($v.Count -lt 1) { throw 'No installed SAPI voice' }
$f=New-Object -ComObject SAPI.SpFileStream
$path=[Console]::In.ReadToEnd()
$f.Open($path,3,$false)
$s.AudioOutputStream=$f
[void]$s.Speak('JARVIS local synthetic voice check.',16)
$f.Close()
Write-Output ('SAPI file synthesis passed; installed voices: '+$v.Count)
"""
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'synthetic.wav'
 r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],input=str(p),text=True,capture_output=True,timeout=30)
 print(r.stdout);print(r.stderr)
 assert r.returncode==0,'SAPI file synthesis failed'
 assert p.exists() and p.stat().st_size>1000,'Synthetic SAPI audio missing'
 print(json.dumps({'sapi_file_synthesis':True,'bytes':p.stat().st_size,'physical_audio_output':'not run: cloud runner lacks confirmed output device','runtime_playback_and_cancellation':'not verified on physical device'}))
