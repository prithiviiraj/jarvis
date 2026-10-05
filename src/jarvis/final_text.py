"""Incremental tagged-thinking suppression. Unclosed thinking is never output."""
class FinalTextFilter:
 def __init__(self):self.buffer='';self.hidden=False;self.suppressed=False;self.total=0;self.start_buffer='';self.start_decided=False;self.scaffold=False
 def feed(self,text,final=False):
  self.total+=len(text)
  if self.total>1000000:raise ValueError('Response too large')
  if self.scaffold:return ''
  if not self.start_decided:
   self.start_buffer+=text
   value=self.start_buffer.lstrip().lower()
   prefixes=("here's a thinking process:","here is a thinking process:","here's my thinking process:","thinking process:")
   if any(value.startswith(p)for p in prefixes):
    self.scaffold=True;self.suppressed=True;self.start_buffer='';return ''
   if not final and (not value or any(p.startswith(value)for p in prefixes)):return ''
   text=self.start_buffer;self.start_buffer='';self.start_decided=True
  self.buffer+=text;out=[]
  markers=('<think>','</think>','<analysis>','</analysis>')
  while self.buffer:
   lower=self.buffer.lower();hits=[(lower.find(m),m)for m in markers if m in lower]
   if hits:
    pos,marker=min(hits);prefix=self.buffer[:pos]
    if not self.hidden:out.append(prefix)
    self.hidden=marker in ('<think>','<analysis>');self.suppressed=True;self.buffer=self.buffer[pos+len(marker):];continue
   # Retain any possible marker prefix across network chunk boundaries.
   keep=max((n for n in range(1,min(len(self.buffer),11)+1)if any(m.startswith(lower[-n:])for m in markers)),default=0)
   if final:keep=0
   chunk=self.buffer[:-keep]if keep else self.buffer
   if not self.hidden:out.append(chunk)
   self.buffer=self.buffer[-keep:]if keep else''
   break
  return ''.join(out)
 def finish(self):return self.feed('',True)
def final_text(text):
 f=FinalTextFilter();return f.feed(text)+f.finish()
