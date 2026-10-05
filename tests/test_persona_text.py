import unittest
from jarvis.persona_text import strip_speaker_tag,SpokenTextFilter,spoken_text,spoken_chunks
from jarvis.moderator import pick
from jarvis.personas import prompt,ROLES
class SpeakerTagTests(unittest.TestCase):
 def test_strips_own_and_foreign_leading_tags(self):
  self.assertEqual(strip_speaker_tag('[JARVIS] Hello master.'),'Hello master.')
  self.assertEqual(strip_speaker_tag('[nova]: hi there'),'hi there')
  self.assertEqual(strip_speaker_tag('[NOVA][JARVIS] double label'),'double label')
  self.assertEqual(strip_speaker_tag('  [LYRA] - spaced'),'spaced')
 def test_keeps_other_brackets_and_mid_text_tags(self):
  self.assertEqual(strip_speaker_tag('[thinking] about it'),'[thinking] about it')
  self.assertEqual(strip_speaker_tag('she said [NOVA] mid sentence'),'she said [NOVA] mid sentence')
 def test_non_string_passthrough(self):
  self.assertIsNone(strip_speaker_tag(None))
class SpokenTextFilterTests(unittest.TestCase):
 def test_removes_bracketed_aside(self):
  self.assertEqual(spoken_text('Master, your report is ready. [adjusts glasses dramatically] Shall I continue?'),'Master, your report is ready.  Shall I continue?')
 def test_chunk_boundaries(self):
  f=SpokenTextFilter();parts=[f.feed('Hello [dram'),f.feed('atic pause] master'),f.feed('',True)]
  self.assertEqual(''.join(parts),'Hello  master')
 def test_unclosed_bracket_never_spoken(self):
  f=SpokenTextFilter();out=f.feed('good answer [unfinished aside');out+=f.feed('',True)
  self.assertEqual(out,'good answer ')
 def test_non_bracket_text_untouched(self):
  self.assertEqual(spoken_text('plain reply with (parens)'),'plain reply with (parens)')
 def test_spoken_chunks_stream(self):
  self.assertEqual(''.join(spoken_chunks(iter(['yes [x','] no']))),'yes  no')
class ModeratorAddressTests(unittest.TestCase):
 def test_talk_with_persona_routes_to_that_persona(self):
  self.assertEqual(pick('I want to talk with NOVA')[0],'NOVA')
  self.assertEqual(pick('Can I speak to jarvis about dinner')[0],'JARVIS')
  self.assertEqual(pick('let me chat with lyra')[0],'LYRA')
 def test_existing_patterns_still_work(self):
  self.assertEqual(pick('Hey NOVA, debug this code')[0],'NOVA')
  self.assertEqual(pick('What did NOVA say?')[0],'JARVIS')
class PersonaPromptTests(unittest.TestCase):
 def test_grounded_apology_rule_present(self):
  for name in ROLES:
   text=prompt(name)
   self.assertIn('check the supplied conversation for your actual mistake',text)
   self.assertIn('ask master which reply or action he means',text)
 def test_bracket_aside_rule_present(self):
  for name in ROLES:
   text=prompt(name)
   self.assertIn('never spoken aloud',text)
   self.assertIn('Never put reasoning, instructions or scaffolding in brackets',text)
 def test_jarvis_loyalty_and_friction(self):
  text=prompt('JARVIS')
  self.assertIn('loyal',text.lower())
  self.assertIn('never admiration',text)
  self.assertIn('soft spot',text)
