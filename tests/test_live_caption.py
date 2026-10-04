import unittest,time
from unittest.mock import Mock
from jarvis.experimental.kokoro_speaker import KokoroSpeaker
from jarvis.ui_bridge import Bridge
class CaptionTests(unittest.TestCase):
 def test_caption_is_actual_clean_synth_text_after_start(self):
  events=[];synth=Mock();out=Mock();synth.synthesize.return_value=([.2]*1200,24000);synth.synthesize.side_effect=lambda text:(events.append(('synth',text))or ([.2]*1200,24000));out.start.side_effect=lambda:events.append(('output-start',));s=KokoroSpeaker(synth,lambda sr:out);s.profile='NOVA';s.playback_event=lambda *a:events.append(a);s.speak('[NOVA] **Hi** 👋');self.assertEqual(events[0],('synth','Hi'));self.assertEqual(events[1],('output-start',));self.assertEqual(events[2][:3],('start','Hi','NOVA'));self.assertEqual(events[-1][0],'finish')
 def test_no_caption_if_pause_during_synthesis(self):
  synth=Mock();s=KokoroSpeaker(synth,Mock());events=[];s.playback_event=lambda *a:events.append(a);synth.synthesize.side_effect=lambda t:(s.stop()or ([.2],24000));s.speak('stale');self.assertFalse(any(x[0]=='start'for x in events))
 def test_write_failure_clears_caption(self):
  synth=Mock();synth.synthesize.return_value=([.2],24000);out=Mock();out.write.side_effect=RuntimeError();s=KokoroSpeaker(synth,lambda sr:out);events=[];s.playback_event=lambda *a:events.append(a)
  with self.assertRaises(RuntimeError):s.speak('Hi')
  self.assertEqual(events[-1][0],'finish')
 def test_bridge_caption_expiration_and_pause_clear(self):
  b=Bridge()
  try:
   b.voice.notify('speech-caption',{'active':True,'name':'NOVA','text':'Actual spoken text','duration_s':4,'at':time.monotonic()});state=b.execute({'command':'status'});self.assertEqual(state['caption']['name'],'NOVA');self.assertTrue(state['caption']['active']);b.caption['expires']=0;self.assertFalse(b.execute({'command':'status'})['caption']['active'])
   b.voice.notify('speech-caption',{'active':True,'name':'DEX','text':'Stale','duration_s':4,'at':time.monotonic()});self.assertFalse(b.execute({'command':'pause'})['caption']['active'])
   b.voice.notify('speech-caption',{'active':True,'name':'DEX','text':'Stale','duration_s':1,'at':time.monotonic()-10});self.assertFalse(b.execute({'command':'status'})['caption']['active'])
  finally:b.close()
 def test_persona_respects_owner_hierarchy_and_negation(self):
  from jarvis.personas import prompt
  p=prompt('JARVIS');self.assertIn('user defines',p);self.assertIn('Read negation',p);self.assertNotIn('say yes',p);self.assertIn('inside the JARVIS app team',p)
