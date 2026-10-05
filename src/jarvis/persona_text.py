"""Speaker identity comes from routing, never from model-generated labels."""
import re
from .personas import ROLES
_TAG=re.compile(r'^\s*\[('+'|'.join(ROLES)+r')\]\s*[:.\-]?\s*',re.I)
def strip_speaker_tag(text):
    """Remove leading model-invented [PERSONA] labels; keep all other bracket text."""
    if not isinstance(text,str):return text
    previous=None
    while previous!=text:
        previous=text;text=_TAG.sub('',text,count=1)
    return text
class SpokenTextFilter:
    """Streaming-safe removal of [bracketed asides] from speech only. Display keeps them."""
    def __init__(self):self.buffer='';self.hidden=False;self.total=0
    def feed(self,text,final=False):
        if not isinstance(text,str):raise ValueError('Text required')
        self.total+=len(text)
        if self.total>1000000:raise ValueError('Response too large')
        self.buffer+=text;out=[]
        while self.buffer:
            if self.hidden:
                end=self.buffer.find(']')
                if end<0:
                    # An unclosed bracket at the end is an unfinished aside; never speak it.
                    if final:self.buffer=''
                    break
                self.buffer=self.buffer[end+1:];self.hidden=False;continue
            start=self.buffer.find('[')
            if start<0:out.append(self.buffer);self.buffer='';break
            out.append(self.buffer[:start]);self.buffer=self.buffer[start+1:];self.hidden=True
        return ''.join(out)
    def finish(self):return self.feed('',True)
def spoken_text(text):
    f=SpokenTextFilter();return f.feed(text)+f.finish()
def spoken_chunks(chunks):
    f=SpokenTextFilter()
    for part in chunks:
        text=f.feed(part)
        if text:yield text
    tail=f.finish()
    if tail:yield tail
