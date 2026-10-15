import unittest,threading,time
from unittest.mock import Mock,patch
from jarvis.shortcut_keys import ShortcutEdges
from jarvis.runtime import VoiceRuntime
class OwnerInterrupt(unittest.TestCase):
 def test_ctrl_alt_is_immediate_edge_not_hold_in_interrupt_mode(self):
  e=ShortcutEdges(mode='interrupt');self.assertEqual(e.feed(True,True,False,False),['interrupt']);self.assertEqual(e.feed(True,True,False,False),[]);self.assertEqual(e.feed(False,False,False,False),[]);self.assertEqual(e.feed(False,True,True,False),[]);self.assertEqual(e.feed(True,True,False,False),['interrupt'])
 def test_disabled_session_never_starts_capture(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();self.assertFalse(v.interrupt_and_listen());v.mic.resume.assert_not_called();v.mic.start.assert_not_called()
 def test_reply_stops_and_new_utterance_survives_old_worker(self):
  entered=threading.Event();release=threading.Event();done=threading.Event();speaker=Mock();speaker.generation=0;stt=Mock();stt.transcribe.side_effect=lambda audio:'old question'if audio==[1]else'new question';router=Mock()
  def answer(messages,**kw):
   if messages[-1]['content']=='old question':entered.set();release.wait(2);return {'text':'stale old answer'}
   done.set();return {'text':'Fresh current answer.'}
  router.ask.side_effect=answer;speaker.stop.side_effect=lambda:setattr(speaker,'generation',speaker.generation+1)
  v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock();v.enable(True);v.on_utterance([1]);self.assertTrue(entered.wait(1));old=v.cancel;self.assertTrue(v.interrupt_and_listen());speaker.stop.assert_called_once();self.assertTrue(old.is_set());self.assertFalse(v.cancel.is_set());v.on_utterance([2]);self.assertIsNotNone(v.pending_utterance);release.set();self.assertTrue(done.wait(2))
  end=time.monotonic()+2
  while v.busy and time.monotonic()<end:time.sleep(.005)
  self.assertEqual([x['content']for x in v.history],['new question','Fresh current answer.']);self.assertEqual(speaker.speak.call_count,1);self.assertEqual(speaker.speak.call_args.args[0],'Fresh current answer.');v.close()
 def test_stop_discards_deferred_audio(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.enabled=True;v.busy=True;v.interrupt_and_listen();v.on_utterance([2]);v.pause();v.busy=False;v._start_deferred();v.stt.transcribe.assert_not_called();self.assertIsNone(v.pending_utterance)
 def test_bridge_interrupt_mode_reuses_current_session_even_with_groq(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  voice=WorkspaceVoice();bridge=Bridge(voice);runtime=Mock();runtime.enabled=True;runtime.busy=False;runtime.persona='JARVIS';voice.runtime=runtime;voice.stt_route='groq'
  try:
   with patch.object(bridge.shortcut_monitor,'start')as start:
    bridge.execute({'command':'shortcuts-enable','mode':'interrupt','consent':True});start.assert_called_once_with(True,mode='interrupt')
   bridge.shortcut_monitor.enabled=True;bridge.shortcut_monitor.mode='interrupt';bridge.shortcut_events.put('interrupt');bridge.execute({'command':'status'});runtime.interrupt_and_listen.assert_called_once();runtime.mic.start.assert_not_called();bridge.execute({'command':'shortcuts-stop'});self.assertIs(voice.runtime,runtime)
  finally:voice.runtime=None;bridge.close()
