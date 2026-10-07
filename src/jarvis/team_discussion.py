"""Explicit user-started bounded fictional team conversation, no tools."""
import re
from .personas import prompt
ORDER=('JARVIS','NOVA','LYRA','SILA','DEX','JARVIS')
BANTER_ORDER=('JARVIS','NOVA','DEX','JARVIS','NOVA','LYRA','SILA','DEX','JARVIS')
def banter(text):return bool(re.search(r'\b(?:argue|argument|bicker|banter)\b',text,re.I))
def order(text,initiator="JARVIS"):
 if re.search(r'\beach\s+other\b',text,re.I)or (requested(text)and not re.search(r'\b(?:among|amongst|between)\s+yourselves\b',text,re.I)):return participants(text,initiator)*2+('JARVIS',)
 return BANTER_ORDER if banter(text) else ORDER
def requested(text):
 if not isinstance(text,str):return False
 if re.search(r"\b(?:do\s+not|don't|dont|never|stop|cancel)\b.{0,50}\b(?:discuss|talk|chat|speak|conversation)\b",text,re.I):return False
 if re.search(r'\b(?:discuss|talk|chat|speak)\s+(?:among|amongst|between)\s+yourselves\b|\b(?:discuss|talk|chat|speak)\b.{0,100}\beach\s+other\b',text,re.I):return True
 from .personas import ROLES
 names='|'.join(re.escape(n)for n in ROLES if n!='REO')
 # Speaking together is discussion; speaking to one profile alone is not.
 if re.search(r'\b(?:talk|chat|speak)\b.{0,70}\bwith\s+(?:the\s+)?(?:'+names+r')\b.{0,40}\btogether\b',text,re.I):return True
 # "discuss with Nova", "have a discussion with Dex", "talk to Nova about".
 verb=r'(?:discuss|discussion|conversation|talk|chat)'
 return bool(re.search(r'\b'+verb+r'\b.{0,45}\bwith\s+(?:the\s+)?(?:'+names+r')\b',text,re.I)or re.search(r'\b'+verb+r'\b.{0,45}\bto\s+(?:'+names+r')\b.{0,25}\babout\b',text,re.I))

def messages(actor,topic,context,index,final=None,addressees=None):
 actors=order(topic)
 if (index==len(actors)-1 if final is None else final):instruction='Give a final one-line useful answer to master, using only this actual discussion. Do not append a routine report label. Never claim jobs are done.'
 elif banter(topic) and index==3:instruction='End the fictional bickering now. Say Stop all! What will master think of us? Idiots. Keep it playful, no threats. Tell the team to settle.'
 elif banter(topic) and index>3:instruction='Give a short apology to Jarvis and master, then one useful sentence. The argument is over, do not restart it.'
 elif banter(topic):
  if actor=='SILA':instruction='One short reserved reply as the introverted researcher and experienced manager. Point out one verified fact from this conversation, gently organize the disagreement, and do not invent mistakes. Optional brief authored reflection stays text-only.'
  elif actor=='NOVA':instruction='One short hot-tempered reply. If your past was thrown at you, explode defensively (Why bring up the past!). Mild fictional outrage only, no slurs.'
  elif actor=='DEX':instruction='One short reply that calmly ends the debate. Practical and matured; the others are wary of you.'
  else:instruction='One short playful in-character disagreement or response to the actual preceding team words. No insults to master, no threats, no real feelings/conflict claims.'
 else:instruction='One short in-character reply to the actual preceding team words. Address teammates, not a fresh introduction. Advance the discussion toward a useful conclusion. No threats or real actions.'
 instruction+=' Keep your turn to1or2short sentences, at most45words. Write only your own reply. Never narrate or write another profile dialogue, no inline speaker labels. Master has absolute priority. Stop or quiet ends this conversation. Do not interrupt master. Only fictional discussion-mode teammates may cut into each other.'
 partners=[n for n in (addressees or participants(topic))if n!=actor]
 if final:partners=['master']
 target=', '.join(partners)or 'master'
 identity=' Current speaker: '+actor+'. Address '+target+', not yourself. Never start by calling yourself '+actor+'. Speaker labels in history name the actual speaker, not your current identity.'
 history=[dict(m,role=('user'if m.get('role')=='assistant'and not m.get('content','').startswith('['+actor+']')else m.get('role','user')))for m in context[-12:]]
 return [{'role':'system','content':prompt(actor)+identity}]+history+[{'role':'user','content':'Master requested a SHORT team conversation: '+topic[:1000]+'. '+instruction}]

def participants(text,initiator="JARVIS"):
 names=[]
 from .personas import ROLES
 pattern=r'\b('+'|'.join(re.escape(n)for n in ROLES if n!='REO')+r')\b'
 for m in re.finditer(pattern,text,re.I):
  name=m.group(1).upper()
  if name not in names:names.append(name)
 if len(names)>5:raise ValueError('Choose at most5profiles per discussion (maximum16turns)')
 if len(names)==1:
  partner=initiator if initiator in ROLES and initiator!='REO' and initiator!=names[0] else ('NOVA' if names[0]=='JARVIS' else 'JARVIS')
  return (partner,names[0])
 return tuple(names) if len(names)>=2 else ('JARVIS','NOVA','LYRA','SILA','DEX')

def clean_reply(text):
 from .persona_text import strip_speaker_tag
 text=strip_speaker_tag(text)
 if not isinstance(text,str)or not text.strip()or len(text)>3000:raise ValueError('Invalid team reply')
 from .personas import ROLES
 names='|'.join(re.escape(n)for n in ROLES)
 if re.search(r'\[(?:'+names+r')\]|(?:^|\n)\s*(?:'+names+r')\s*:',text,re.I):raise ValueError('One profile attempted to write another profile reply')
 return text
