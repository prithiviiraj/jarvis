"""Explicit verified calendar-to-Telegram draft handoff. Never submits output."""
import copy,threading
class CalendarTelegram:
 def __init__(self,calendar,output):self.calendar=calendar;self.output=output;self.generation=0;self.busy=False;self.worker=None;self.status='No calendar confirmation draft';self.error=''
 def prepare(self,consent=False):
  if consent is not True:raise ValueError('Review account/event to paired-chat draft handoff')
  if self.busy or self.calendar.busy or self.output.busy:raise ValueError('Previous connector action running')
  source=self.calendar.snapshot()
  if source['state']!='completed'or not source.get('plan')or not source.get('result'):raise ValueError('Only exact completed calendar event can supply draft')
  if not self.output.connection.pair.bound or not self.output.connection.bot:raise ValueError('Verify private Telegram pairing first')
  source=copy.deepcopy(source);self.generation+=1;ticket=self.generation;calendar_ticket=self.calendar.generation;connection_ticket=self.calendar.connection.generation;telegram_ticket=self.output.connection.generation;identity=copy.deepcopy(self.output.connection.pair.bound);bot=copy.deepcopy(self.output.connection.bot);self.busy=True;self.error='';self.status='Rechecking exact event, no Telegram output sent'
  def work():
   try:
    p=source['plan']['payload'];event_id=source['result']['external_id'];self.calendar.verify_account(p['account']);row=self.calendar.request('GET',event_id,account=p['account'])
    if not self.calendar.same(row,p,event_id):raise ValueError('Event changed; no draft')
    current=self.calendar.snapshot()
    if self.generation!=ticket or self.calendar.generation!=calendar_ticket or self.calendar.connection.generation!=connection_ticket or current['state']!='completed'or current['plan']!=source['plan']or current['result']!=source['result']or self.output.connection.generation!=telegram_ticket or self.output.connection.pair.bound!=identity or self.output.connection.bot!=bot:raise ValueError('Source/destination changed; no draft')
    text='Calendar event verified in '+p['account']+' (primary).\nTitle: '+p['title']+'\nStart: '+p['start']+'\nEnd: '+p['end']+'\nLocation: '+(p['location']or'None')+'\nNo invitations or reminders requested. This is a solo calendar event, not a restaurant/business booking confirmation.'
    # Omit private notes, use only exact reviewed metadata. Existing output review
    # handles final bot/chat/words approval and re-verification; never auto-submit.
    self.output.prepare(text);self.status='Telegram draft ready for exact destination and words review; not sent'
   except Exception:self.error='Event/destination unavailable or changed; no automatic draft retry or output send';self.status='Calendar confirmation draft not prepared'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,daemon=True);self.worker.start()
 def stop(self):self.generation+=1;self.status='Pending calendar-to-Telegram handoff stopped; no output sent'
 def snapshot(self):return {'busy':self.busy,'status':self.status,'error':self.error,'scope':'Explicit draft handoff from exact live-verified solo event metadata. Omits notes; no Telegram submit, voice, background trigger or Zapier account.'}
