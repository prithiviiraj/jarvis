"""Explicit local session news selection. No fetching, default source or inference."""
import re
from .browser_control import BrowserControl
class NewsConductor:
 def __init__(self):self.capture_requested=False;self.transport='legacy';self.requested=False;self.source='';self.pending=None;self.status='Choose your news page';self.awaiting_open=False;self.observed_url='';self.text_preview=None;self.observed_revision=None
 def request(self,text):
  if not isinstance(text,str):return False
  pattern=r"\s*(?:(?:jarvis|lyra|dex)[,.:]?\s+)?(?:news|show (?:me )?(?:the )?news|open (?:the )?news|what(?:'s| is) (?:the )?news(?: today)?)(?: with (?:images|pictures))?(?: from (https://[^\s]+))?[?!.]*\s*"
  match=re.fullmatch(pattern,text,re.I)
  if not match:return False
  if match.group(1):self.preview(match.group(1));return True
  self.cancel();self.source='';self.requested=True;self.status='Which news page should I open? Paste its HTTPS URL.';return True
 def preview(self,url):
  url=BrowserControl.destination(url)
  self.capture_requested=False;self.source=url;self.pending={'command':'open','value':url,'scope':'Open this exact news page in the reviewed browser; no headlines or audio fetched yet'};self.requested=True;self.awaiting_open=False;self.observed_url='';self.text_preview=None;self.status='Review exact news page before opening';return dict(self.pending)
 def confirm(self,reviewed,confirm=False):
  if confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review the exact news page first')
  proposal=dict(self.pending);self.pending=None;self.awaiting_open=True;self.status='Opening requested page; waiting for observed browser result';return proposal
 def observe(self,state):
  if self.observed_url and (state.get('state')in ('error','stopping','off')or state.get('state')=='ready'and (state.get('url')!=self.observed_url or self.observed_revision is not None and state.get('page_revision')!=self.observed_revision)):
   self.observed_url='';self.text_preview=None;self.awaiting_open=False;self.status='Observed news page is no longer current. Review the source and capture again.'
  if not self.awaiting_open:return
  if state.get('state')=='error':self.awaiting_open=False;self.status='News page did not open; no reading started';return
  if state.get('state')=='ready'and state.get('requested_url')==self.source:
   self.awaiting_open=False;self.observed_url=BrowserControl.destination(state.get('url'));self.observed_revision=state.get('page_revision');self.status='Page opened. Shall I read it for you? Review the visible page text first.'
 def accept_text(self,row):
  from .news_page import validate
  validate(row)
  if row['url']!=self.observed_url:raise ValueError('News capture does not match observed page')
  self.text_preview=dict(row);self.status='Review exact visible page text; no model receives it'
 def cancel(self):self.capture_requested=False;self.pending=None;self.awaiting_open=False;self.requested=False;self.text_preview=None;self.observed_url='';self.status='News request cancelled; no reading started'
 def snapshot(self):return {'transport':self.transport,'requested':self.requested,'source':self.source,'pending':self.pending,'status':self.status,'observed_url':self.observed_url,'reading_available':True,'text_preview':self.text_preview}
