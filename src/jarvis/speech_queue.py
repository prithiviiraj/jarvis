"""Bounded generation-scoped speech queue. Backpressure and single installed voice."""
import queue,threading
from .streaming import sentences
class SpeechQueue:
    def __init__(self,speaker,cancel):self.speaker=speaker;self.cancel=cancel;self.queue=queue.Queue(maxsize=3);self.error=None
    def run(self,ticket):
        while not self.cancel.is_set():
            try:part=self.queue.get(timeout=.1)
            except queue.Empty:continue
            if part is None:return
            try:self.speaker.speak(part,generation=ticket)
            except Exception:self.error=RuntimeError('Local voice failed.');self.cancel.set();return
    def put(self,part):
        while not self.cancel.is_set():
            try:self.queue.put(part,timeout=.1);return True
            except queue.Full:continue
        return False
    def play_stream(self,chunks,ticket,on_clause=lambda *a:None):
        thread=threading.Thread(target=self.run,args=(ticket,),daemon=True);thread.start()
        try:
            for part in sentences(chunks):
                if self.cancel.is_set():break
                on_clause(part)
                if not self.put(part):break
        finally:
            self.put(None);thread.join(timeout=3 if self.cancel.is_set() else 120)
            if thread.is_alive():self.cancel.set();self.speaker.stop()
        if self.error:raise self.error
