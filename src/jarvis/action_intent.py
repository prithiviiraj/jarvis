"""Bounded explicit browser intents for any persona. Questions do not become effects."""
import re
from .browser_control import parse_voice

def parse(text):
 if not isinstance(text,str):return None
 t=re.sub(r'^\s*(?:(?:hey|hi|hello)[,!]?\s+)?(?:(?:jarvis|nova|kai|lyra|dex|reo)[,:!]?\s+)?','',text,flags=re.I).strip()
 t=re.sub(r'^(?:(?:can|could|would)\s+you\s+|please\s+)','',t,flags=re.I)
 t=re.sub(r'\s+please[.!?]*$','',t,flags=re.I).strip().rstrip('?!')
 if re.fullmatch(r'open (?:this |the |a )?browser',t,re.I):return {'command':'open-window','value':''}
 m=re.fullmatch(r'scroll\s+(?:(slightly|a little)\s*)?(up|down)?(?:\s+(slightly|a little))?',t,re.I)
 if m:
  return {'command':'scroll-'+(m.group(2)or'down')+('-small'if m.group(1)or m.group(3)else''),'value':''}
 if re.match(r'^(?:what|when|why|how|is|are|do|does)\b',t,re.I):return None
 if t.lower().startswith(('open https://','open http://','open www.')):return parse_voice('browser '+t)
 if t.lower().startswith('browser '):
  proposal=parse_voice(t)
  return proposal if proposal and proposal['command']in ('open','search','scroll-down','scroll-up','open-window')else None
 return None

def goal(text):
 if not isinstance(text,str):return None
 from .reo_commands import parse as reo_parse
 normalized=re.sub(r'^\s*(?:(?:hey|hi|hello)[,!]?\s+)?(?:(?:jarvis|nova|kai|lyra|dex|reo)[,:!]?\s+)?','',text,flags=re.I).strip()
 normalized=re.sub(r'^(?:(?:can|could|would)\s+you\s+|please\s+)','',normalized,flags=re.I)
 if re.match(r'^(?:what|when|why|how|is|are|do|does)\b',normalized,re.I):return None
 if normalized.lower()in ('browser read links',)or re.fullmatch(r'browser (?:choose|select) link \d+[.!]?',normalized,re.I):return None
 return reo_parse('Reo '+normalized)
