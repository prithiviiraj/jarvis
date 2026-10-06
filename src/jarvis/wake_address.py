"""Conservative ambiguity check. Never silently rewrite recognized speech."""
import re
def ambiguous(text,names):
 if not isinstance(text,str):return False
 options='|'.join(re.escape(n)for n in names)
 match=re.match(r'^\s*(?:(?:hey|hi|hello)[,!.:]?\s+)?('+options+r')\s+('+options+r')\b',text,re.I)
 return bool(match and match.group(1).upper()!=match.group(2).upper())
