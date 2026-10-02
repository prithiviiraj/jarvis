"""Synthetic Windows speech integration, no owner audio."""
from jarvis.speech import SapiSpeaker
import time,threading
s=SapiSpeaker();s.speak('JARVIS local voice check.')
errors=[]
def long():
 try:s.speak('This is a cancellable local speech test. '*30)
 except RuntimeError:pass # terminating subprocess intentionally interrupts it
thread=threading.Thread(target=long);thread.start();time.sleep(.5);s.stop();thread.join(timeout=5)
assert not thread.is_alive(),'Speech worker did not stop'
assert s.process is None,'Speech process retained'
print('Installed Windows SAPI synthesis and cancellation passed. No cloud voice or mic.')
