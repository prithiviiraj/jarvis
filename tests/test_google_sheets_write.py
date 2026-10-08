import tempfile,pathlib,unittest,types
from jarvis.google_sheets_write import SheetsWrite
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.cells=[['old','prior']];self.calls=[];self.conn=types.SimpleNamespace(account='owner@example.invalid',busy=False,generation=0,tokens=types.SimpleNamespace(access=lambda a,s:'fixture'))
  def transport(m,u,p):
   self.calls.append((m,u,p))
   if '/values/'not in u:return {'spreadsheetId':'fixture','properties':{'title':'Exact book'},'sheets':[{'properties':{'sheetId':4,'title':'Tab','gridProperties':{'rowCount':100,'columnCount':10}}}]}
   if m=='PUT':self.cells=p['values'];return {'spreadsheetId':'fixture','updatedCells':2}
   return {'range':'Tab!A1:B1','values':self.cells}
  self.transport=transport;self.a=SheetsWrite(self.conn,pathlib.Path(self.tmp.name)/'ledger.json',transport,lambda t:{'email_verified':True,'email':self.conn.account})
 def tearDown(self):self.a.stop();self.tmp.cleanup()
 def prepare(self):self.a.prepare('fixture','Tab','A1:B1',[['=1+2','']],True);self.a.worker.join(3);self.assertFalse(self.a.error);return self.a.snapshot()['plan']
 def test_exact_review_raw_and_readback_restart(self):
  r=self.prepare();self.assertEqual(r['payload']['before'],[['old','prior']]);self.assertFalse(any(m=='PUT'for m,u,p in self.calls))
  with self.assertRaises(ValueError):self.a.submit(r)
  self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'completed');put=[x for x in self.calls if x[0]=='PUT'][0];self.assertIn('valueInputOption=RAW',put[1]);self.assertEqual(put[2]['values'],[['=1+2','']]);self.assertEqual(SheetsWrite(self.conn,self.a.path).snapshot()['state'],'completed')
 def test_prior_change_no_write(self):
  r=self.prepare();self.cells=[['changed','prior']];self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'review');self.assertFalse(any(x[0]=='PUT'for x in self.calls))
 def test_write_failure_uncertain_no_retry(self):
  r=self.prepare();old=self.a.transport
  def bad(m,u,p):
   if m=='PUT':raise OSError('interrupted')
   return old(m,u,p)
  self.a.transport=bad;self.a.submit(r,True);self.a.worker.join(3);fresh=SheetsWrite(self.conn,self.a.path);self.assertEqual(fresh.snapshot()['state'],'uncertain')
  with self.assertRaises(ValueError):fresh.prepare('fixture','Tab','A1:B1',[['a','b']],True)
 def test_scope_dimensions_stop(self):
  with self.assertRaises(ValueError):self.a.prepare('fixture','Tab','A1:B1',[['a','b']])
  for rect,v in [('A1:A101',[['a']]*101),('B1:A1',[['a']]),('A1:B1',[['a']])]:
   with self.assertRaises(ValueError):self.a.rectangle('Tab',rect,v)
  r=self.prepare();self.a.stop()
  with self.assertRaises(ValueError):self.a.submit(r,True)

 def test_expiry_bounds_account_and_payload(self):
  from unittest.mock import patch
  r=self.prepare()
  with patch('jarvis.google_sheets_write.time.time',return_value=r['payload']['expires_at']+1):self.a.submit(r,True);self.a.worker.join(3)
  self.assertEqual(self.a.snapshot()['state'],'review');self.assertFalse(any(x[0]=='PUT'for x in self.calls))
  with self.assertRaises(ValueError):self.a.rectangle('Tab','A1:T1',[['a'*1000]*20])
  self.conn.account='other@example.invalid';self.a.submit(r,True);self.a.worker.join(3);self.assertFalse(any(x[0]=='PUT'for x in self.calls))
