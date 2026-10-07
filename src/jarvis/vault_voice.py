"""Explicit local vault commands. Never infer access from ordinary chat."""
import re

def parse_voice(text):
 if not isinstance(text,str):return None
 text=re.sub(r'^(?:hey\s+|hi\s+|hello\s+)?(?:jarvis|nova|sila|lyra|dex)[,:]?\s+','',text.strip(),flags=re.I)
 match=re.fullmatch(r'(?:obsidian|vault)\s+(search|read)\s+(.+)',text,flags=re.I)
 if not match:
  if re.match(r'^(?:obsidian|vault)\s+(?:search|read|create|write|delete|open|edit|overwrite)\b',text,re.I):raise ValueError('Use explicit vault search words or vault read Exact/Note.md. Spoken writes are not enabled; nothing was sent to a model.')
  return None
 action,value=match.groups();value=value.strip()
 if action.lower()=='search':
  if len(value)>100:raise ValueError('Use a search of up to 100 characters')
  return {'command':'vault-search','query':value}
 # Keep exact names, including punctuation and case. No fuzzy file selection.
 if len(value)>240:raise ValueError('Use a note path of up to 240 characters')
 return {'command':'vault-read','note_name':value}
