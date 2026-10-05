"""Explicit local model proposals; no executor and no authority from model output."""
import hashlib,json,time
from urllib.parse import urlsplit
from .experimental.browser_proposals import Snapshot,Element,validate
from .experimental.browser_gate import gate,ReadScope
from .experimental.laya_local import LayaLocal

def fingerprint(state):
 return hashlib.sha256(json.dumps({'url':state.get('url'),'links':state.get('links',[])},sort_keys=True).encode()).hexdigest()
def prepare(state,goal,client=None):
 if state.get('state')!='ready':raise ValueError('Open a reviewed page and read its links first')
 from .browser_control import BrowserControl
 url=BrowserControl.destination(state.get('url'));rows=state.get('links',[])
 if not isinstance(rows,list)or len(rows)>20:raise ValueError('Use current bounded browser links')
 if any(not isinstance(r,dict)or not isinstance(r.get('id'),str)or not isinstance(r.get('label'),str)or not isinstance(r.get('url'),str)for r in rows):raise ValueError('Invalid offered links')
 if len({r['id']for r in rows})!=len(rows):raise ValueError('Duplicate offered links')
 elements=tuple(Element(r['id'],r['label'],'link',True)for r in rows)
 now=time.monotonic();snapshot=Snapshot(fingerprint(state),url,now,elements);hosts=(urlsplit(url).hostname,)
 proposal=(client or LayaLocal()).prepare(snapshot,goal,hosts,now,snapshot.id)
 validate(snapshot,hosts,time.monotonic())
 if proposal.operation in ('DONE','BLOCKED'):return None,'Model proposed '+proposal.operation+'; no completion or action is claimed.'
 scope=ReadScope(goal,('CLICK','SCROLL_DOWN','SCROLL_UP','WAIT'),True,tuple(e.id for e in elements));gate(scope,proposal)
 if proposal.operation=='WAIT':return None,'Model proposed WAIT; no action taken.'
 if proposal.operation=='CLICK':
  row=next(r for r in rows if r['id']==proposal.target_id)
  return {'command':'open','value':BrowserControl.destination(row['url']),'expected_url':url},'Laya suggested an observed link. Exact review required.'
 return {'command':'scroll-down'if proposal.operation=='SCROLL_DOWN'else'scroll-up','value':'','expected_url':url},'Laya suggested scrolling this page. Exact review required.'
