import io,json,unittest
from unittest.mock import Mock
from jarvis.vision import LocalVision

def opener(models):
    class Resp(io.BytesIO):
        def __enter__(self):return self
        def __exit__(self,*a):self.close()
        headers={}
    class Opener:
        def open(self,url,timeout=8):
            assert url.endswith('/api/v1/models')
            return Resp(json.dumps({'models':models}).encode())
    return Opener()
VISION=[{'key':'qwen2.5-vl-3b-instruct','capabilities':{'vision':True},'loaded_instances':[{'id':'qwen2.5-vl-3b-instruct'}]}]
PLAIN=[{'key':'text-only-model','capabilities':{'vision':False},'loaded_instances':[]}]

class LocalVisionTests(unittest.TestCase):
 def test_consent_required(self):
    with self.assertRaises(ValueError):LocalVision(lambda:b'x',opener=opener(VISION)).enable()
 def test_refuses_non_vision_model(self):
    v=LocalVision(lambda:b'x',opener=opener(PLAIN))
    with self.assertRaisesRegex(RuntimeError,'does not advertise vision'):v.enable(consent=True)
    self.assertFalse(v.enabled)
 def test_attach_adds_current_frame_as_data_url(self):
    v=LocalVision(lambda:b'jpeg-bytes',opener=opener(VISION));v.enable(consent=True)
    out=v.attach([{'role':'system','content':'s'},{'role':'user','content':'what do you see'}])
    content=out[-1]['content'];self.assertEqual(content[0],{'type':'text','text':'what do you see'})
    self.assertEqual(content[1]['type'],'image_url');self.assertTrue(content[1]['image_url']['url'].startswith('data:image/jpeg;base64,'))
    self.assertEqual(out[0]['content'],'s')
 def test_no_attach_when_disabled_or_no_frame(self):
    msgs=[{'role':'user','content':'hi'}]
    self.assertIs(LocalVision(lambda:b'x',opener=opener(VISION)).attach(msgs),msgs)
    v=LocalVision(lambda:None,opener=opener(VISION));v.enable(consent=True);self.assertIs(v.attach(msgs),msgs)
 def test_reverify_after_cache_expiry(self):
    clock=[0.0];v=LocalVision(lambda:b'x',opener=opener(VISION),clock=lambda:clock[0],recheck_seconds=15);v.enable(consent=True)
    v.opener=opener(PLAIN);clock[0]=20.0
    with self.assertRaisesRegex(RuntimeError,'no longer advertises vision'):v.attach([{'role':'user','content':'hi'}])
 def test_oversize_frame_dropped(self):
    v=LocalVision(lambda:b'x'*300001,opener=opener(VISION));v.enable(consent=True)
    msgs=[{'role':'user','content':'hi'}];self.assertIs(v.attach(msgs),msgs)

class VisionWiringTests(unittest.TestCase):
 def test_ui_bridge_command_flow(self):
    from jarvis.ui_bridge import Bridge
    from jarvis.workspace_voice import WorkspaceVoice
    b=Bridge(WorkspaceVoice())
    try:
        self.assertEqual(b.execute({'command':'status'})['awareness']['vision'],'off')
        with self.assertRaises(ValueError):b.execute({'command':'camera-vision','consent':True})
        with self.assertRaises(ValueError):
            b.context.camera_state('on');b.execute({'command':'camera-vision'})
        b.vision.enable=Mock();b.execute({'command':'camera-vision','consent':True});b.vision.enable.assert_called_once_with(consent=True)
        b.vision.enabled=True
        self.assertEqual(b.execute({'command':'status'})['awareness']['vision'],'on')
        b.execute({'command':'camera-vision','enabled':False});self.assertFalse(b.vision.enabled)
    finally:b.close()
 def test_runtime_attaches_frame_and_survives_failure(self):
    from jarvis.runtime import VoiceRuntime
    stt=Mock();stt.transcribe.return_value='what do you see';router=Mock();router.ask.return_value={'text':'I see a desk.'};speaker=Mock();speaker.generation=1
    v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock()
    class FakeVision:
        def attach(self,messages):
            m=[dict(x) for x in messages];m[-1]['content']=[{'type':'text','text':m[-1]['content']},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,AA'}}];return m
    v.vision=FakeVision();v.enable(True);v.turn([0],v.generation,False,[])
    content=router.ask.call_args.args[0][-1]['content'];self.assertEqual(content[1]['type'],'image_url')
    speaker.speak.assert_called_once()
 def test_runtime_vision_failure_continues_text_only(self):
    from jarvis.runtime import VoiceRuntime
    stt=Mock();stt.transcribe.return_value='hi';router=Mock();router.ask.return_value={'text':'hello'};speaker=Mock();speaker.generation=1
    v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock()
    bad=Mock();bad.attach.side_effect=RuntimeError('model changed');v.vision=bad
    v.enable(True);v.turn([0],v.generation,False,[])
    self.assertEqual(router.ask.call_args.args[0][-1]['content'],'hi')

class LoadedVisionContractTests(unittest.TestCase):
 def test_downloaded_vision_is_not_loaded(self):
  v=LocalVision(lambda:b'x',opener=opener([{'type':'llm','key':'vision','capabilities':{'vision':True},'loaded_instances':[]}]))
  with self.assertRaises(RuntimeError):v.enable(True)
 def test_several_loaded_instances_refused(self):
  v=LocalVision(lambda:b'x',opener=opener([{'type':'llm','key':'vision','capabilities':{'vision':True},'loaded_instances':[{'id':'one'},{'id':'two'}]}]))
  with self.assertRaisesRegex(RuntimeError,'exactly one'):v.enable(True)
