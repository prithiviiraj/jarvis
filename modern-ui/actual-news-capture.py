"""Actual Chromium fixture page, intercepted locally with zero external requests."""
import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'src'))
from playwright.sync_api import sync_playwright
from jarvis.news_page import capture,validate
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
 page.goto('https://example.com/different')
 try:capture(page,'https://example.com/news')
 except ValueError:pass
 else:raise AssertionError('Changed page accepted')
 result={'scope':'Actual headless Chromium intercepted fixture, no external network/page, no device proof','checks':['observed DOM captured','same-URL edit changes quote hash','changed URL rejected'],'intercepted_requests':requests}
 print(json.dumps(result,indent=2));pathlib.Path('ui-evidence/actual-news-capture.json').write_text(json.dumps(result,indent=2));b.close()
