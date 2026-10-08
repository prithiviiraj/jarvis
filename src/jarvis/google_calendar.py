"""Exact reviewed solo primary-calendar events. No invites, recurrence or deletion."""
import json,ssl,threading,urllib.parse,urllib.request
from .connector_workflows import address
from .connector_journal import ConnectorJournal
from .google_oauth import SCOPES
from .google_read_connector import GoogleReadConnector,NoRedirect
from .google_authorization import GoogleAuthorization

def plan(account,title,start,end,location='',notes=''):
 address(account);GoogleReadConnector.interval(start,end)
 if not isinstance(title,str)or not title.strip()or len(title)>300:raise ValueError('Review event title')
 if not isinstance(location,str)or len(location)>1000 or not isinstance(notes,str)or len(notes)>10000:raise ValueError('Review bounded location and notes')
 return {'kind':'calendar','account':account,'calendar_id':'primary','title':title,'start':start,'end':end,'location':location,'notes':notes,'attendees':[],'send_updates':'none','visibility':'private','reminders':False,'recurrence':[],'conference':None,'scope':'Solo bookkeeping on this account primary calendar. No invitations, notification emails, reminders or video link.'}
class GoogleCalendar:
 def __init__(self,connection,path,transport=None,identity=None):self.connection=connection;self.path=path;self.transport=transport;self.identity=identity;self.ledger=None;self.busy=False;self.error='';self.worker=None;self.generation=0
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'calendar')
  return self.ledger
 def prepare(self,title,start,end,location='',notes=''):
  if self.busy or self.connection.busy or not self.connection.account:raise ValueError('Choose connected account with no pending action')
  self.error='';return self.journal().prepare(plan(self.connection.account,title,start,end,location,notes))
 def request(self,method,event_id=None,payload=None,account=None):
  if method not in ('GET','POST'):raise ValueError('Unsupported calendar method')
  base='https://www.googleapis.com/calendar/v3/calendars/primary/events'
  if method=='POST':url=base+'?sendUpdates=none'
  elif event_id:
   import re
   if not re.fullmatch('[a-v0-9]{5,1024}',event_id):raise ValueError('Invalid event ID')
   url=base+'/'+event_id
  else:raise ValueError('Event identity required')
  if not account or self.connection.account!=account:raise ValueError('Calendar account changed')
  token=self.connection.tokens.access(account,SCOPES['calendar-write-owned'])
  if self.transport:return self.transport(method,url,payload)
  import certifi
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  req=urllib.request.Request(url,method=method,data=json.dumps(payload).encode()if payload else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json'})
  with opener.open(req,timeout=15)as r:raw=r.read(2_000_001)
  if len(raw)>2_000_000:raise ValueError('Calendar result too large')
  row=json.loads(raw)
  if not isinstance(row,dict):raise ValueError('Calendar result invalid')
  return row
 def verify_account(self,expected):
  if self.connection.account!=expected or self.connection.busy:raise ValueError('Google account changed')
  token=self.connection.tokens.access(expected,SCOPES['calendar-write-owned'])
  who=self.identity(token)if self.identity else GoogleAuthorization().identity(token)
  if not isinstance(who,dict)or who.get('email_verified')is not True or str(who.get('email','')).casefold()!=expected.casefold():raise ValueError('Live Google identity mismatch')
 @staticmethod
 def same(row,payload,event_id):
  from datetime import datetime
  try:times=all(datetime.fromisoformat(row[key]['dateTime'].replace('Z','+00:00'))==datetime.fromisoformat(payload[key])for key in ('start','end'))
  except Exception:times=False
  return row.get('id')==event_id and row.get('status')!='cancelled'and row.get('summary')==payload['title']and row.get('description','')==payload['notes']and row.get('location','')==payload['location']and times and not row.get('attendees')and row.get('visibility')=='private'and row.get('reminders',{}).get('useDefault')is False and not row.get('reminders',{}).get('overrides')and not row.get('recurrence')and not row.get('conferenceData')
 def submit(self,reviewed,confirm=False):
  ledger=self.journal()
  if self.busy or confirm is not True or ledger.job.state!='review'or reviewed!=ledger.job.plan:raise ValueError('Review exact calendar account, times and no-invite event again')
  self.busy=True;self.error='';self.generation+=1;ticket=self.generation;connection_ticket=self.connection.generation;event_id='jarvis'+reviewed['review_id']
  def validate(payload):
   if self.generation!=ticket or self.connection.generation!=connection_ticket:raise ValueError('Calendar review stopped')
   if plan(payload['account'],payload['title'],payload['start'],payload['end'],payload['location'],payload['notes'])!=payload:raise ValueError('Calendar review changed')
   self.verify_account(payload['account'])
   reader=GoogleReadConnector(lambda:self.connection.tokens.access(payload['account'],SCOPES['calendar-freebusy']),payload['account'],self.transport)
   availability=reader.freebusy(['primary'],payload['start'],payload['end'],True)
   if availability['calendars']['primary']:raise ValueError('Primary calendar has a conflict; choose another time')
   return self.generation==ticket and self.connection.generation==connection_ticket
  def transport(payload):
   if self.generation!=ticket or self.connection.generation!=connection_ticket or self.connection.account!=payload['account']:raise ValueError('Calendar account changed')
   body={'id':event_id,'summary':payload['title'],'start':{'dateTime':payload['start']},'end':{'dateTime':payload['end']},'location':payload['location'],'description':payload['notes'],'visibility':'private','reminders':{'useDefault':False},'attendees':[]}
   row=self.request('POST',payload=body,account=payload['account'])
   if row.get('id')!=event_id:raise ValueError('Calendar server identity changed')
   if self.connection.account!=payload['account']:raise ValueError('Calendar account changed')
   stored=self.request('GET',event_id,account=payload['account'])
   if not self.same(stored,payload,event_id):raise ValueError('Exact calendar readback mismatch')
   return {'verified':True,'external_id':event_id,'url':stored.get('htmlLink'),'scope':'Stored solo event readback verified. No invitations or reminders requested.'}
  def work():
   try:ledger.submit(reviewed,True,validate,transport)
   except Exception:self.error='Calendar action blocked or outcome uncertain. Inspect ledger before retry.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='calendar-reviewed-event',daemon=True);self.worker.start()
 def stop(self):
  self.generation+=1
  if self.ledger:self.ledger.cancel()
 def reconcile(self,consent=False):
  ledger=self.journal()
  if consent is not True or self.busy or ledger.job.state!='uncertain':raise ValueError('Review uncertain calendar readback first')
  self.busy=True;self.error=''
  def work():
   try:
    def readback(payload):
     self.verify_account(payload['account']);event_id='jarvis'+ledger.job.plan['review_id'];row=self.request('GET',event_id,account=payload['account'])
     if not self.same(row,payload,event_id):raise ValueError('Calendar outcome unknown')
     return {'verified':True,'external_id':event_id,'url':row.get('htmlLink')}
    ledger.reconcile(readback)
   except Exception:self.error='Calendar outcome remains unknown; do not retry. Inspect your calendar manually.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='calendar-reconcile',daemon=True);self.worker.start()
 def snapshot(self):
  try:state=self.journal().snapshot()
  except Exception:state={'state':'blocked','plan':None,'result':None};self.error='Calendar ledger invalid; preserve it and reconcile externally.'
  return {**state,'busy':self.busy,'error':self.error,'scope':'Solo primary-calendar bookkeeping only. No attendees, reminders, recurrence, video link or automatic conflict changes.'}
