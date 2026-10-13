"""Deterministic voice guards and safe metadata. No models or media access."""
import re
from .persona_text import strip_speaker_tag

def safe_route(value):
 return {k:v for k,v in value.items()if k in ('provider','model','slot')and isinstance(v,str)and re.fullmatch(r'[A-Za-z0-9_./:@+-]{1,200}',v)and not re.search(r'(?:^sk-|^gsk_|^AIza|bearer|password|secret|token=|://)',v,re.I)}

def normalized(text):return re.sub(r'[^\w]+',' ',text.casefold()).strip()

def echo_reply(answer,question):
 answer=strip_speaker_tag(answer).strip();question=question.strip()
 # Reject only an exact whole-question echo, never quotes inside a useful answer.
 return len(question.split())>=3 and normalized(answer)==normalized(question)

def camera_question(text):return bool(re.search(r'\b(?:what (?:do|can) you see|can you see(?: me)?|look at me|see through (?:the )?camera)\b',text,re.I))

def vision_unavailable(vision,text):
 if camera_question(text)and vision is not None and getattr(vision,'enabled',None)is False and getattr(vision,'screen_enabled',False)is False:
  return 'I cannot see a camera image right now. Camera permission alone is not vision. The camera and a ready vision model must both be on. No image was sent.'
 return None

def runtime_device_scope(stt,speaker):
 stt_name=type(stt).__name__;speaker_name=type(speaker).__name__
 return {'stt_backend':'faster-whisper CPU int8 / 2 threads'if stt_name=='WhisperSTT'else'Groq remote transcription'if stt_name=='GroqSTT'else'controlled-or-unknown','speech_backend':'Kokoro ONNX CPU / 2 threads'if speaker_name=='KokoroSpeaker'else'controlled-or-unknown','answer_device':'Not verified. GPU presence and requested offload are not inference proof.'}
