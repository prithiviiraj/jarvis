"""Optional XTTS local server entry. Model download requires explicit CPML review.
Separate from default JARVIS backend; fixed loopback binding, no external files.
"""
import sys,json,pathlib,os

def main():
 if '--version' in sys.argv:
  import importlib.metadata as m
  print(json.dumps({'engine':'coqui-tts','version':m.version('coqui-tts'),'models_bundled':False,'model_license':'CPML non-commercial model and outputs'}));return
 # Do not set COQUI_TOS_AGREED or silently download weights.
 print('Optional engine setup is not complete. Review XTTS-v2 CPML for non-commercial use, then install verified model assets. No model download, server or microphone was started.',flush=True)
 if '--serve' in sys.argv:raise SystemExit(2)
if __name__=='__main__':main()
