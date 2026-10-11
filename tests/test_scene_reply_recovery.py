import unittest,json,io,threading
from unittest.mock import Mock
from jarvis.game_companion import LocalGameModel,scene_reply,VisionReplyUnavailable
class Reply(unittest.TestCase):
 def raw(self,text):return json.dumps({'choices':[{'message':{'content':text}}]}).encode()
 def row(self):return {'observed':'Visible scene','comment':'Optional model words','confidence':'medium'}
 def test_plain_fenced_and_text_parts(self):
  for text in (json.dumps(self.row()),'```json\n'+json.dumps(self.row())+'\n```',[{'type':'text','text':json.dumps(self.row())}]):self.assertEqual(scene_reply(self.raw(text)),self.row())
 def test_empty_invalid_extra_fields_rejected(self):
  for text in ('','\n\n','explanation',json.dumps(dict(self.row(),command='send'))):
   with self.assertRaises(ValueError):scene_reply(self.raw(text))
 def test_format_retry_once_and_schema_timeout(self):
  class R(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  op=Mock();op.open.side_effect=[R(self.raw('')),R(self.raw(json.dumps(self.row())))];m=LocalGameModel('tiny',op);m.verify=Mock();self.assertEqual(m.analyze(b'jpeg'),self.row());self.assertEqual(op.open.call_count,2)
  req=op.open.call_args.args[0];d=json.loads(req.data);self.assertEqual(d['max_tokens'],384);self.assertEqual(d['response_format']['type'],'json_schema');self.assertEqual(op.open.call_args.kwargs['timeout'],30)
 def test_invalid_twice_friendly_pause_error(self):
  class R(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  op=Mock();op.open.side_effect=lambda *a,**k:R(self.raw(''));m=LocalGameModel('tiny',op);m.verify=Mock()
  with self.assertRaisesRegex(VisionReplyUnavailable,'twice'):m.analyze(b'jpeg')
  self.assertEqual(op.open.call_count,2)
 def test_timeout_not_retried_blindly(self):
  op=Mock();op.open.side_effect=TimeoutError();m=LocalGameModel('tiny',op);m.verify=Mock()
  with self.assertRaisesRegex(VisionReplyUnavailable,'timed out'):m.analyze(b'jpeg')
  self.assertEqual(op.open.call_count,1)
 def test_discovery_loss_friendly_recoverable(self):
  m=LocalGameModel('tiny',Mock());m.verify=Mock(side_effect=ValueError('unloaded'))
  with self.assertRaisesRegex(VisionReplyUnavailable,'no longer available'):m.analyze(b'jpeg')
