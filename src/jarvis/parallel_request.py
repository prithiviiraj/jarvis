"""One explicit bounded command plus an independent question. No model-chosen effects."""
import re
from .action_intent import parse

def split(text):
 if not isinstance(text,str)or len(text)>2000:return None
 match=re.fullmatch(r'\s*(.+?)\s+(?:and|while)\s+(?:tell me|explain|answer)\s+(.+?)\s*',text,re.I)
 if not match:return None
 command,question=match.groups()
 if re.search(r'\b(?:do not|don\x27t|never|instead|then|send|pay|delete|upload|password|credential)\b',command,re.I):return None
 proposal=parse(command)
 if not proposal or proposal['command']not in ('open-window','open','search'):return None
 if not question.strip()or len(question)>1000:return None
 return {'command_text':command,'proposal':proposal,'question':question.strip()}
