"""Optional session-only five-question evidence preview. Never dispatches an action."""
import copy
from .decision_layer import assess
class ReflexSession:
 def __init__(self):self.enabled=False;self.result=None
 def set_enabled(self,enabled,consent=False):
  if type(enabled)is not bool:raise ValueError('Choose Reflex on or off')
  if enabled and consent is not True:raise ValueError('Review local Reflex evidence scope first')
  self.enabled=enabled;self.result=None
 def preview(self,text,source='typed',endpoint=None,retrieval=None):
  if not self.enabled:raise ValueError('Reflex is off')
  if not isinstance(text,str)or not text.strip()or len(text)>2000:raise ValueError('Enter a request up to2000characters')
  if source not in ('typed','speech'):raise ValueError('Unknown request source')
  self.result=assess(text,source,endpoint,retrieval);return copy.deepcopy(self.result)
 def stop(self):self.enabled=False;self.result=None
 def snapshot(self):return {'enabled':self.enabled,'result':copy.deepcopy(self.result),'scope':'Local deterministic five-question preview, not a trained fast model or probabilities. No speech endpoint invented. No model, sensors, retrieval, tools or actions start; source text is not executed.'}
