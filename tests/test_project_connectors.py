import base64,threading,unittest,json
from jarvis.project_connectors import ProjectConnectors
class Store:
 def __init__(self):self.rows={}
 def get(self,k):return self.rows.get(k)
 def set(self,k,v):self.rows[k]=v
 def delete(self,k):self.rows.pop(k,None)
class Tests(unittest.TestCase):
 def fixture(self,read=None):
  calls=[]
  def transport(s,m,u,p,t):
   calls.append((s,m,u,p,t))
   if u.endswith('/user'):return {'login':'owner'}
   if u.endswith('/users/me'):return {'id':'11111111-1111-4111-8111-111111111111','type':'bot'}
   return read(u)if read else []
  return ProjectConnectors(Store(),transport),calls
 def connected(self,q,s='github',i='owner'):
  q.connect(s,i,'fixture-token-only',True);q.worker.join(2);self.assertFalse(q.error)
 def test_inert_exact_identity_and_local_secret(self):
  q,c=self.fixture();self.assertFalse(c);self.assertIsNone(q.worker)
  with self.assertRaises(ValueError):q.connect('github','owner','fixture-token-only')
  self.connected(q);self.assertEqual(q.accounts,{'github':'owner'});self.assertNotIn('fixture-token',json.dumps(q.snapshot()));q.disconnect('github',True);self.assertFalse(q.store.rows)
 def test_wrong_identity_not_saved(self):
  q,c=self.fixture();q.connect('github','wrong','fixture-token-only',True);q.worker.join(2);self.assertTrue(q.error);self.assertFalse(q.store.rows)
 def test_file_exact_ref_and_read_only(self):
  raw=b'Untrusted external source'
  q,c=self.fixture(lambda u:{'type':'file','path':'docs/readme.md','encoding':'base64','size':len(raw),'content':base64.b64encode(raw).decode(),'sha':'observed-sha'})
  self.connected(q);q.read('github',{'owner':'owner','repo':'repo','kind':'file','path':'docs/readme.md','ref':'main'},True);q.worker.join(2);self.assertFalse(q.error);self.assertEqual(q.result['content'],raw.decode());self.assertTrue(all(x[1]=='GET'and x[3]is None for x in c))
 def test_issue_partial_and_invalid_paths(self):
  q,c=self.fixture(lambda u:[{'number':7,'title':'External title'}]);self.connected(q);q.read('github',{'owner':'owner','repo':'repo','kind':'issues'},True);q.worker.join(2);self.assertFalse(q.result['complete'])
  q.read('github',{'owner':'owner','repo':'repo','kind':'file','path':'../secret','ref':'main'},True);q.worker.join(2);self.assertTrue(q.error)
  with self.assertRaises(ValueError):q.request('github','/user?redirect=bad','fixture')
 def test_notion_bounded_child_page(self):
  q,c=self.fixture(lambda u:{'results':[{'object':'block','id':'external'}],'has_more':True});self.connected(q,'notion','11111111-1111-4111-8111-111111111111');q.read('notion',{'block_id':'22222222-2222-4222-8222-222222222222'},True);q.worker.join(2);self.assertFalse(q.error);self.assertFalse(q.result['complete']);self.assertIn('page_size=20',c[-1][2])
 def test_stop_prevents_late_save(self):
  entered=threading.Event();release=threading.Event();q=ProjectConnectors(Store(),lambda *a:entered.set()or release.wait(2)or {})
  def transport(*a):entered.set();release.wait(2);return {'login':'owner'}
  q.transport=transport;q.connect('github','owner','fixture-token-only',True);entered.wait(1);q.stop();release.set();q.worker.join(2);self.assertFalse(q.store.rows);self.assertIsNone(q.result)
 def test_restart_no_auto_access_saved_reverify(self):
  q,c=self.fixture();self.connected(q);before=len(c);fresh=ProjectConnectors(q.store,q.transport);self.assertFalse(fresh.accounts);self.assertEqual(len(c),before);fresh.connect('github','owner','',True);fresh.worker.join(2);self.assertFalse(fresh.error);self.assertEqual(fresh.accounts['github'],'owner')
