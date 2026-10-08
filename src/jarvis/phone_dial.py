"""Reviewed dial preparation only. No Android companion, call or speech injection transport."""
import copy,hashlib,json,re,secrets
class PhoneDial:
 def __init__(self):self.pending=None;self.state='off';self.result=None
 def prepare(self,contact,number,words,device):
  if not isinstance(contact,str)or not 1<=len(contact)<=100:raise ValueError('Choose the exact contact')
  if not isinstance(number,str)or not re.fullmatch(r'\+[1-9][0-9]{7,14}',number):raise ValueError('Review one exact international phone number')
  if not isinstance(words,str)or not 1<=len(words)<=2000:raise ValueError('Review exactly what should be said')
  if not isinstance(device,dict)or not device.get('verified_pairing')or not isinstance(device.get('id'),str)or device.get('platform')!='android':raise ValueError('A verified paired Android companion is required')
  # A reported unlimited plan is not a tariff check: international/premium/roaming exceptions remain.
  data={'contact':contact,'number':number,'words':words,'device_id':device['id'],'scope':'Dial only. Speaking these words into a carrier call is unavailable until on-device HFP audio acceptance. No two-way call AI.'}
  self.pending={'payload':data,'sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'review_id':secrets.token_hex(16)};self.state='review';self.result=None;return copy.deepcopy(self.pending)
 def cancel(self):self.pending=None;self.state='cancelled'
 def dispatch(self,reviewed,confirm=False,live_check=None,transport=None):
  if confirm is not True or not self.pending or reviewed!=self.pending:raise ValueError('Review exact recipient, number and words first')
  # No simulated success: unavailable transport is an explicit gate, not fallback to tel: or shell.
  if transport is None:raise ValueError('Android dial transport is not installed; no call started')
  raise ValueError('Carrier call execution is not enabled. Verify current costs, companion identity, permissions and native readback before implementation')
 def snapshot(self):return {'state':self.state,'pending':copy.deepcopy(self.pending),'result':self.result,'scope':'Prepared reviewed dial request only. No call started, no automatic TTS, no call-audio capture.'}
