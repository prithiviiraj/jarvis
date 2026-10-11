"""Actual Chromium fixture page, intercepted locally with zero external requests."""
import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'src'))
from playwright.sync_api import sync_playwright
from jarvis.news_page import capture,validate
from jarvis.browser_control import BrowserSession
from jarvis.news_conductor import NewsConductor
import threading
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page();requests=[]
 def route(r):
  requests.append(r.request.url);r.fulfill(status=200,content_type='text/html',body='<html><title>Local News Fixture</title><body><nav>Fixture navigation</nav><main><h1>Fixture headline, not actual news</h1><p>Quoted local content only.</p></main></body></html>')
 page.route('**/*',route)
 # Wait on the expected content, not only navigation lifecycle; fail with pixels
 # and current URL/DOM if the runner never exposes the locally fulfilled body.
 page.goto('https://example.com/news',wait_until='domcontentloaded')
 try:page.locator('h1').filter(has_text='Fixture headline, not actual news').wait_for(state='visible',timeout=15000)
 except Exception:
  pathlib.Path('ui-evidence/news-capture-readiness-failure.html').write_text(page.content(),encoding='utf-8')
  page.screenshot(path='ui-evidence/news-capture-readiness-failure.png')
  print(json.dumps({'url':page.url,'intercepted_requests':requests,'failure':'expected local fixture content never became visible'}));raise
 row=capture(page,'https://example.com/news');assert 'Fixture headline' in validate(row)
 page.evaluate("document.querySelector('main').innerHTML='<h1>Changed fixture headline</h1>'")
 changed=capture(page,'https://example.com/news');assert changed['sha256']!=row['sha256']
 # Real Chromium navigation events update the same worker-owned state contract.
 session=BrowserSession.__new__(BrowserSession);session.lock=threading.RLock();session.state={'state':'ready','url':page.url,'news_text':changed,'links':[{'url':'old'}]};session.observe_page(page)
 news=NewsConductor();proposal=news.preview(page.url);news.confirm(proposal,True);news.observe({'state':'ready','url':page.url,'requested_url':page.url,'page_revision':0});news.accept_text(changed)
 page.reload(wait_until='domcontentloaded');page.locator('h1').wait_for(state='visible')
 assert session.snapshot()['page_revision']>=1 and 'news_text'not in session.snapshot() and not session.snapshot()['links']
 news.observe(session.snapshot());assert not news.observed_url and news.text_preview is None
 page.screenshot(path='ui-evidence/actual-news-page-reloaded.png')
 # Actual intercepted Chromium chained navigation, no external search traffic.
 from jarvis.browser_chain import parse as chain_parse,execute as chain_execute
 page.unroute('**/*')
 def chain_route(r):
  requests.append(r.request.url)
  body=('<a href="https://en.wikipedia.org/wiki/Iron_Man">Iron Man Wikipedia</a>'if 'google.com'in r.request.url else '<h1>Observed Wikipedia fixture</h1><a href="https://example.com/final">First observed fixture link</a>')
  r.fulfill(status=200,content_type='text/html',body='<html><title>Chain fixture</title><body>'+body+'</body></html>')
 page.route('**/*',chain_route)
 chained=chain_execute(page,chain_parse('open browser then search Iron Man then open Wikipedia page then click first link')['value'],threading.Event())
 assert len(chained['chain_steps'])==4 and page.url=='https://example.com/final'
 page.screenshot(path='ui-evidence/actual-browser-chain.png')
 pathlib.Path('ui-evidence/actual-browser-chain.json').write_text(json.dumps({'scope':'Actual Chromium intercepted chain, no external sites or owner hardware','steps':chained['chain_steps']},indent=2))
 page.goto('https://example.com/different')
 assert session.snapshot()['url']==page.url and 'news_text'not in session.snapshot()
 try:capture(page,'https://example.com/news')
 except ValueError:pass
 else:raise AssertionError('Changed page accepted')
 page.close();assert session.snapshot()['state']=='off' and not session.snapshot()['url']
 result={'scope':'Actual headless Chromium intercepted fixture, no external network/page, no device proof','checks':['observed DOM captured','same-URL edit changes quote hash','changed URL rejected','actual Chromium same-URL reload revokes captured news','actual Chromium manual URL event clears quote and links','actual Chromium close clears observed page'],'intercepted_requests':requests}
 print(json.dumps(result,indent=2));pathlib.Path('ui-evidence/actual-news-capture.json').write_text(json.dumps(result,indent=2));b.close()
