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
class ReportSpeechFilter:
    """Sentence buffering prevents split report/thought labels escaping into TTS."""
    def __init__(self):self.buffer='';self.report=False
    def feed(self,text,final=False):
        self.buffer+=text;out=[]
        while self.buffer:
            if self.report or re.match(r'^\s*(?:report\s+to\s+master|report\s+for\s+master|internal\s+(?:report|thought)|thought|status\s+report)\s*[:\-]',self.buffer,re.I):
                self.report=True
                newline=self.buffer.find('\n')
                if newline<0:
                    self.buffer=''
                    if final:self.report=False
                    break
                self.buffer=self.buffer[newline+1:];self.report=False;out.append('\n');continue
            boundary=re.search(r'[.!?](?=\s|$)|\n',self.buffer)
            if boundary is None and not final:break
            end=boundary.end() if boundary else len(self.buffer)
            sentence=self.buffer[:end];self.buffer=self.buffer[end:]
            if not re.match(r'^\s*(?:report\s+to\s+master|report\s+for\s+master|internal\s+(?:report|thought)|thought|status\s+report)\s*[:\-]',sentence,re.I):out.append(sentence)
        return ''.join(out)
    def finish(self):return self.feed('',True)
def spoken_text(text):
    f=SpokenTextFilter();r=ReportSpeechFilter();return r.feed(f.feed(text)+f.finish(),True)
def spoken_chunks(chunks):
    f=SpokenTextFilter();r=ReportSpeechFilter()
    for part in chunks:
        text=r.feed(f.feed(part))
        if text:yield text
    tail=r.feed(f.finish(),True)
    if tail:yield tail
