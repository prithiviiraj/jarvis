"""Deterministic local browser voice commands. Page text never becomes instructions.
Navigation uses an isolated automation profile. No send/pay/delete/type automation.
"""
from urllib.parse import urlsplit,urlencode
import ipaddress
class BrowserControl:
 def __init__(self,page):self.page=page
 @staticmethod
 def destination(url):
  if not isinstance(url,str)or len(url)>2048:raise ValueError('Invalid browser destination')
  try:
   p=urlsplit(url);port=p.port
   if p.scheme!='https'or not p.hostname or p.username or p.password or port not in (None,443):raise ValueError()
   host=p.hostname.lower()
   if host in ('localhost','localhost.localdomain')or host.endswith(('.local','.internal','.localhost'))or '.'not in host:raise ValueError()
   try:
    ip=ipaddress.ip_address(host)
    if not ip.is_global:raise ValueError()
   except ValueError:
    if ':'in host or all(x.isdigit()or x=='.'for x in host):raise ValueError()
   return url
  except ValueError:raise ValueError('Use a public HTTPS site, not local or private addresses')
 def execute(self,command,value='',confirmed=False):
  if command=='search':
   if not isinstance(value,str)or not value.strip()or len(value)>300:raise ValueError('Enter a short search')
   # Search terms leave the machine; review exact text before navigation.
   if confirmed is not True:raise ValueError('Review search terms before opening browser')
   self.page.goto('https://www.google.com/search?'+urlencode({'q':value}),wait_until='domcontentloaded',timeout=15000)
  elif command=='open':
   url=self.destination(value)
   if confirmed is not True:raise ValueError('Review exact destination first')
   self.page.goto(url,wait_until='domcontentloaded',timeout=15000)
  elif command in ('scroll-down','scroll-up'):
   self.page.mouse.wheel(0,600 if command=='scroll-down'else-600)
  else:raise ValueError('Available: open site, search web, scroll up/down. Sending, buying and form submission are not enabled.')
  return {'url':self.page.url,'title':self.page.title()[:160]}
