import pathlib,tempfile,types,unittest
from jarvis.github_issue import GitHubIssue
from jarvis.notion_text import NotionText
from jarvis.google_sheets_write import SheetsWrite
from jarvis.drive_text import DriveText
class Tests(unittest.TestCase):
 def test_invalid_ledger_status_fail_closed_does_not_break_bridge_status(self):
  with tempfile.TemporaryDirectory()as folder:
   p=pathlib.Path(folder)/'broken.json';p.write_text('{bad')
   for cls in (GitHubIssue,NotionText,SheetsWrite,DriveText):
    a=cls(types.SimpleNamespace(),p);s=a.snapshot();self.assertEqual(s['state'],'blocked');self.assertIsNone(s['plan']);self.assertIn('Preserve',s['error']);self.assertEqual(p.read_text(),'{bad')
    with self.assertRaises(ValueError):a.journal()
