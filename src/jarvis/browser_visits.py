"""Bounded history of this adapter's verified public destinations only.
Never imports personal browser profiles, page text, images or account history.
"""
import json,threading,time,pathlib,os
from .browser_control import BrowserControl
class BrowserVisits:
 def __init__(self,path=None,clock=time.time):self.path=pathlib.Path(path)if path else None;self.clock=clock;self.rows=[];self.loaded=False;self.lock=threading.RLock();self.error=''
 def load(self):
  if self.loaded:return
  self.loaded=True
  if not self.path or not self.path.exists():return
  try:
   if self.path.stat().st_size>250000:raise ValueError('History file exceeds the bounded limit')
   rows=json.loads(self.path.read_text(encoding='utf-8'))
   if not isinstance(rows,list)or len(rows)>100:raise ValueError('Invalid visited-page history')
   clean=[]
   for row in rows:
    if not isinstance(row,dict)or set(row)!={'url','at'}or type(row['at'])not in (int,float)or not 0<row['at']<1e11:raise ValueError('Invalid visited-page receipt')
    BrowserControl.destination(row['url']);clean.append(dict(row))
   self.rows=clean
  except Exception:self.error='Saved JARVIS page history could not be read; original file preserved.'
 def record(self,url):
  if url=='about:blank':return
  BrowserControl.destination(url)
  with self.lock:
   self.load()
   if self.error:return
   self.rows=[{'url':url,'at':self.clock()}]+[r for r in self.rows if r['url']!=url][:99]
   if self.path:
    try:
     self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.rows,ensure_ascii=True),encoding='utf-8');os.replace(temp,self.path)
    except OSError:self.error='Page opened, but local visited-page history could not be saved.'
 def list(self,yesterday=False):
  with self.lock:
   self.load();rows=list(self.rows)
  if yesterday:
   import datetime
   from zoneinfo import ZoneInfo
   zone=ZoneInfo('Asia/Kolkata');day=datetime.datetime.fromtimestamp(self.clock(),zone).date()-datetime.timedelta(days=1)
   rows=[r for r in rows if datetime.datetime.fromtimestamp(r['at'],zone).date()==day]
  return [dict(r)for r in rows[:20]]
