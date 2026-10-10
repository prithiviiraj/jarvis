"""Owner-entered calendar draft edits, never saves events or guesses timezone."""
import datetime,re
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
FIELDS=('title','start','end','timezone','place','notes')
def update(current,text,now=None):
 moved=move(current,text,now)
 if moved is not None:return moved
 if not isinstance(current,dict)or not isinstance(text,str):return None
 m=re.fullmatch(r'\s*(?:(?:jarvis|lyra|dex)[,.:]?\s+)?calendar\s+(title|start|end|timezone|place|notes)\s+(.+?)\s*',text,re.I)
 if not m:return None
 field=m.group(1).lower();value=m.group(2);limit={'title':120,'place':240,'notes':1000,'timezone':80,'start':16,'end':16}[field]
 if len(value)>limit or any(ord(c)<32 for c in value):raise ValueError('Calendar field is too long or has control characters')
 if field in ('start','end'):
  if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',value):raise ValueError('Use exact YYYY-MM-DDTHH:MM. Relative dates and spoken times remain unresolved')
  datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M')
 if field=='timezone':
  try:ZoneInfo(value)
  except ZoneInfoNotFoundError:raise ValueError('Use a valid explicit IANA timezone')from None
 result=dict(current);result['revision']=current.get('revision',0)+1;result[field]=value;result['missing']=[k for k in ('title','start','end','timezone')if not result.get(k)]
 if result.get('start')and result.get('end'):
  start=datetime.datetime.strptime(result['start'],'%Y-%m-%dT%H:%M');end=datetime.datetime.strptime(result['end'],'%Y-%m-%dT%H:%M')
  if end<=start or (end-start).total_seconds()>7*86400:raise ValueError('End must follow start, at most7days')
 if result.get('start'):result['weekday']=datetime.datetime.strptime(result['start'],'%Y-%m-%dT%H:%M').strftime('%A')
 result['scope']='Unsaved owner draft. Review every field and confirm in the local calendar panel. No reminder, invitation, Google change or app opening.'
 return result

def move(current,text,now=None):
 """Move the unsaved draft as one revision; never changes a saved event."""
 if not isinstance(current,dict)or not isinstance(text,str):return None
 m=re.fullmatch(r'\s*(?:(?:jarvis|lyra|dex)[,.:]?\s+)?(?:calendar\s+)?move\s+(?:the\s+)?(?:calendar\s+)?draft\s+to\s+(\d{4}-\d{2}-\d{2}|today|tomorrow)[.!?]*\s*',text,re.I)
 if not m:return None
 if not all(current.get(k)for k in ('start','end','timezone')):raise ValueError('Enter exact draft start, end and timezone before moving its date')
 zone=ZoneInfo(current['timezone']);start=datetime.datetime.strptime(current['start'],'%Y-%m-%dT%H:%M');end=datetime.datetime.strptime(current['end'],'%Y-%m-%dT%H:%M');duration=end-start
 if duration.total_seconds()<=0 or duration.total_seconds()>7*86400:raise ValueError('Invalid draft duration')
 target=m.group(1).lower()
 if target in ('today','tomorrow'):
  clock=now or datetime.datetime.now(zone)
  if clock.tzinfo is None:raise ValueError('Date resolution requires an aware local clock')
  clock=clock.astimezone(zone)
  if clock.hour<4:
   a=clock.date();b=a+datetime.timedelta(days=1)
   raise ValueError('Early-morning day word is ambiguous. Give the exact date: '+a.strftime('%A %Y-%m-%d')+' or '+b.strftime('%A %Y-%m-%d'))
  day=clock.date()+datetime.timedelta(days=target=='tomorrow')
 else:day=datetime.datetime.strptime(target,'%Y-%m-%d').date()
 new_start=datetime.datetime.combine(day,start.time());new_end=new_start+duration
 def offset(wall):
  choices=[]
  for fold in (0,1):
   candidate=wall.replace(tzinfo=zone,fold=fold)
   if candidate.astimezone(datetime.timezone.utc).astimezone(zone).replace(tzinfo=None)==wall:choices.append(candidate.utcoffset())
  if not choices or len(set(choices))!=1:raise ValueError('Draft time is missing or ambiguous at a daylight-saving change. Enter exact valid start/end instead')
  return choices[0]
 if offset(new_start)!=offset(new_end):raise ValueError('Draft spans a timezone clock change. Enter exact start/end instead')
 result=dict(current);result['start']=new_start.strftime('%Y-%m-%dT%H:%M');result['end']=new_end.strftime('%Y-%m-%dT%H:%M');result['weekday']=new_start.strftime('%A');result['revision']=current.get('revision',0)+1
 result['missing']=[k for k in ('title','start','end','timezone')if not result.get(k)]
 result['scope']='Unsaved draft date moved; existing local times and duration retained. Review every field before saving. No saved event, reminder, invitation or external calendar changed.'
 return result
