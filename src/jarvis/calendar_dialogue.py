"""Owner-entered exact calendar draft fields, no event save or relative guesses."""
import datetime,re
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
FIELDS=('title','start','end','timezone','place','notes')
def update(current,text):
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
