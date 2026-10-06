"""Explicit addressed list, not mere name mentions or STT adjacent-name ambiguity."""
import re
def addressed(text):
 if not isinstance(text,str):return ()
 from .personas import ROLES
 options='|'.join(re.escape(n)for n in ROLES if n!='REO')
 match=re.match(r'^\s*(?:(?:hey|hi|hello)\s+)?('+options+r')\b',text,re.I)
 if not match:return ()
 names=[match.group(1).upper()];rest=text[match.end():]
 while True:
  nxt=re.match(r'\s*(?:,\s*(?:and\s+)?|and\s+|&\s*)('+options+r')\b',rest,re.I)
  if not nxt:break
  name=nxt.group(1).upper()
  if name not in names:names.append(name)
  rest=rest[nxt.end():]
 return tuple(names)if len(names)>=2 else ()
def request(actor,topic,context):
 from .personas import prompt
 return [{'role':'system','content':prompt(actor)+' The user explicitly addressed several teammates. Reply as '+actor+' only, directly to master, in1or2short sentences. Follow the named order. Use the actual prior replies to avoid copying them; vary naturally, not at random facts. If only called by name, acknowledge warmly. Never fabricate another teammate reply or completed work. This is not a discussion or extra summary turn.'}]+context[-12:]+[{'role':'user','content':topic[:1000]}]
