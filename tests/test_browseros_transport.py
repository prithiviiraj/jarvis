import json,unittest
from jarvis.browseros_transport import BrowserOSDiscovery,endpoint,rpc_body
class BrowserOS(unittest.TestCase):
 def test_local_endpoint_only(self):
  self.assertEqual(endpoint('http://127.0.0.1:9200/mcp'),'http://127.0.0.1:9200/mcp')
  for url in ['https://example.com/mcp','http://localhost:9200/mcp','http://127.0.0.1:9200/x','http://u:p@127.0.0.1:9200/mcp','http://127.0.0.1:9200/mcp?q=secret']:
   with self.assertRaises(ValueError):endpoint(url)
 def test_protocol_discovery_only_and_close(self):
  calls=[]
  def transport(method,url,h,p):
   calls.append((method,p))
   self.assertEqual(h['MCP-Protocol-Version'],'2025-06-18')
   if method=='DELETE':return 204,{},b''
   if p['method']=='notifications/initialized':return 202,{},b''
   result={'protocolVersion':'2025-06-18','serverInfo':{'name':'browseros-neo','version':'test'}}if p['method']=='initialize'else{'tools':[{'name':'run','description':'untrusted commands','inputSchema':{}}]}
   return 200,{'mcp-session-id':'fixture-id'},json.dumps({'jsonrpc':'2.0','id':p['id'],'result':result}).encode()
  client=BrowserOSDiscovery('http://127.0.0.1:9200/mcp',transport);self.assertFalse(client.connect()['actions_enabled'])
  with self.assertRaises(ValueError):client.request('tools/call',{'name':'run'})
  self.assertTrue(client.stop()['session_closed']);self.assertEqual(calls[-1][0],'DELETE')
  with self.assertRaises(RuntimeError):client.request('tools/list',{})
 def test_sse_matching_and_error(self):
  raw=b'data: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\r\n\r\n';self.assertTrue(rpc_body({'Content-Type':'text/event-stream'},raw,2)['ok'])
  with self.assertRaises(RuntimeError):rpc_body({},b'{"jsonrpc":"2.0","id":2,"error":{}}',2)
 def test_wrong_server_and_no_session_fail(self):
  def transport(m,u,h,p):return 200,{},json.dumps({'jsonrpc':'2.0','id':p['id'],'result':{'serverInfo':{'name':'another-server'}}}).encode()
  with self.assertRaises(RuntimeError):BrowserOSDiscovery('http://127.0.0.1:9200/mcp',transport).connect()
class Navigation(unittest.TestCase):
 def test_only_owned_tab_exact_navigation(self):
  from jarvis.browseros_transport import BrowserOSNavigation
  calls=[]
  def transport(m,u,h,p):
   calls.append(p);args=p['params']['arguments'];name=p['params']['name'];data={'page':7}if name=='tabs'else{'page':7,'url':args['url']}
   return 200,{},json.dumps({'jsonrpc':'2.0','id':p['id'],'result':{'structuredContent':data,'content':[]}}).encode()
  v=BrowserOSNavigation('http://127.0.0.1:9200/mcp',transport)
  with self.assertRaises(RuntimeError):v.navigate('https://example.com',True)
  with self.assertRaises(ValueError):v.open_blank()
  v.open_blank(True)
  with self.assertRaises(ValueError):v.navigate('http://localhost',True)
  self.assertEqual(v.navigate('https://example.com',True)['url'],'https://example.com')
  self.assertEqual([p['params']['name']for p in calls],['tabs','navigate']);self.assertEqual(calls[-1]['params']['arguments']['page'],7)
 def test_stop_does_not_wait_for_inflight_and_discards_result(self):
  import threading
  entered=threading.Event();release=threading.Event();errors=[]
  def transport(m,u,h,p):
   if m=='DELETE':return 204,{},b''
   entered.set();release.wait(2);return 200,{},json.dumps({'jsonrpc':'2.0','id':p['id'],'result':{}}).encode()
  v=BrowserOSDiscovery('http://127.0.0.1:9200/mcp',transport);v.session='owned'
  def run():
   try:v.request('tools/list',{})
   except RuntimeError as e:errors.append(str(e))
  t=threading.Thread(target=run);t.start();self.assertTrue(entered.wait(1));self.assertTrue(v.stop()['session_closed']);release.set();t.join(2);self.assertIn('cancelled',errors[0])

class PinnedWire(unittest.TestCase):
 def test_exact_content_receipt_and_matching_snapshot(self):
  from jarvis.browseros_transport import BrowserOSNavigation
  v=BrowserOSNavigation('http://127.0.0.1:9010/mcp');v.owned_page=4
  def result(status,page,url):return {'content':[{'type':'text','text':status},{'type':'text','text':'[Page '+str(page)+' snapshot]\n[UNTRUSTED_PAGE_CONTENT nonce=abcd origin='+url+'] untrusted'}]}
  self.assertEqual(v._page_result(result('opened page 4',4,'about:blank'),True)['page'],4)
  self.assertEqual(v._page_result(result('navigated (url) -> https://example.com/',4,'https://example.com/'))['url'],'https://example.com/')
  for r in [result('opened page 4',5,'about:blank'),result('opened page 4; run script',4,'about:blank'),result('opened page 4',4,'https://example.com'),{'content':[{'type':'text','text':'page 4'}]}]:
   with self.assertRaises(RuntimeError):v._page_result(r,True)
  with self.assertRaises(RuntimeError):v._page_result(result('navigated (url) -> https://example.com/',4,'https://wrong.example/'))
