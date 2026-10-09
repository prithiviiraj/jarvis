"""Explicit user note-search intent only. No model reads or guessed files."""
import re
def parse(text):
 if not isinstance(text,str):return None
 text=re.sub(r'^\s*(?:(?:hey|hi|hello)[,!.:]?\s+)?(?:jarvis|lyra|dex|laya)[,.:]?\s+','',text,flags=re.I).strip()
 m=re.fullmatch(r'(?:search (?:my |the )?(?:notes|vault|obsidian) (?:for )?|find (?:in|from) (?:my |the )?(?:notes|vault|obsidian)\s+)(.+?)[.!?]*',text,re.I)
 if not m:return None
 query=m.group(1).strip()
 if not 0<len(query)<=100:raise ValueError('Use a note query up to100characters')
 return query
