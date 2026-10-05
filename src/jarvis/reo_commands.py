"""Explicit Reo action goals only. Questions stay in chat; no inferred authority."""
import re

def parse(text):
 if not isinstance(text,str):return None
 m=re.match(r'^\s*(?:(?:hey|hi|hello)[,!:]?\s+)?(?:jarvis[,!:]?\s+)?(?:(?:ask|tell)\s+)?reo[,!:]?\s+(?:to\s+)?(.+?)\s*$',text,re.I)
 if not m:return None
 goal=m.group(1).strip()
 if not re.match(r'^(?:browser\b|open\b|navigate\b|scroll\b|click\b|find\b|search\b|read\b|action\b|do\b)',goal,re.I):return None
 if len(goal)>1000:raise ValueError('Use a Reo action goal under1000characters')
 return goal
