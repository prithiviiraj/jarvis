"""Explicit optional engines. Never download or accept licenses on startup."""
from pathlib import Path
class KittenSynth:
 def __init__(self,engine,voice='Jasper',speed=1.):
  if voice not in ('Bella','Jasper','Luna','Bruno','Rosie','Hugo','Kiki','Leo'):raise ValueError('Unknown Kitten voice')
  if not .75<=speed<=1.3:raise ValueError('Use speed0.75-1.3')
  self.engine=engine;self.voice=voice;self.speed=speed
 def synthesize(self,text):
  if any('\u0b80'<=c<='\u0bff'for c in text):raise ValueError('Kitten English voice does not support Tamil text')
  return self.engine.generate(text,voice=self.voice,speed=self.speed),24000
class XTTSSynth:
 LANGUAGES=('en','es','fr','de','it','pt','pl','tr','ru','nl','cs','ar','zh-cn','ja','hu','ko','hi')
 def __init__(self,engine,reference,language='en',noncommercial=False,voice_rights=False):
  if noncommercial is not True:raise ValueError('XTTS model and outputs are restricted to non-commercial use')
  if voice_rights is not True:raise ValueError('Use only a voice recording you have permission to use')
  if language not in self.LANGUAGES:raise ValueError('XTTS-v2 does not support this language; Tamil is not listed')
  p=Path(reference).resolve(strict=True)
  if p.suffix.lower()!='.wav'or p.stat().st_size>20_000_000:raise ValueError('Choose a small local WAV reference')
  self.engine=engine;self.reference=str(p);self.language=language
 def synthesize(self,text):
  if any('\u0b80'<=c<='\u0bff'for c in text):raise ValueError('XTTS-v2 does not support Tamil text')
  return self.engine.tts(text=text,speaker_wav=self.reference,language=self.language),24000
