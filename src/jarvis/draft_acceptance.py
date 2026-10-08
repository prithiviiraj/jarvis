"""Explicit frozen fixture for local design and phone-text draft contracts. No hardware/model/account."""
def run():
 import json,pathlib,tempfile,threading,hashlib
 from .design_draft import DesignDraft
 from .phone_controller import PhoneController
 class TextMemory:
  def __init__(self):self.history_lock=threading.RLock();self.history=[];self.generation=0
  def reset_session(self):
   with self.history_lock:self.generation+=1;self.history=[]
  def close(self):self.reset_session()
 p=TextMemory();c=PhoneController(p)
 with tempfile.TemporaryDirectory()as folder:
  try:
   d=DesignDraft(pathlib.Path(folder)/'posters');facts={'title':'Synthetic design fixture','body':'Exact synthetic wording only. No Canva account accessed.','footer':'Not published','theme':'paper'};r=d.prepare(facts,True);saved=d.save(r,True);assert pathlib.Path(saved['path']).read_text(encoding='utf-8')==r['svg']
   r=d.prepare(facts,True);d.cancel()
   try:d.save(r,True)
   except ValueError:pass
   else:raise AssertionError('Stopped design accepted')
   request=c.request_pair(c.enable(True),'Synthetic unverified label');token=c.approve(request,True);p.history=[{'role':'user','content':'Synthetic private note, not an action request.'},{'role':'assistant','content':'Synthetic unverified reply.'}];review=c.prepare_handoff(True);assert review['turns']==1;assert c.apply_handoff(review,True)==review['text'];assert not c.snapshot()['paired']and p.history==[]
   try:c.take_reply(token)
   except ValueError:pass
   else:raise AssertionError('Revoked token accepted')
   report={'frozen_executable':True,'synthetic_text_only':True,'editable_SVG_exact_review_write_readback_cancel':True,'SVG_sha256':hashlib.sha256(pathlib.Path(saved['path']).read_bytes()).hexdigest(),'recent_phone_text_exact_review_revoke_clear':True,'no_network_listener_account_open_send_speech':True,'unrun':['physical phone','real speech and model','native UI phone text continuation','Canva account integration','carrier calling']}
   out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True);(out/'frozen-local-draft-contracts.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
  finally:c.close()
