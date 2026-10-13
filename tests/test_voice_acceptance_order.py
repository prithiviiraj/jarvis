import unittest
from jarvis.voice_acceptance import validate_turn_evidence
class VoiceAcceptanceOrder(unittest.TestCase):
 def evidence(self):
  metrics={'stt_s':1,'first_text_s':3,'first_output_write_s':6,'turn_s':7,'scope':'not sound heard'}
  captions=[{'event':'start','text':'Hello. I am ready when you are.','persona':'JARVIS','at':5},{'event':'finish','text':'','persona':'JARVIS','at':7}]
  outputs=[{'event':'first-write','at':6,'elapsed_s':6}]
  return metrics,captions,outputs
 def test_reply_caption_pcm_order_valid(self):validate_turn_evidence(*self.evidence(),'JARVIS')
 def test_earlier_model_text_valid(self):
  m,c,o=self.evidence();m['first_text_s']=1.5;validate_turn_evidence(m,c,o,'JARVIS')
 def test_each_missing_metric_rejected(self):
  for key in ('stt_s','first_text_s','first_output_write_s','turn_s'):
   with self.subTest(key=key):
    m,c,o=self.evidence();del m[key]
    with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_bad_metrics_rejected(self):
  for key,value in [('stt_s',4),('first_text_s',8),('first_output_write_s',.5),('turn_s',1),('stt_s',float('nan')),('stt_s',True)]:
   with self.subTest(key=key,value=value):
    m,c,o=self.evidence();m[key]=value
    with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_missing_or_wrong_ack_and_reply_rejected(self):
  for index,text in [(0,'On it.'),(0,'Wrong reply')]:
   m,c,o=self.evidence();c[index]['text']=text
   with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_persona_and_missing_finish_rejected(self):
  m,c,o=self.evidence();c[0]['persona']='LYRA'
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
  m,c,o=self.evidence();c.pop()
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_missing_or_outside_caption_pcm_write_rejected(self):
  m,c,o=self.evidence();o.pop()
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
  m,c,o=self.evidence();o[0]['at']=8
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_pcm_after_caption_end_rejected(self):
  m,c,o=self.evidence();c[1]['at']=5.5
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
 def test_reply_pcm_before_model_text_rejected(self):
  m,c,o=self.evidence();o[0]['elapsed_s']=2
  with self.assertRaises(AssertionError):validate_turn_evidence(m,c,o,'JARVIS')
