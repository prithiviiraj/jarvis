"""Explicit user-started bounded fictional team conversation, no tools."""
import re
from .personas import prompt
ORDER=('JARVIS','NOVA','LYRA','KAI','DEX','JARVIS')
BANTER_ORDER=('JARVIS','NOVA','DEX','JARVIS','NOVA','LYRA','KAI','DEX','JARVIS')
def banter(text):return bool(re.search(r'\b(?:argue|argument|bicker|banter)\b',text,re.I))
def order(text):return BANTER_ORDER if banter(text) else ORDER
def requested(text):return bool(re.search(r'\b(?:discuss|talk|chat)\s+(?:among|amongst|between)\s+yourselves\b',text,re.I))
def messages(actor,topic,context,index):
 actors=order(topic)
 if index==len(actors)-1:instruction='Give a final one-line concrete report to master, using only this discussion. Say the team has settled, not that jobs are done.'
 elif banter(topic) and index==3:instruction='End the fictional bickering now. Say Stop all! What will master think of us? Idiots. Keep it playful, no threats. Tell the team to settle.'
 elif banter(topic) and index>3:instruction='Give a short apology to Jarvis and master, then one useful sentence. The argument is over, do not restart it.'
 elif banter(topic):
  if actor=='KAI':instruction='One short reply as the team recorder: cite an actual earlier mistake from the supplied conversation to win, if one exists. Never invent one. Dry, smug, few words.'
  elif actor=='NOVA':instruction='One short hot-tempered reply. If your past was thrown at you, explode defensively (Why bring up the past!). Mild fictional outrage only, no slurs.'
  elif actor=='DEX':instruction='One short reply that calmly ends the debate. Practical and matured; the others are wary of you.'
  else:instruction='One short playful in-character disagreement or response to the actual preceding team words. No insults to master, no threats, no real feelings/conflict claims.'
 else:instruction='One short in-character reply to the actual preceding team words. Address teammates, not a fresh introduction. Advance the discussion toward a useful conclusion. No threats or real actions.'
 instruction+=' Master has absolute priority. Stop or quiet ends this conversation. Do not interrupt master. Only fictional discussion-mode teammates may cut into each other.'
 return [{'role':'system','content':prompt(actor)}]+context[-12:]+[{'role':'user','content':'Master requested a SHORT team conversation: '+topic[:1000]+'. '+instruction}]
