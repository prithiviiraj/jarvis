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
   # Exercise real default callback wiring while mocking only the HTTP boundary.
   # This catches missing router keywords hidden by whole-callback substitutes.
   from unittest.mock import patch
   with patch('jarvis.router.HttpTransport.complete',return_value='Synthetic transport-only local draft')as http:
    default_answer=SourceAnswer(threading.Lock());default_row=default_answer._generate('synthetic-local','Question',note,threading.Event());assert default_row['cloud']is False and default_row['model']=='synthetic-local'
    default_switch=BrainSwitch(settings);default_row=default_switch._probe('synthetic-local',threading.Event());assert default_row['cloud']is False and default_row['model']=='synthetic-local'and http.call_count==2
   # Real frozen Bridge poll boundary, only browser snapshot/speech transport substituted.
   from .ui_bridge import Bridge
   from unittest.mock import Mock
   b=Bridge();b.browser=Mock();b.news_speech.stop=Mock()
   try:
    proposal=b.news.preview('https://example.com/news');b.news.confirm(proposal,True);b.news.observe({'state':'ready','requested_url':proposal['value'],'url':proposal['value']})
    text='Synthetic captured news quote';b.news.accept_text({'url':proposal['value'],'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    b.neural.offer('news','JARVIS','Synthetic old page',text);b.neural.picture='data:image/jpeg;base64,eA==';b.neural_question={'row':dict(b.neural.row)}
    from .browser_control import BrowserSession
    from types import SimpleNamespace
    session=BrowserSession.__new__(BrowserSession);session.lock=threading.RLock();session.state={'state':'ready','url':proposal['value'],'news_text':b.news.text_preview,'links':[{'url':'old'}],'page_revision':1}
    b.news.observed_revision=1
    callbacks={};page=SimpleNamespace(url=proposal['value'],main_frame=object(),on=lambda k,f:callbacks.update({k:f}));session.observe_page(page);callbacks['framenavigated'](page.main_frame)
    assert session.snapshot()['page_revision']==2 and 'news_text'not in session.snapshot() and not session.snapshot()['links']
    b.browser.snapshot.side_effect=session.snapshot
    b.execute({'command':'status'})
    assert not b.news.observed_url and b.news.text_preview is None and b.neural.row is None and b.neural.picture is None and b.neural_question is None
    b.news_speech.stop.assert_called();b.browser.submit.assert_not_called()
   finally:b.close()
   from .browser_chain import parse as chain_parse,execute as chain_execute
   from .browser_control import BrowserControl
   page=Mock();page.url='https://example.com/';page.title.return_value='Synthetic chain';steps=[]
   def command(self,kind,value='',confirmed=False):
    steps.append(kind);page.url=value if kind=='open'else'https://example.com/search';return {'url':page.url,'title':'Synthetic chain'}
   with patch('jarvis.browser_control.BrowserControl.execute',command):
    chain=chain_execute(page,chain_parse('open browser then search Iron Man')['value'],threading.Event())
   assert steps==['open-window','search']and len(chain['chain_steps'])==2
   from .game_companion import scene_reply,LocalGameModel,VisionReplyUnavailable
   scene={'observed':'Synthetic visible scene','comment':'Fixture words only','confidence':'high'}
   raw=lambda text:json.dumps({'choices':[{'message':{'content':text}}]}).encode()
   assert scene_reply(raw('```json\n'+json.dumps(scene)+'\n```'))==scene
   import io
   class Response(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
   transport=Mock();transport.open.side_effect=[Response(raw('')),Response(raw(json.dumps(scene)))];model=LocalGameModel('synthetic',transport);model.verify=Mock();assert model.analyze(b'synthetic jpeg')==scene and transport.open.call_count==2
   from .live_screen import LiveScreen
   import time
   listener=Mock();model.analyze=Mock(side_effect=[VisionReplyUnavailable('Synthetic invalid response'),scene]);live=LiveScreen(listener,source=lambda t:b'synthetic jpeg',interval=.01);live.enable({'id':1,'title':'Synthetic'},{'id':1,'title':'Synthetic'},model,True)
   limit=time.monotonic()+2
   while not live.analysis_error and time.monotonic()<limit:time.sleep(.005)
   assert live.enabled and live.analysis_error and not listener.called
   live.retry_analysis();limit=time.monotonic()+2
   while not listener.called and time.monotonic()<limit:time.sleep(.005)
   assert listener.called and model.analyze.call_count==2;live.stop();assert live.preview is None and not live.analysis_error
   report={'frozen_executable':bool(getattr(__import__('sys'),'frozen',False)),'synthetic_text_only':True,'editable_SVG_exact_review_write_readback_cancel':True,'SVG_sha256':hashlib.sha256(pathlib.Path(saved['path']).read_bytes()).hexdigest(),'recent_phone_text_exact_review_revoke_clear':True,'synthetic_source_answer_attribution_cloud_reject':True,'synthetic_brain_switch_exact_route_cloud_reject':True,'real_default_source_switch_callback_transport_mock_contract':True,'observed_news_page_change_revokes_picture_quote_question_speech':True,'same_url_document_event_revokes_frozen_news':True,'bounded_frozen_browser_chain_dispatch':True,'frozen_scene_format_retry_pause_recovery_stop':True,'no_network_listener_account_open_send_speech':True,'unrun':['physical phone','real speech and model','native UI phone text continuation','Canva account integration','carrier calling']}
   out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True);(out/'frozen-local-draft-contracts.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
  finally:c.close()
