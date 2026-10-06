"""Conservative local-only casual routing. Short wording does not imply casual intent."""
import re

def casual(text):
 if not isinstance(text,str):return False
 t=text.lower().strip()
 t=re.sub(r'^(?:hey\s+)?(?:jarvis|nova|lyra|kai|dex|master)[,:.!]?\s+','',t).strip().rstrip('.!?')
 return bool(re.fullmatch(r'(?:hi|hey|hello|good (?:morning|afternoon|evening|night)|how are you|how are you doing|are you there|can you hear me|thanks|thank you|okay|ok|love you|i love you|flirt with me|tease me|say something cute)',t))

def local_turn(messages):
 """Only authenticated workflow construction chooses idle, never content claims."""
 if not isinstance(messages,list):return False
 for row in reversed(messages):
  if isinstance(row,dict)and row.get('role')=='user':return casual(row.get('content'))
 return False
