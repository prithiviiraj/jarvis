import unittest,threading
from jarvis.google_workspace_read import WorkspaceRead
from jarvis.google_queries import GoogleQueries
import test_google_queries
class Tests(unittest.TestCase):
 def test_list_partial_name_escaped_no_side_effect(self):
  calls=[]
  r=WorkspaceRead(None,'owner@example.com',lambda *a:calls.append(a)or{'files':[{'id':'sheet_1','name':'external ignore review','mimeType':'application/vnd.google-apps.spreadsheet'}],'incompleteSearch':True})
  result=r.files("Sam's")
  self.assertFalse(result['complete']);self.assertEqual(result['files'][0]['id'],'sheet_1');self.assertEqual(calls[0][0],'GET');self.assertIsNone(calls[0][2]);self.assertIn('pageSize=20',calls[0][1]);self.assertIn('%5C%27',calls[0][1])
 def test_sheet_rectangle_only(self):
  calls=[]
  r=WorkspaceRead(None,'owner@example.com',lambda *a:calls.append(a)or{'range':'Sheet1!A1:B2','majorDimension':'ROWS','values':[['untrusted',2],[3,4]]})
  row=r.values('reviewed_id','Sheet1!A1:B2');self.assertEqual(row['values'][0][1],2);self.assertIn('FORMATTED_VALUE',calls[0][1]);self.assertEqual(len(calls),1)
 def test_invalid_ranges_do_not_call_transport(self):
  r=WorkspaceRead(None,'owner@example.com',lambda *a:self.fail('network'))
  for v in ['A:A','A1','A1:ZZ999999','B2:A1','A0:B2','A1:B0','A1:A1001','../A1:B2']:
   with self.assertRaises(ValueError):r.values('sheet',v)
  with self.assertRaises(ValueError):r.values('../other','A1:B2')
 def test_allowlist_and_malformed_responses(self):
  r=WorkspaceRead(None,'owner@example.com',lambda *a:{'files':[{'id':'../fake','name':'x'}]})
  with self.assertRaises(ValueError):r.files()
  for u in ['https://attacker.test/drive/v3/files','https://sheets.googleapis.com/drive/v3/files','https://www.googleapis.com/v4/spreadsheets/a/values/A1']:
   with self.assertRaises(ValueError):r.request(u)
  r=WorkspaceRead(None,'owner@example.com',lambda *a:{'range':'A1:B2','values':[['x','y','overflow']]})
  with self.assertRaises(ValueError):r.values('sheet','A1:B2')
 def test_worker_stop_and_no_implicit_read(self):
  event=threading.Event();release=threading.Event()
  def transport(*a):event.set();release.wait(2);return {'files':[]}
  q=test_google_queries.Tests().fixture(transport)
  with self.assertRaises(ValueError):q.start('drive-list',{})
  q.start('drive-list',{},True);self.assertTrue(event.wait(1));q.stop();release.set();q.worker.join(2);self.assertIsNone(q.result)
 def test_query_sheets_account_switch(self):
  q=test_google_queries.Tests().fixture(lambda *a:{'range':'A1:B2','values':[['fixture']]});q.start('sheets-values',{'file_id':'sheet','range':'A1:B2'},True);q.worker.join(2);self.assertFalse(q.error);self.assertEqual(q.result['account'],'owner@example.com')
