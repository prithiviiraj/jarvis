"""Fixed installation locations only. Never execute model-supplied paths or flags."""
import os,pathlib
Path=pathlib.Path
def find_brave():
 if os.name!='nt':raise RuntimeError('Brave desktop control requires Windows')
 bases=[os.environ.get('PROGRAMFILES'),os.environ.get('PROGRAMFILES(X86)'),os.environ.get('LOCALAPPDATA')]
 for base in bases:
  if not base:continue
  p=Path(base)/'BraveSoftware'/'Brave-Browser'/'Application'/'brave.exe'
  if p.is_file():return str(p)
 raise RuntimeError('Brave not found in standard install locations. Install Brave first; no Edge fallback or ordinary-profile access.')
