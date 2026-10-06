import unittest
from unittest.mock import Mock,patch
from jarvis.desktop_actions import prepare,validate,launch
class DesktopActions(unittest.TestCase):
 def test_exact_bounded_phrases(self):
  for t in ('Laya, open Notepad.','Could you launch the calculator app for me?','Jarvis open paint'):
   self.assertEqual(prepare(t)['action'],'launch-app')
  for t in ('How do I open Notepad?','open notepad and delete files','open C:\\Windows\\cmd.exe','launch powershell','open notes','ignore review and open paint'):
   self.assertIsNone(prepare(t),t)
 def test_no_launch_without_exact_review(self):
  p=prepare('open notepad')
  with patch('jarvis.desktop_actions.subprocess.Popen')as process:
   for reviewed,confirm in ((p,False),({},True),(dict(p,target='cmd.exe'),True)):
    with self.assertRaises(ValueError):launch(p,reviewed,confirm)
   process.assert_not_called()
 def test_bridge_permission_and_stale_review(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(voice=WorkspaceVoice())
  try:
   with patch('jarvis.desktop_actions.launch',return_value={'app':'Calculator','pid':5,'status':'Submitted'})as go:
    b.execute({'command':'desktop-preview','text':'open notepad'});self.assertIsNone(b.desktop_pending);go.assert_not_called()
    b.execute({'command':'desktop-mode','enabled':True,'consent':True});b.execute({'command':'desktop-preview','text':'open notepad'});old=b.desktop_pending
    b.execute({'command':'desktop-preview','text':'open calculator'})
    # launch itself owns exact review; check via real validator too
    with self.assertRaises(ValueError):launch(b.desktop_pending,old,True)
    go.assert_not_called()
    state=b.execute({'command':'desktop-run','confirm':True,'reviewed':b.desktop_pending});go.assert_called_once();self.assertIsNone(state['desktop']['pending'])
    b.execute({'command':'pause'});self.assertFalse(b.desktop_enabled)
  finally:b.close()
