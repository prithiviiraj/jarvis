import unittest,base64,email
from jarvis.google_mail_draft import encode,plain_message
from jarvis.connector_workflows import email_plan
class Tests(unittest.TestCase):
 def test_exact_unicode_and_header_draft(self):
  p=email_plan('owner@example.com',['friend@example.com'],'Tamil வணக்கம்','Exact $50 and "words"\nSecond line',cc=['copy@example.com']);r=encode(p);msg=email.message_from_bytes(base64.urlsafe_b64decode(r['raw']+'='*(-len(r['raw'])%4)),policy=email.policy.default);self.assertEqual(msg['To'],'friend@example.com');self.assertEqual(msg['Cc'],'copy@example.com');self.assertEqual(msg.get_content(),'Exact $50 and "words"\r\nSecond line\r\n');self.assertIsNone(msg['Bcc'])
  p['payload']['body']='changed'
  with self.assertRaises(ValueError):encode(p)
 def row(self):return {'id':'observed','labelIds':['SENT'],'payload':{'mimeType':'text/plain','headers':[{'name':'To','value':'Friend <friend@example.com>'},{'name':'Subject','value':'Subject'}],'body':{'data':base64.urlsafe_b64encode(b'Exact body\r\n').decode()}}}
 def test_read_complete_plain_and_attachments_incomplete(self):
  row=self.row();r=plain_message(row,'owner@example.com');self.assertTrue(r['complete']);self.assertEqual(r['body'],'Exact body\n');self.assertEqual(r['to'],['friend@example.com']);row['payload']['filename']='attachment.txt';r=plain_message(row,'owner@example.com');self.assertFalse(r['complete']);self.assertFalse(r['attachments'][0]['downloaded'])
 def test_duplicate_header_html_or_bad_body_incomplete(self):
  row=self.row();row['payload']['headers'].append({'name':'To','value':'other@example.com'});self.assertFalse(plain_message(row,'owner@example.com')['complete']);row=self.row();row['payload']['mimeType']='text/html';self.assertFalse(plain_message(row,'owner@example.com')['complete']);row=self.row();row['payload']['body']['data']='%%%';self.assertFalse(plain_message(row,'owner@example.com')['complete'])
