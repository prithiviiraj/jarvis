import unittest
from unittest.mock import Mock,patch
from jarvis.persona_text import speaker_context,own_reply
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.brain_settings import BrainSettings
from jarvis.local_endpoint import bind,unbind

class OwnerPersonaRoutingTests(unittest.TestCase):
 def test_other_speaker_is_quoted_not_self_assistant_history(self):
  rows=[{'role':'user','content':'what do you see?'},{'role':'assistant','content':'[JARVIS] I see a face.'},{'role':'assistant','content':'[DEX] I need a current image.'}]
  out=speaker_context(rows,'DEX')
  self.assertEqual(out[1]['role'],'user');self.assertIn('Historical teammate reply',out[1]['content']);self.assertIn('JARVIS: I see a face.',out[1]['content']);self.assertEqual(out[2],rows[2]);self.assertEqual(rows[1]['role'],'assistant')
 def test_foreign_identity_rejected_but_mentions_allowed(self):
  for text in ["I'm Jarvis.",'I am JARVIS, your team leader.','My name is Lyra.']:
   with self.assertRaises(ValueError):own_reply(text,'DEX')
  self.assertEqual(own_reply('Jarvis can lead while I check the code.','DEX'),'Jarvis can lead while I check the code.')
 def test_typed_dex_receives_own_system_and_quoted_jarvis(self):
  seen=[]
  class Router:
   def select_persona(self,name):self.name=name
   def stream(self,messages,**kw):seen.append((self.name,messages));yield {'text':'I will check the current evidence.','provider':'local'}
  voice=WorkspaceVoice(text_factory=Router);voice.memory.append('JARVIS','what can you see','I saw a face in the previous image.');voice.select('DEX');voice.send_text('what can you see now?').join(2)
  self.assertEqual(seen[0][0],'DEX');self.assertIn('current speaker is DEX',seen[0][1][0]['content']);self.assertEqual(seen[0][1][2]['role'],'user');self.assertIn('Historical teammate reply',seen[0][1][2]['content']);self.assertEqual(voice.memory.snapshot()[-1][0],'DEX')
 def test_owned_session_precedes_cloud_and_wrong_assigned_local(self):
  settings=BrainSettings(Mock());settings.configure([{'id':'slot1','provider':'groq','model':'llama-3.1-8b-instant','enabled':True,'consent':True,'free':True},{'id':'slot5','provider':'local','model':'unrelated-lmstudio','enabled':True}],{'DEX':'slot1'})
  owner=Mock();owner.route.return_value={'model':'owned-qwen','url':'http://127.0.0.1:9999/v1','key':'fixture'};bind(owner)
  try:
   self.assertEqual([(x.provider,x.model)for x in settings.candidates('DEX')],[('local','owned-qwen')]);self.assertEqual(settings.local_candidate('DEX').model,'owned-qwen')
   owner.route.side_effect=ValueError('owned route failed')
   with self.assertRaises(ValueError):settings.candidates('DEX')
  finally:unbind(owner)
 def test_nonstream_voice_foreign_identity_cannot_reach_speaker(self):
  from jarvis.runtime import VoiceRuntime
  stt=Mock();stt.transcribe.return_value='tell me your name';router=Mock();router.ask.return_value={'text':'I am Jarvis.'};speaker=Mock();speaker.generation=1
  runtime=VoiceRuntime(Mock(),stt,router,speaker);runtime.persona='DEX';runtime.mic=Mock();runtime.enable(True);runtime.turn([],runtime.generation,False,[]);speaker.speak.assert_not_called();runtime.close()
 def test_capability_context_uses_actual_browseros_and_managed_state(self):
  from jarvis.ui_bridge import Bridge
  bridge=Bridge(WorkspaceVoice())
  try:
   with patch.object(bridge.browseros,'snapshot',return_value={'state':'connected','busy':False}),patch.object(bridge.managed_session,'snapshot',return_value={'active':True,'status':'ready'}):
    context=bridge.interface_context('browser camera can you see me')
   self.assertIn('BrowserOS own-tab adapter connected',context);self.assertIn('Owned managed model first',context);self.assertIn('Prior teammate image descriptions are historical',context);self.assertIn('Completed voice/text open-browser',context)
  finally:bridge.close()
 def test_visual_question_drops_historical_descriptions_not_just_identity_tags(self):
  from jarvis.vision import LocalVision
  vision=LocalVision(lambda:b'current-jpeg');vision.enabled=True;vision.checked_at=vision.clock()
  history=[{'role':'system','content':'Current speaker DEX'},{'role':'user','content':'what did Jarvis see'},{'role':'assistant','content':'[JARVIS] I see an old imagined face.'},{'role':'user','content':'What can you see on the camera now?'}]
  out=vision.attach(history);self.assertEqual(len(out),2);self.assertEqual(out[0],history[0]);self.assertNotIn('old imagined face',str(out));self.assertEqual(history[2]['role'],'assistant');self.assertIn('current-jpeg',__import__('base64').b64decode(out[-1]['content'][-1]['image_url']['url'].split(',')[1]).decode())
