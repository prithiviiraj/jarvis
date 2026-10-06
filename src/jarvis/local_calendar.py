"""Explicit reviewed local Obsidian calendar notes. No Google sync or invitations."""
import datetime,hashlib,json,re,uuid,calendar
class LocalCalendar:
 def __init__(self,vault):self.vault=vault;self.pending=None;self.status='Local notes only';self.result=''
 def preview(self,event):
  if not self.vault.enabled:raise ValueError('Create managed Brain of Brain vault first')
  if not isinstance(event,dict)or set(event)!={'title','start','end','place','notes','timezone'}:raise ValueError('Review full calendar event fields')
  for k,cap in [('title',120),('place',240),('notes',1000),('timezone',80),('start',16),('end',16)]:
   if not isinstance(event[k],str)or len(event[k])>cap or any(ord(c)<32 and c!='\n'for c in event[k]):raise ValueError('Invalid calendar field')
  if not event['title'].strip()or not event['timezone'].strip():raise ValueError('Title and explicit timezone required')
  from zoneinfo import ZoneInfo
  ZoneInfo(event['timezone'])
  start=datetime.datetime.strptime(event['start'],'%Y-%m-%dT%H:%M');end=datetime.datetime.strptime(event['end'],'%Y-%m-%dT%H:%M')
  if end<=start or (end-start).total_seconds()>7*86400:raise ValueError('End must follow start, at most7days')
  data=dict(event);data['weekday']=start.strftime('%A');data['scope']='Local Obsidian note only, no reminders, conflict verification, Google sync or invitations';data['sha256']=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest();self.pending=data;return dict(data)
 def cancel(self):self.pending=None
 def save(self,reviewed,confirm=False):
  if confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review full exact local event before saving')
  data=dict(self.pending);self.preview({k:data[k]for k in ('title','start','end','place','notes','timezone')});ident=uuid.uuid4().hex;filename='Calendar/Events/'+data['start'][:10]+'-'+ident+'.md';p=self.vault.safe(filename);p.parent.mkdir(parents=True,exist_ok=True)
  metadata=json.dumps(data,ensure_ascii=False);text='---\njarvis_local_event: '+metadata+'\n---\n\n# '+data['title']+'\n\n'+data['weekday']+' '+data['start']+' to '+data['end']+' ('+data['timezone']+')\n\nPlace: '+data['place']+'\n\n'+data['notes']+'\n\n[[Calendar/Home|Calendar]] · [[Planning/Today|Today plan]]\n\n'+data['scope']+'\n'
  with p.open('x',encoding='utf-8')as f:f.write(text)
  self.pending=None;self.result=str(p);self.status='Local event saved; no external calendar changed';return filename
 def rows(self):
  if not self.vault.enabled or self.vault.root is None:return []
  root=self.vault.safe('Calendar/Events');rows=[]
  if not root.exists():return rows
  for p in sorted(root.glob('*.md'),reverse=True)[:100]:
   try:
    if p.resolve().parent!=root.resolve()or p.stat().st_size>8192:continue
    lines=p.read_text(encoding='utf-8').splitlines()
    if len(lines)>1 and lines[1].startswith('jarvis_local_event: '):
     row=json.loads(lines[1][len('jarvis_local_event: '):]);self.preview_check(row);rows.append({k:row[k]for k in ('title','start','end','timezone','place')})
   except (OSError,ValueError,KeyError):continue
  return sorted(rows,key=lambda r:r['start'])
 def preview_check(self,row):
  if not isinstance(row,dict)or any(not isinstance(row.get(k),str)for k in ('title','start','end','timezone','place')):raise ValueError('Invalid local event record')
 def snapshot(self):return {'pending':self.pending,'status':self.status,'result':self.result,'events':self.rows(),'scope':'Local Obsidian notes only; no background scheduling, reminders, conflict detection or Google sync.'}
