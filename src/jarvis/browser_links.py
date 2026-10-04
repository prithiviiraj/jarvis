"""Browser link proposals only. Never click a page control or submit a form."""
from urllib.parse import urljoin
from .browser_control import BrowserControl

def links(page):
 # Labels and hrefs are untrusted data. Only public HTTPS navigation can be offered.
 rows=page.locator('a[href]').evaluate_all('(els)=>els.slice(0,100).map(e=>({label:(e.innerText||e.getAttribute("aria-label")||"").trim().slice(0,120),href:e.href}))')
 out=[];seen=set()
 for r in rows:
  if not r.get('label'):continue
  url=urljoin(page.url,r.get('href',''))
  try:BrowserControl.destination(url)
  except ValueError:continue
  if url in seen:continue
  seen.add(url);out.append({'id':str(len(out)+1),'label':r['label'],'url':url})
  if len(out)==20:break
 return {'page_url':page.url,'links':out}

def prepare_select(snapshot,link_id,current_url):
 if snapshot['page_url']!=current_url:raise ValueError('Page changed. Read available links again')
 row=next((r for r in snapshot['links']if r['id']==link_id),None)
 if not row:raise ValueError('Select an observed link number')
 return {'command':'open','value':BrowserControl.destination(row['url']),'label':row['label']}
