"""Reviewed game-comment output only. No microphone, download or cloud."""
import threading
class GameSpeech:
 def __init__(self,game,factory,notify=lambda *a:None):self.game=game;self.factory=factory;self.notify=notify;self.speaker=None;self.busy=False;self.generation=0;self.lock=threading.RLock();self.status='Off'
 def stop(self):
  with self.lock:self.generation+=1;self.status='Stopped';speaker=self.speaker
  if speaker:speaker.stop()
 def close(self):
  self.stop()
  if self.speaker and hasattr(self.speaker,'close'):self.speaker.close()
  self.speaker=None
 def play(self,row,conversation_busy=False):
  if conversation_busy or row.get('audio')is not True or not row.get('comment'):return None
  with self.lock:
   if self.busy or not self.game.enabled or not self.game.audio or row.get('generation')!=self.game.generation:return None
   ticket=self.generation;game_ticket=self.game.generation;self.busy=True;self.status='Preparing reviewed game speech'
  def valid():return ticket==self.generation and self.game.enabled and self.game.audio and game_ticket==self.game.generation
  def work():
   candidate=None
   try:
    candidate=self.speaker or self.factory()
    with self.lock:
     if not valid():candidate.stop();return
     self.speaker=candidate;voice_ticket=candidate.generation;self.status='Game speech output only'
     candidate.playback_event=lambda event,text,actor,sr,n:self.notify('speech-caption',{'active':event=='start','name':'JARVIS','text':text,'duration_s':n/sr if sr else 0,'at':__import__('time').monotonic()})
    from .persona_text import spoken_text
    text=spoken_text(row['comment'])
    if text.strip() and valid():candidate.speak(text,generation=voice_ticket)
   except Exception:self.status='Game speech unavailable; no download or cloud fallback'
   finally:
    with self.lock:self.busy=False
  t=threading.Thread(target=work,daemon=True);t.start();return t
