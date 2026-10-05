"""Speech-only formatting cleanup. Display text remains unchanged."""
import re,unicodedata
from .final_text import final_text
def speech_text(text):
 text=final_text(text)
 text=re.sub(r'\[(?:JARVIS|NOVA|KAI|LYRA|DEX)\]\s*','',text,flags=re.I)
 text=re.sub(r'!\[[^\]]*\]\([^)]*\)','',text)
 text=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',text)
 text=re.sub(r'```[\s\S]*?```',' Code is shown in the chat. ',text)
 text=re.sub(r'^[ \t]*#{1,6}\s*','',text,flags=re.M)
 text=re.sub(r'^[ \t]*[-*+]\s+','',text,flags=re.M)
 text=text.translate(str.maketrans('','', '`*_~'))
 text=''.join(c for c in text if not(0x1F000<=ord(c)<=0x1FAFF or 0x2600<=ord(c)<=0x27BF or ord(c)in(0xFE0F,0x200D,0x20E3)))
 # Persona names are words for TTS, even if a model spells capitals or spaced initials.
 for name in ('JARVIS','NOVA','KAI','LYRA','DEX'):
  spaced=r'\b'+r'[ .-]*'.join(name)+r'\b'
  text=re.sub(spaced,name.title(),text,flags=re.I)
 return re.sub(r'\s+',' ',text).strip()
