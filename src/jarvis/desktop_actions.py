"""Fixed Windows app-launch targets. No shell, arguments, arbitrary paths or inference."""
import re,os,pathlib,subprocess
APPS={'notepad':('Notepad','notepad.exe'),'calculator':('Calculator','calc.exe'),'paint':('Paint','mspaint.exe')}
def prepare(text):
 if not isinstance(text,str):return None
 t=re.sub(r'^\s*(?:(?:hey|hi|hello)[,!]?\s+)?(?:(?:jarvis|nova|sila|lyra|dex|laya)[.,:!]?\s+)?','',text,flags=re.I).strip()
 t=re.sub(r'^(?:(?:can|could|would)\s+you\s+|please\s+)','',t,flags=re.I)
 m=re.fullmatch(r'(?:open|launch)\s+(?:the\s+)?(notepad|calculator|paint)(?:\s+app)?(?:\s+for me)?[.!?]*',t,re.I)
 if not m:return None
 app=m.group(1).lower();return {'action':'launch-app','app':app,'label':APPS[app][0],'target':'Windows System32/'+APPS[app][1]}
def validate(proposal):
 if not isinstance(proposal,dict)or proposal.get('app')not in APPS:raise ValueError('Choose Notepad, Calculator or Paint')
 expected=prepare('open '+proposal['app'])
 if proposal!=expected:raise ValueError('App proposal changed; review again')
 return expected

def launch(proposal,reviewed,confirm=False):
 proposal=validate(proposal)
 if confirm is not True or reviewed!=proposal:raise ValueError('Review the exact app before opening')
 if os.name!='nt':raise RuntimeError('App launch is Windows-only')
 import ctypes
 buf=ctypes.create_unicode_buffer(32768)
 n=ctypes.windll.kernel32.GetWindowsDirectoryW(buf,len(buf))
 if not n or n>=len(buf):raise RuntimeError('Windows folder unavailable')
 exe=pathlib.Path(buf.value)/'System32'/APPS[proposal['app']][1]
 if not exe.is_file():raise RuntimeError(proposal['label']+' is not installed at its approved Windows location')
 process=subprocess.Popen([str(exe)],shell=False,close_fds=True)
 return {'app':proposal['label'],'pid':process.pid,'status':'Launch submitted. Window visibility is not yet verified.'}
