"""Local speech engine preference only, no consent or sensor state persists."""
from pathlib import Path
import json,os
class VoicePreferences:
 def __init__(self,path):self.path=Path(path)
 def load(self):
  try:
   if self.path.stat().st_size>1000:return 'kokoro'
   data=json.loads(self.path.read_text(encoding='utf-8'))
   return data['engine']if set(data)=={'engine'}and data['engine']=='kokoro'else'kokoro'
  except (OSError,ValueError,KeyError,TypeError):return 'kokoro'
 def save(self,engine):
  if engine!='kokoro':raise ValueError('Unsupported speech engine')
  self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp')
  temp.write_text(json.dumps({'engine':engine}),encoding='utf-8');os.replace(temp,self.path)
