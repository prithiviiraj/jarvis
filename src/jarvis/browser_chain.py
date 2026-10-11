"""Explicit bounded read-only browser chain. Page/model words never become steps."""
import re,json,time
from .browser_control import BrowserControl

def parse(text):
 if not isinstance(text,str)or len(text)>1500:return None
 text=re.sub(r'^\s*(?:(?:hey\s+)?(?:jarvis|lyra|dex|laya)[,.:]?\s+)?','',text,flags=re.I).strip().rstrip('.!?')
 # Deliberate chain separators only; do not split ordinary query words.
 parts=re.split(r'\s+then\s+|\s*,\s*(?=(?:open|search|click|read|scroll)\b)',text,flags=re.I)
 if len(parts)<2:return None
 if len(parts)>6:raise ValueError('Use at most6browser steps')
 steps=[]
 for part in parts:
  t=part.strip()
  if re.fullmatch(r'open (?:the |a )?(?:browser|brave)',t,re.I):steps.append({'command':'open-window','value':''});continue
  m=re.fullmatch(r'(?:browser )?search(?: for)? (.{1,200})',t,re.I)
  if m:
   if re.search(r'\b(?:then|send|pay|delete|upload|password|credential)\b',m[1],re.I):raise ValueError('Unsafe or ambiguous search step')
   steps.append({'command':'search','value':m[1]});continue
  m=re.fullmatch(r'open (https://\S+)',t,re.I)
  if m:steps.append({'command':'open','value':BrowserControl.destination(m[1])});continue
  m=re.fullmatch(r'open (?:its |the )?(wikipedia)(?: page)?',t,re.I)
  if m:steps.append({'command':'observed-site','value':'wikipedia.org'});continue
  m=re.fullmatch(r'(?:click|open|select) (?:the )?(first|[1-9]|1[0-9]|20) link',t,re.I)
  if m:steps.append({'command':'observed-link','value':1 if m[1].lower()=='first'else int(m[1])});continue
  if re.fullmatch(r'(?:browser )?read (?:the )?links',t,re.I):steps.append({'command':'read-links','value':''});continue
  m=re.fullmatch(r'scroll (up|down)',t,re.I)
  if m:steps.append({'command':'scroll-'+m[1].lower(),'value':''});continue
  raise ValueError('Unsupported chain step. Use open browser, search, exact HTTPS URL, observed Wikipedia/link number or read links. Nothing started.')
 return {'command':'chain','value':json.dumps(steps,ensure_ascii=True,separators=(',',':'))}

def validate(value):
 if not isinstance(value,str)or len(value)>3000:raise ValueError('Invalid browser chain')
 steps=json.loads(value)
 if not isinstance(steps,list)or not 2<=len(steps)<=6:raise ValueError('Invalid step count')
 for s in steps:
  if not isinstance(s,dict)or set(s)!={'command','value'}:raise ValueError('Invalid chain step')
  c,v=s['command'],s['value']
  if c=='open':BrowserControl.destination(v)
  elif c=='search':
   if not isinstance(v,str)or not 1<=len(v)<=200:raise ValueError('Invalid search')
  elif c=='observed-link':
   if type(v)is not int or not 1<=v<=20:raise ValueError('Invalid link')
  elif c=='observed-site':
   if v!='wikipedia.org':raise ValueError('Unsupported observed site')
  elif c in ('open-window','read-links','scroll-up','scroll-down'):
   if v!='':raise ValueError('Unexpected step value')
  else:raise ValueError('Unsupported chain command')
 return steps

def execute(page,value,cancel,report=lambda row:None):
 from .browser_links import links
 from urllib.parse import urlsplit
 steps=validate(value);rows=[];deadline=time.monotonic()+60
 for index,s in enumerate(steps):
  if cancel.is_set():raise ValueError('Browser chain stopped; remaining steps discarded')
  if time.monotonic()>deadline:raise ValueError('Browser chain exceeded60seconds')
  c,v=s['command'],s['value']
  if c in ('observed-link','observed-site','read-links','scroll-up','scroll-down'):BrowserControl.destination(page.url)
  if c in ('observed-link','observed-site','read-links'):
   page.locator('a[href]').first.wait_for(state='attached',timeout=5000)
   if cancel.is_set():raise ValueError('Chain stopped while waiting for links')
   snapshot=links(page)
   if c=='observed-site':
    candidates=[r for r in snapshot['links']if (urlsplit(r['url']).hostname or '').lower()=='wikipedia.org'or (urlsplit(r['url']).hostname or '').lower().endswith('.wikipedia.org')]
    if len(candidates)!=1:raise ValueError('Wikipedia result missing or ambiguous; chain paused, choose an observed link')
    target=candidates[0]['url']
   elif c=='observed-link':
    if v>len(snapshot['links']):raise ValueError('Requested link number not observed')
    target=snapshot['links'][v-1]['url']
   if c!='read-links':
    if page.url!=snapshot['page_url']:raise ValueError('Page changed while reading links')
    if cancel.is_set():raise ValueError('Chain stopped before navigation')
    result=BrowserControl(page).execute('open',target,True)
   else:result={'url':page.url,'title':page.title()[:160],'links':snapshot['links']}
  else:result=BrowserControl(page).execute(c,v,True)
  if cancel.is_set():raise ValueError('Chain stopped after submitted step; no remaining steps started')
  row={'step':index+1,'command':c,'url':result['url'],'status':'completed'};rows.append(row);report(dict(row))
 return dict(result,chain_steps=rows)
