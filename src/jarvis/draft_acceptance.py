"""Explicit frozen fixture for local design and phone-text draft contracts. No hardware/model/account."""
def run():
 import json,pathlib,tempfile,threading,hashlib
 from .design_draft import DesignDraft
 from .phone_controller import PhoneController
 from .source_answer import SourceAnswer
 from .brain_switch import BrainSwitch
 from .brain_settings import BrainSettings
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
   vault=pathlib.Path(folder)/'vault';vault.mkdir();(vault/'.obsidian').mkdir();source=vault/'fixture.md';source.write_text('Exact synthetic evidence',encoding='utf-8');note={'name':'fixture.md','vault_folder':str(vault.resolve()),'text':'Exact synthetic evidence','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'truncated':False}
   answer=SourceAnswer(threading.Lock(),lambda:[{'id':'synthetic-local'}],lambda m,*a:{'text':'Unverified synthetic draft','model':m})
   r=answer.prepare(vault,note,'What does the fixture say?','synthetic-local');answer.start(vault,r,True);answer.worker.join(3);assert not answer.worker.is_alive()and answer.result['source_sha256']==note['sha256']
   answer.generate=lambda m,*a:{'text':'Synthetic cloud-labelled reply','model':m,'cloud':True};r=answer.prepare(vault,note,'What does the fixture say?','synthetic-local');answer.start(vault,r,True);answer.worker.join(3);assert not answer.worker.is_alive()and answer.result is None and answer.error;answer.stop()
   settings=BrainSettings();settings.configure([{'id':'slot5','provider':'local','model':'old','enabled':True}],{'JARVIS':'slot5'});switch=BrainSwitch(settings,lambda:[{'id':'synthetic-local'}],lambda m,c:{'text':'ready','model':m,'cloud':True})
   r=switch.prepare('JARVIS','slot5','synthetic-local');switch.apply(r,True);switch.worker.join(3);assert not switch.worker.is_alive()and settings.rows['slot5'].model=='old'and not switch.verified and switch.error
   switch.probe=lambda m,c:{'text':'ready','model':m};r=switch.prepare('JARVIS','slot5','synthetic-local');switch.apply(r,True);switch.worker.join(3);assert not switch.worker.is_alive()and settings.rows['slot5'].model=='synthetic-local'and switch.snapshot()['verified'];switch.stop()
   report={'frozen_executable':bool(getattr(__import__('sys'),'frozen',False)),'synthetic_text_only':True,'editable_SVG_exact_review_write_readback_cancel':True,'SVG_sha256':hashlib.sha256(pathlib.Path(saved['path']).read_bytes()).hexdigest(),'recent_phone_text_exact_review_revoke_clear':True,'synthetic_source_answer_attribution_cloud_reject':True,'synthetic_brain_switch_exact_route_cloud_reject':True,'no_network_listener_account_open_send_speech':True,'unrun':['physical phone','real speech and model','native UI phone text continuation','Canva account integration','carrier calling']}
   out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True);(out/'frozen-local-draft-contracts.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
  finally:c.close()
