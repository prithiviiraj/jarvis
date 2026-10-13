"""Exact displayed-review binding. UI acknowledgement is not approval."""
import copy,time,uuid,re
class VoiceReview:
 def __init__(self,clock=time.monotonic):self.clock=clock;self.binding=None
 def clear(self):self.binding=None
 def bind(self,kind,payload,current,extra_pending=False):
  if extra_pending or kind not in ('browser','app','focus','brain','invoice','design','github','notion','drive','sheets','mail','calendar','telegram','source','model-download','model-start','phone-pair','news','local-calendar')or payload!=current or not isinstance(payload,dict):raise ValueError('Show one current exact review before voice approval')
  if kind=='telegram'and payload.get('payload',{}).get('format')!='text':raise ValueError('Telegram voice output requires listening to the exact audio review; spoken approval is unavailable')
  if self.binding and self.binding['kind']==kind and self.binding['payload']==payload:return self.snapshot()
  self.binding={'id':uuid.uuid4().hex,'kind':kind,'payload':copy.deepcopy(payload),'until':self.clock()+60};return self.snapshot()
 def snapshot(self):
  if not self.binding or self.clock()>self.binding['until']:return None
  return {'id':self.binding['id'],'kind':self.binding['kind'],'expires_in_s':max(0,round(self.binding['until']-self.clock(),1))}
 def choice(self,text,current,extra_pending=False):
  if not isinstance(text,str):return None
  m=re.fullmatch(r'\s*(?:(?:hey\s+)?(?:jarvis|lyra|dex)[,.:]?\s+)?(confirm|cancel)(?:\s+(browser|app|focus|brain|invoice|design|github|notion|drive|sheets|mail|calendar|telegram|source|model-download|model-start|phone-pair|news|local-calendar)(?:\s+action)?)?[.!?]*\s*',text,re.I)
  if not m:return None
  b=self.binding
  if not b or self.clock()>b['until']or extra_pending or current!=b['payload']or m.group(2)and m.group(2).lower()!=b['kind']:
   self.clear();raise ValueError('Voice approval was not applied. Show one current exact review and say confirm or cancel again.')
  self.clear();return {'choice':m.group(1).lower(),'kind':b['kind'],'payload':copy.deepcopy(b['payload']),'id':b['id']}
