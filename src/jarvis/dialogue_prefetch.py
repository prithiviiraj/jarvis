"""At most one real next turn, bounded deltas, cancellation and no audio output."""
import queue,threading
class Prefetch:
 def __init__(self,router,messages,cancel,local_only=False):
  self.queue=queue.Queue(maxsize=3);self.cancel=cancel
  def put(item):
   while not cancel.is_set():
    try:self.queue.put(item,timeout=.05);return
    except queue.Full:pass
  def run():
   try:
    for delta in router.stream(messages,cancel=cancel,**({'local_only':True}if local_only else{})):
     if cancel.is_set():return
     put(('delta',delta))
   except Exception as e:put(('error',e))
   finally:put(('done',None))
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start()
 def stream(self):
  while not self.cancel.is_set():
   try:kind,item=self.queue.get(timeout=.05)
   except queue.Empty:continue
   if kind=='done':return
   if kind=='error':raise item
   yield item
