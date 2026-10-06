"""Lossless request handoff. Relative date/time/duration are never guessed."""
import re

def draft(text):
 if not isinstance(text,str)or not text.strip()or len(text)>2000:raise ValueError('Short calendar request required')
 # A conservative explicit phrase may supply place; retain the whole request too.
 m=re.search(r'\b(?:go to|at)\s+([^.!?\n]{1,200})[.!?]?$',text,re.I)
 place=m.group(1).strip() if m else ''
 return {'request':text,'title':'','start':'','end':'','timezone':'','place':place,'notes':text,'missing':['title','exact start date and time','exact end date and time','timezone'],'scope':'Draft only. Relative dates and this time are unresolved. No event, reminder or Google change yet.'}
