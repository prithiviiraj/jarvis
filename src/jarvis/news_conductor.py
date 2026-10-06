"""Explicit local session news selection. No fetching, default source or inference."""
import re
from .browser_control import BrowserControl
class NewsConductor:
 def __init__(self):self.requested=False;self.source='';self.pending=None;self.status='Choose your news page';self.awaiting_open=False;self.observed_url='';self.text_preview=None
 def request(self,text):
  if not isinstance(text,str)or not re.fullmatch(r"\s*(?:jarvis[,.:]?\s+)?(?:news|show (?:me )?(?:the )?news|open (?:the )?news|what(?:'s| is) (?:the )?news(?: today)?)[?!.]*\s*",text,re.I):return False
  self.requested=True;self.status='Which news page should I open? Paste its HTTPS URL.';return True
 def preview(self,url):
  url=BrowserControl.destination(url)
  self.source=url;self.pending={'command':'open','value':url,'scope':'Open this exact news page in the reviewed browser; no headlines or audio fetched yet'};self.requested=True;self.awaiting_open=False;self.observed_url='';self.text_preview=None;self.status='Review exact news page before opening';return dict(self.pending)
 def confirm(self,reviewed,confirm=False):
  if confirm is not True or self.pending is None or reviewed!=self.pending:raise ValueError('Review the exact news page first')
  proposal=dict(self.pending);self.pending=None;self.awaiting_open=True;self.status='Opening requested page; waiting for observed browser result';return proposal
 def observe(self,state):
  if not self.awaiting_open:return
  if state.get('state')=='error':self.awaiting_open=False;self.status='News page did not open; no reading started';return
  if state.get('state')=='ready'and state.get('requested_url')==self.source:
   self.awaiting_open=False;self.observed_url=BrowserControl.destination(state.get('url'));self.status='Page opened. Shall I read it for you? Review the visible page text first.'
 def accept_text(self,row):
  from .news_page import validate
  validate(row)
  if row['url']!=self.observed_url:raise ValueError('News capture does not match observed page')
  self.text_preview=dict(row);self.status='Review exact visible page text; no model receives it'
 def cancel(self):self.pending=None;self.awaiting_open=False;self.requested=False;self.text_preview=None;self.observed_url='';self.status='News request cancelled; no reading started'
 def snapshot(self):return {'requested':self.requested,'source':self.source,'pending':self.pending,'status':self.status,'observed_url':self.observed_url,'reading_available':True,'text_preview':self.text_preview}
