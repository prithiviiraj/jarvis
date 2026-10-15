"""Pinned separately installed neo, disposable profile. No account import/model/API tasks."""
import os,pathlib,subprocess,time,json,urllib.request,hashlib,base64,io
from PIL import Image
from PIL import ImageGrab
from jarvis.browseros_transport import BrowserOSNavigation,http
root=pathlib.Path('ui-evidence/browseros-isolated').resolve();root.mkdir(parents=True,exist_ok=True)
exe=pathlib.Path(os.environ['BROWSEROS_EXE']).resolve();assert exe.is_file()
env=dict(os.environ);env['CLAW_ANALYTICS_ENABLED']='false'
p=subprocess.Popen([str(exe),'--enable-logging','--log-file='+str(root/'browser-startup.log'),'--user-data-dir='+str(root/'profile'),'--no-first-run','--no-default-browser-check','about:blank'],env=env)
client=None
rpc=[]
def recording_transport(method,url,headers,payload):
 result=http(method,url,headers,payload)
 try:body=json.loads(result[2])
 except (ValueError,UnicodeError):body=result[2].decode('utf-8',errors='replace')
 if isinstance(body,str)and payload and payload.get('method')=='initialize':
  from jarvis.browseros_transport import rpc_body
  parsed=rpc_body(result[1],result[2],payload['id']);parsed.pop('instructions',None);body={'server_metadata':parsed}
 rpc.append({'method':method,'request':payload,'status':result[0],'response':body})
 (root/'mcp-runtime.json').write_text(json.dumps(rpc,indent=2),encoding='utf-8')
 return result
try:
 candidates=['http://127.0.0.1:9200/mcp'];last='not started'
 # Read only disposable profile metadata. Do not scan the owner's profile or accounts.
 for _ in range(60):
  statefile=root/'profile'/'Local State'
  try:
   ports=json.loads(statefile.read_text(encoding='utf-8')).get('browseros',{}).get('server',{})
   for key in ['proxy_port','server_port','mcp_port']:
    port=ports.get(key)
    if type(port)is int and 0<port<65536:
     url='http://127.0.0.1:'+str(port)+'/mcp'
     if url not in candidates:candidates.insert(0,url)
  except (ValueError,OSError):pass
  for f in (root/'profile').rglob('sidecar.json'):
   try:
    x=json.loads(f.read_text());port=x.get('ports',{}).get('proxy')or x.get('ports',{}).get('server')
    if type(port)is int and 0<port<65536:
     url='http://127.0.0.1:'+str(port)+'/mcp'
     if url not in candidates:candidates.insert(0,url)
   except (ValueError,OSError):pass
  for endpoint in candidates:
   try:
    client=BrowserOSNavigation(endpoint,recording_transport);meta=client.connect();break
   except Exception as e:last=str(e);client=None
  if client:break
  time.sleep(2)
 if not client:
  ImageGrab.grab().save(root/'browseros-startup-failure.png')
  (root/'startup-failure.json').write_text(json.dumps({'candidates':candidates,'last_error':last,'process_exit':p.poll()},indent=2),encoding='utf-8')
  raise AssertionError('BrowserOS MCP not available in isolated profile: '+last)
 base=client.url[:-4]
 request=urllib.request.Request(base+'/api/v1/settings/telemetry',data=b'{"consent":false}',headers={'Content-Type':'application/json'},method='PUT')
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 with opener.open(request,timeout=5)as r:telemetry=json.load(r)
 assert telemetry.get('enabled')is False and telemetry.get('consent')is False,'Telemetry off not confirmed'
 opened=client.open_blank(True);assert opened['page']>0
 # Harmless public fixture only. This cannot prove real signed-in account automation.
 result=client.navigate('https://example.com',True);assert result['url'].startswith('https://example.com'),'Unexpected observed destination'
 snap=client.snapshot();assert not snap.get('isError');assert 'origin=https://example.com/'in json.dumps(snap)and 'Learn more'in json.dumps(snap),'Actual owned fixture snapshot not read'
 preview=client.screenshot();picture=base64.b64decode(preview['data_url'].split(',',1)[1],validate=True)
 (root/'owned-page-current.jpg').write_bytes(picture)
 with Image.open(io.BytesIO(picture))as image:
  assert image.format=='JPEG' and image.width>100 and image.height>100,'Actual owned page JPEG did not decode'
 scroll=client.scroll('down');assert scroll['acknowledged']is True,'Fixed scroll receipt missing'
 news=client.news_capture(result['url']);assert 'Example Domain'in news['text'],'Current-page news text was not from actual owned page'
 assert news['url']==result['url']and news['sha256']==hashlib.sha256(news['text'].encode()).hexdigest(),'Current text/origin/hash mismatch'
 (root/'captured-news.jpg').write_bytes(base64.b64decode(news.pop('picture').split(',',1)[1],validate=True))
 (root/'captured-news.json').write_text(json.dumps(news,indent=2),encoding='utf-8')
 ImageGrab.grab().save(root/'browseros-native-screen.png')
 # Actual public desktop YouTube layout acceptance. Read-only, no video opened.
 youtube=[]
 for query in ['science+education','public+domain+space']:
  target=client.navigate('https://www.youtube.com/results?search_query='+query,True)
  last_error=None
  for attempt in range(6):
   try:
    listed=client.youtube_videos(target['url']);break
   except RuntimeError as error:
    last_error=str(error)
    if attempt==5:raise AssertionError('Actual YouTube desktop layout did not yield verified anchors: '+last_error)
    time.sleep(2)
  assert listed['binding']=='single-result-anchor-v1' and listed['videos'],'No exact result anchor binding'
  checked=client.youtube_videos(target['url'])
  assert checked['videos'][0]==listed['videos'][0],'First result changed during fresh ordinal recheck; no selection allowed'
  preview=client.screenshot();(root/('youtube-'+query.replace('+','-')+'.jpg')).write_bytes(base64.b64decode(preview['data_url'].split(',',1)[1],validate=True))
  youtube.append({'observed_url':target['url'],'first_observation':listed,'fresh_recheck':checked,'scope':'Read-only real public desktop layout; no result opened, no account used'})
 (root/'youtube-layout-result.json').write_text(json.dumps(youtube,indent=2),encoding='utf-8')
 closed=client.stop();assert closed['session_closed']
 try:client.navigate('https://example.org',True)
 except RuntimeError:pass
 else:raise AssertionError('Stopped session allowed another navigation')
 (root/'result.json').write_text(json.dumps({'browser_exe':str(exe),'required_version':'0.51.1.2','server':meta['server'],'telemetry':telemetry,'opened_page':opened['page'],'observed_url':result['url'],'stop':closed,'scroll':scroll,'news':news,'owned_page_jpeg_bytes':len(picture),'scope':'Actual Windows neo isolated profile, harmless page, no accounts/model quality or owner speed claims'},indent=2))
 print('BrowserOS native isolated MCP, exact owned navigation, telemetry off, Stop: passed')
except Exception:
 ImageGrab.grab().save(root/'browseros-operation-failure.png')
 raise
finally:
 if client and not client.stopped:
  try:client.stop()
  except Exception:pass
 p.terminate()
 try:p.wait(10)
 except subprocess.TimeoutExpired:p.kill()
