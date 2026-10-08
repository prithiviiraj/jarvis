"""Frozen Windows credential/callback software acceptance. Google replies are fixtures."""
import hashlib,json,threading,urllib.parse,urllib.request
from .google_tokens import GoogleTokens,GoogleCredentials
from .google_authorization import GoogleAuthorization,IDENTITY
from .google_connection import GoogleConnection
from .google_oauth import SCOPES

def run():
 from pathlib import Path
 import uuid
 email='fixture-'+uuid.uuid4().hex+'@example.invalid';client='fixture.apps.googleusercontent.com';secret='fixture-secret';scope=SCOPES['calendar-freebusy'];store=GoogleCredentials();key=GoogleTokens.key(email);probe=hashlib.sha256(uuid.uuid4().bytes).hexdigest()
 try:
  store.set(probe,'fixture-credential');assert store.status(probe)['present'];assert store.get(probe)=='fixture-credential';store.delete(probe);assert not store.status(probe)['present']
  calls=[]
  def transport(payload):
   calls.append(payload.copy())
   if payload['grant_type']=='authorization_code':return {'access_token':'fixture-access','refresh_token':'fixture-refresh','token_type':'Bearer','scope':' '.join({scope}|IDENTITY)}
   assert payload['client_secret']==secret
   return {'access_token':'fixture-refreshed','token_type':'Bearer','expires_in':3600,'scope':scope}
  tokens=GoogleTokens(store,transport);auth=GoogleAuthorization(tokens,lambda t:{'email':email,'email_verified':True,'sub':'fixture-subject'});urls=[];connection=GoogleConnection(tokens,auth,lambda u:urls.append(u)or True)
  # Never overwrite the product client's target in a fixture. Supply a disposable
  # test store mapping for that fixed key, while account tokens use real WinCred.
  from .google_connection import CLIENT_KEY
  class Scoped:
   def get(self,k):return json.dumps({'client_id':client,'client_secret':secret})if k==CLIENT_KEY else store.get(k)
   def set(self,k,v):
    assert k!=CLIENT_KEY;store.set(k,v)
   def status(self,k):return store.status(k)
   def delete(self,k):assert k!=CLIENT_KEY;store.delete(k)
  tokens.store=Scoped()
  connection.begin(email,['calendar-freebusy'],True)
  import time
  deadline=time.monotonic()+2
  while not urls and time.monotonic()<deadline:time.sleep(.01)
  q=urllib.parse.parse_qs(urllib.parse.urlsplit(urls[0]).query);callback=q['redirect_uri'][0]+'?'+urllib.parse.urlencode({'state':q['state'][0],'code':'fixture-code'})
  assert urllib.parse.urlsplit(callback).hostname=='127.0.0.1'
  with urllib.request.urlopen(callback,timeout=3)as reply:assert reply.status==200 and reply.headers['Cache-Control']=='no-store'
  connection.worker.join(5);assert not connection.busy and not connection.error,connection.snapshot();assert store.status(key)['present'];assert tokens.access(email,scope)=='fixture-refreshed';assert len(calls)==2
  assert 'fixture-secret'not in json.dumps(connection.snapshot())
  # Real frozen review/journal/encoding/readback with entirely controlled Gmail
  # transport. No network mail side effect and no owner's account credential.
  import tempfile,email as mailparser
  from .google_mail import GoogleMail
  tokens.save(email,client,'fixture-refresh',[SCOPES['mail-read'],SCOPES['mail-send']],True,secret)
  tokens.transport=lambda p:{'access_token':'fixture-mail','token_type':'Bearer','expires_in':3600,'scope':SCOPES['mail-read']+' '+SCOPES['mail-send']}
  fixture_sent={};fixture_posts=[]
  def mail_transport(method,url,payload):
   if url.endswith('/profile'):return {'emailAddress':email}
   if 'messages?'in url:return {'messages':[]}
   if method=='POST':
    fixture_posts.append(payload)
    msg=mailparser.message_from_bytes(__import__('base64').urlsafe_b64decode(payload['raw']+'='*(-len(payload['raw'])%4)),policy=mailparser.policy.default)
    fixture_sent.update({'id':'fixture-sent','labelIds':['SENT'],'payload':{'mimeType':'text/plain','headers':[{'name':k,'value':str(msg[k])}for k in ('To','Subject','Message-ID')],'body':{'data':__import__('base64').urlsafe_b64encode(msg.get_content().encode()).decode()}}});return {'id':'fixture-sent'}
   return fixture_sent
  with tempfile.TemporaryDirectory()as folder:
   ledger=Path(folder)/'mail.json';mail=GoogleMail(connection,ledger,mail_transport);review=mail.prepare(['friend@example.invalid'],'Fixture review','Exact fixture words');mail.submit(review,True);mail.worker.join(5);assert mail.snapshot()['state']=='completed',mail.snapshot();assert len(fixture_posts)==1;assert GoogleMail(connection,ledger,mail_transport).snapshot()['state']=='completed'
  from .google_calendar import GoogleCalendar
  tokens.save(email,client,'fixture-refresh',[SCOPES['calendar-write-owned'],SCOPES['calendar-freebusy']],True,secret)
  tokens.transport=lambda p:{'access_token':'fixture-calendar','token_type':'Bearer','expires_in':3600,'scope':SCOPES['calendar-write-owned']+' '+SCOPES['calendar-freebusy']}
  events={};calendar_posts=[]
  def calendar_transport(method,url,payload):
   if url.endswith('/freeBusy'):return {'calendars':{'primary':{'busy':[]}}}
   if method=='POST':calendar_posts.append(payload);events[payload['id']]=dict(payload,status='confirmed');return events[payload['id']]
   return events[url.rsplit('/',1)[-1]]
  with tempfile.TemporaryDirectory()as folder:
   ledger=Path(folder)/'calendar.json';calendar=GoogleCalendar(connection,ledger,calendar_transport,lambda t:{'email':email,'email_verified':True});review=calendar.prepare('Fixture solo bookkeeping','2026-10-08T17:00:00+05:30','2026-10-08T17:30:00+05:30');calendar.submit(review,True);calendar.worker.join(5);assert calendar.snapshot()['state']=='completed',calendar.snapshot();assert len(calendar_posts)==1 and calendar_posts[0]['attendees']==[] and not calendar_posts[0]['reminders']['useDefault'];assert GoogleCalendar(connection,ledger,calendar_transport).snapshot()['state']=='completed'
  from .google_queries import GoogleQueries
  tokens.save(email,client,'fixture-refresh',[SCOPES['drive-metadata-read'],SCOPES['sheets-read']],True,secret)
  tokens.transport=lambda p:{'access_token':'fixture-workspace','token_type':'Bearer','expires_in':3600,'scope':SCOPES['drive-metadata-read']+' '+SCOPES['sheets-read']}
  workspace_calls=[]
  def workspace_transport(method,url,payload):
   workspace_calls.append((method,url,payload))
   assert method=='GET'and payload is None
   if '/drive/v3/files?'in url:return {'files':[{'id':'fixture_sheet','name':'Controlled sheet','mimeType':'application/vnd.google-apps.spreadsheet'}],'nextPageToken':'partial'}
   assert '/fixture_sheet/values/Sheet1%21A1%3AB2?'in url
   return {'range':'Sheet1!A1:B2','majorDimension':'ROWS','values':[['External fixture',2],[3,4]]}
  reads=GoogleQueries(connection,workspace_transport);reads.start('drive-list',{'query':'fixture'},True);reads.worker.join(5);assert not reads.error and not reads.result['complete'];reads.start('sheets-values',{'file_id':'fixture_sheet','range':'Sheet1!A1:B2'},True);reads.worker.join(5);assert not reads.error and reads.result['values'][1][1]==4;assert len(workspace_calls)==2;reads.stop();assert reads.result is None
  from .google_sheets_write import SheetsWrite
  tokens.save(email,client,'fixture-refresh',[SCOPES['sheets-write']],True,secret)
  tokens.transport=lambda p:{'access_token':'fixture-sheets','token_type':'Bearer','expires_in':3600,'scope':SCOPES['sheets-write']}
  sheet_calls=[];sheet_values=[['prior','old']]
  def sheet_transport(method,url,payload):
   nonlocal sheet_values
   sheet_calls.append((method,url,payload))
   if '/values/'not in url:return {'spreadsheetId':'fixture_sheet','properties':{'title':'Controlled sheet'},'sheets':[{'properties':{'sheetId':3,'title':'Tab','gridProperties':{'rowCount':20,'columnCount':10}}}]}
   if method=='PUT':sheet_values=payload['values'];return {'spreadsheetId':'fixture_sheet','updatedCells':2}
   return {'range':'Tab!A1:B1','values':sheet_values}
  with tempfile.TemporaryDirectory()as folder:
   sheets=SheetsWrite(connection,Path(folder)/'sheets.json',sheet_transport,lambda t:{'email':email,'email_verified':True});sheets.prepare('fixture_sheet','Tab','A1:B1',[['=1+2','']],True);sheets.worker.join(5);assert not sheets.error,sheets.snapshot();review=sheets.snapshot()['plan'];assert review['payload']['before']==[['prior','old']];assert not any(m=='PUT'for m,u,p in sheet_calls);sheets.submit(review,True);sheets.worker.join(5);assert sheets.snapshot()['state']=='completed',sheets.snapshot();assert sheet_values==[['=1+2','']];assert len([x for x in sheet_calls if x[0]=='PUT'])==1;assert SheetsWrite(connection,sheets.path).snapshot()['state']=='completed'
  from .project_connectors import ProjectConnectors,ProjectCredentials
  projects_store=ProjectCredentials();project_identity='fixture-'+uuid.uuid4().hex[:16];project_key=ProjectConnectors.key('github',project_identity)
  try:
   project_calls=[]
   def project_transport(service,method,url,payload,token):
    project_calls.append(url);assert service=='github'and method=='GET'and payload is None
    if url.endswith('/user'):return {'login':project_identity}
    return [{'number':1,'title':'Controlled issue','body':'Untrusted fixture only'}]
   projects=ProjectConnectors(projects_store,project_transport);projects.connect('github',project_identity,'fixture-project-token',True);projects.worker.join(5);assert not projects.error
   projects.read('github',{'kind':'issues','owner':'fixture','repo':'fixture'},True);projects.worker.join(5);assert not projects.error and len(projects.result['issues'])==1
   from .github_issue import GitHubIssue
   issue_calls=[];created={}
   def issue_transport(method,url,payload,token):
    assert token=='fixture-project-token';issue_calls.append((method,url,payload))
    if not '/issues' in url:return {'full_name':'fixture/fixture','has_issues':True,'archived':False}
    if method=='POST':created.update(payload,number=7,html_url='https://github.com/fixture/fixture/issues/7',user={'login':project_identity})
    return dict(created)
   with tempfile.TemporaryDirectory()as folder:
    issue=GitHubIssue(projects,Path(folder)/'issue.json',issue_transport)
    try:issue.prepare('fixture','fixture','Controlled title','Controlled exact fixture body',False)
    except ValueError:pass
    else:raise AssertionError('Issue read permission became write')
    review=issue.prepare('fixture','fixture','Controlled title','Controlled exact fixture body',True);assert not issue_calls
    issue.submit(review,True);issue.worker.join(5);assert issue.snapshot()['state']=='completed',issue.snapshot()
    assert [x[0]for x in issue_calls]==['GET','POST','GET']
    assert GitHubIssue(projects,issue.path,issue_transport).snapshot()['state']=='completed'
    try:issue.prepare('fixture','fixture','Controlled title','Controlled exact fixture body',True)
    except ValueError:pass
    else:raise AssertionError('Completed issue duplicated')
   restarted=ProjectConnectors(projects_store,project_transport);assert not restarted.accounts;restarted.connect('github',project_identity,'',True);restarted.worker.join(5);assert not restarted.error;restarted.disconnect('github',True);assert not projects_store.get(project_key)
  finally:projects_store.delete(project_key)
  from .focus_session import FocusSession
  tick=[0];focus=FocusSession(lambda:tick[0]);focus_review=focus.prepare('Isolated focus fixture',5);assert focus.state=='review';focus.start(focus_review,True);tick[0]=100;focus.pause();tick[0]=500;assert focus.snapshot()['remaining_seconds']==200;focus.resume(True);tick[0]=700;assert focus.snapshot()['state']=='check-in';focus.finish(True);assert focus.history[0]['done'];focus.stop();assert focus.state=='off'
  connection.disconnect(True);assert not store.status(key)['present'];connection.stop()
  from .reflex_session import ReflexSession
  reflex=ReflexSession();reflex.set_enabled(True,True);reflex_row=reflex.preview('Jarvis call my brother');assert reflex_row['confidence']is None and 'review'in reflex_row['action_stakes'];reflex.stop();assert reflex.result is None
  from .brain_settings import BrainSettings
  from .brain_switch import BrainSwitch
  brains=BrainSettings();brains.configure([{'id':'slot5','provider':'local','model':'old','enabled':True}],{'JARVIS':'slot5'});switch=BrainSwitch(brains,lambda:[{'id':'fixture-new'}],lambda m,c:{'text':'ready','model':m});brain_review=switch.prepare('JARVIS','slot5','fixture-new');switch.apply(brain_review,True);switch.worker.join(5);assert brains.rows['slot5'].model=='fixture-new' and 'JARVIS'in switch.verified;assert len(brains.candidates('JARVIS'))==1
  from .source_answer import SourceAnswer
  from .obsidian import Vault
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();(root/'.obsidian').mkdir();(root/'source.md').write_text('Controlled quote');note={'name':'source.md','vault_folder':str(root),'text':'Controlled quote','sha256':hashlib.sha256(b'Controlled quote').hexdigest(),'truncated':False};answer=SourceAnswer(threading.Lock(),lambda:[{'id':'fixture-local'}],lambda m,q,n,c:{'text':'Controlled draft','model':m});source_review=answer.prepare(root,note,'Question','fixture-local');answer.start(root,source_review,True);answer.worker.join(5);assert answer.result['source_sha256']==note['sha256'];answer.stop();assert answer.result is None
  result={'host':'actual frozen Windows core','windows_credential_write_read_delete':True,'real_ipv4_loopback_callback':True,'PKCE_state_and_verified_identity_fixture':True,'exchange_refresh_local_disconnect_fixture':True,'live_google':False,'real_registered_client':False,'reviewed_Gmail_send_readback_and_restart_fixture':True,'mail_sent':False,'reviewed_solo_calendar_readback_restart_fixture':True,'calendar_changed':False,'reviewed_Drive_metadata_Sheets_values_fixture':True,'workspace_write':False,'reviewed_RAW_Sheets_prior_new_readback_restart_fixture':True,'reviewed_project_read_secure_resume_fixture':True,'live_projects':False,'reviewed_GitHub_issue_write_gate_readback_restart_fixture':True,'live_issue_created':False,'local_focus_timer_review_pause_checkin_fixture':True,'local_reflex_five_questions_no_effect_fixture':True,'exact_local_brain_switch_no_cloud_fixture':True,'reviewed_single_source_local_answer_fixture':True}
  Path('ui-evidence').mkdir(exist_ok=True);Path('ui-evidence/frozen-google-acceptance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 finally:store.delete(key);store.delete(probe)
