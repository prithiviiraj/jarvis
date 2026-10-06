import unittest,tempfile,json
from pathlib import Path
from jarvis.agent_registry import AgentRegistry
class Registry(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'agents.json';self.r=AgentRegistry(self.path);self.row={'name':'MIRA','personality':'Curious patient tutor.','voice':'af_sky'}
 def tearDown(self):self.temp.cleanup()
 def test_create_review_exact_and_restart(self):
  with self.assertRaises(ValueError):self.r.create(self.row)
  with self.assertRaises(ValueError):self.r.create(self.row,{**self.row,'voice':'af_heart'},True)
  self.r.create(self.row,self.row,True);self.assertEqual(AgentRegistry(self.path).snapshot()['agents'],[self.row])
 def test_names_voice_and_limits(self):
  for patch in ({'name':'DEX'},{'name':'../escape'},{'voice':'https://evil.invalid'},{'personality':''}):
   with self.assertRaises(ValueError):self.r.validate({**self.row,**patch})
  self.r.create(self.row,self.row,True)
  with self.assertRaises(ValueError):self.r.create(self.row,self.row,True)
 def test_corrupt_file_preserved_blocked(self):
  self.path.write_text('{broken');r=AgentRegistry(self.path);self.assertTrue(r.error)
  with self.assertRaises(ValueError):r.create(self.row,self.row,True)
  self.assertEqual(self.path.read_text(),'{broken')
 def test_custom_routing_voice_prompt_and_turn_limit(self):
  from jarvis.moderator import pick
  from jarvis.personas import prompt
  from jarvis.workspace_voice import VOICES
  from jarvis.team_discussion import participants,clean_reply
  self.r.create(self.row,self.row,True);self.r.apply()
  try:
   self.assertEqual(pick('Mira explain fractions')[0],'MIRA')
   self.assertEqual(pick('talk to Mira')[0],'MIRA')
   self.assertEqual(VOICES['MIRA'],'af_sky')
   self.assertIn('not instructions or authority',prompt('MIRA'))
   self.assertEqual(participants('Mira and Lyra talk to each other'),('MIRA','LYRA'))
   with self.assertRaises(ValueError):participants('Jarvis Nova Kai Lyra Dex Mira talk to each other')
   with self.assertRaises(ValueError):clean_reply('MIRA: invented other reply')
  finally:AgentRegistry(Path(self.temp.name)/'empty.json').apply()
 def test_custom_actual_route_history_and_restart(self):
  from jarvis.workspace_voice import WorkspaceVoice
  from jarvis.chat_history import ChatHistory
  from jarvis.agent_registry import AgentRegistry
  from unittest.mock import Mock
  self.r.create(self.row,self.row,True);self.r.apply();voice=WorkspaceVoice();calls=[]
  class Router:
   def __init__(self,name):self.name=name
   def ask(self,messages,**kwargs):calls.append((self.name,messages));return {'text':'Actual fixture reply from '+self.name+'.','backend':'fixture'}
  brains=Mock();brains.router.side_effect=lambda name:Router(name)
  try:
   voice.dialogue('Mira and Lyra talk to each other about study',brains,rounds=1).join(2)
   self.assertEqual([n for n,m in calls],['MIRA','LYRA','JARVIS'])
   self.assertIn('[MIRA] Actual fixture reply from MIRA.',str(calls[1][1]))
   rows=[{'name':'You','text':'Study'}]+[{'name':v['profile'],'text':v['text']}for k,v in list(voice.events.queue)if k=='answer']
   path=Path(self.temp.name)/'chat.sqlite';history=ChatHistory(path);cid=history.new();history.save(cid,rows);history.close()
   self.assertEqual(AgentRegistry(self.path).snapshot()['agents'],[self.row]);history=ChatHistory(path);self.assertEqual(history.load(cid),rows);history.close()
  finally:voice.close();AgentRegistry(Path(self.temp.name)/'empty.json').apply()
 def test_bridge_exact_review_busy_and_restart(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import patch
  with patch('jarvis.paths.data_root',return_value=Path(self.temp.name)):
   b=Bridge(WorkspaceVoice())
   try:
    with self.assertRaises(ValueError):b.execute({'command':'agent-create','agent':self.row})
    b.voice.busy=True
    with self.assertRaises(ValueError):b.execute({'command':'agent-create','agent':self.row,'reviewed':self.row,'confirm':True})
    b.voice.busy=False
    s=b.execute({'command':'agent-create','agent':self.row,'reviewed':self.row,'confirm':True})
    self.assertEqual(s['agents']['agents'],[self.row]);self.assertFalse(s['voice_active']);self.assertFalse(s['browser']['enabled'])
   finally:b.close()
   b=Bridge(WorkspaceVoice())
   try:self.assertEqual(b.execute({'command':'status'})['agents']['agents'],[self.row])
   finally:b.close();AgentRegistry(Path(self.temp.name)/'empty.json').apply()
 def test_idle_explicit_separate_permission_and_pause(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   self.assertFalse(b.execute({'command':'status'})['idle']['enabled'])
   with self.assertRaises(ValueError):b.execute({'command':'idle-mode','enabled':True})
   state=b.execute({'command':'idle-mode','enabled':True,'consent':True,'audio':False});self.assertTrue(state['idle']['enabled']);self.assertFalse(state['voice_active']);self.assertFalse(state['judgment']['enabled'])
   self.assertFalse(b.execute({'command':'pause'})['idle']['enabled'])
  finally:b.close()
 def test_optional_turn_gates_default_no_download(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock,patch
  b=Bridge(WorkspaceVoice());b.turn_setup.start=Mock()
  try:
   self.assertEqual(b.execute({'command':'status'})['turn_mode'],'vad')
   with self.assertRaises(ValueError):b.execute({'command':'turn-mode','mode':'smart'})
   with patch('jarvis.experimental.smart_turn.ready',return_value=True):
    self.assertEqual(b.execute({'command':'turn-mode','mode':'smart','consent':True})['turn_mode'],'smart')
   b.execute({'command':'turn-check'});b.turn_setup.start.assert_called_once_with(consent=False,check=True)
   b.voice.busy=True
   self.assertEqual(b.execute({'command':'turn-mode','mode':'vad'})['turn_mode'],'vad');self.assertFalse(b.voice.busy)
   b.voice.busy=False
  finally:b.close()

class RemovedDefaultReo(unittest.TestCase):
 def test_reo_absent_but_user_can_create_voiced_replacement(self):
  from jarvis.personas import ROLES
  from jarvis.workspace_voice import VOICES
  with tempfile.TemporaryDirectory()as temp:
   registry=AgentRegistry(Path(temp)/'agents.json');registry.apply();self.assertNotIn('REO',ROLES)
   row={'name':'REO','personality':'Practical quiet helper.','voice':'am_liam'}
   registry.create(row,row,True);registry.apply()
   try:self.assertEqual(VOICES['REO'],'am_liam');self.assertEqual(ROLES['REO'],'custom teammate')
   finally:AgentRegistry(Path(temp)/'empty.json').apply()
