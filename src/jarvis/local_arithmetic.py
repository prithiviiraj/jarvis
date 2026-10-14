"""Bounded spoken binary arithmetic. No eval, shell, model or guessed digits."""
import re
from decimal import Decimal,localcontext

def answer(text):
 if not isinstance(text,str)or len(text)>240:return None
 # Only a complete arithmetic question is accepted. Unknown STT words are not removed.
 number=r'(-?\d{1,12}(?:\.\d{1,8})?)'
 pattern=r"\s*(?:(?:hey\s+)?(?:jarvis|lyra|dex)[,.:]?\s+)?(?:(?:what(?:'s| is)|calculate|compute)\s+)?"+number+r'\s*(plus|minus|times|multiplied by|divided by|[+*/])\s*'+number+r'[.!?]*\s*'
 m=re.fullmatch(pattern,text,re.I)
 if not m:return None
 a,op,b=Decimal(m[1]),m[2].lower(),Decimal(m[3])
 with localcontext()as ctx:
  ctx.prec=32
  if op in ('plus','+'):value=a+b
  elif op=='minus':value=a-b
  elif op in ('times','multiplied by','*'):value=a*b
  elif b==0:return 'I cannot divide by zero.'
  else:value=a/b
 display=format(value,'f');display=display.rstrip('0').rstrip('.')if '.'in display else display
 if len(display)>80:return 'That result is too long to read safely. Please use the calculator.'
 return format(a,'f')+' '+op+' '+format(b,'f')+' is '+display+'.'
