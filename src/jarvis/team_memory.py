"""Bounded, memory-only shared conversation. No sensor or network access."""
import threading
from .personas import ROLES
class TeamMemory:
    def __init__(self,max_turns=12,max_chars=12000):
        self.lock=threading.RLock();self.turns=[];self.max_turns=max_turns;self.max_chars=max_chars
    def append(self,name,user,answer):
        if name not in ROLES:raise ValueError('Unknown profile')
        if not isinstance(user,str) or not isinstance(answer,str):raise ValueError('Text required')
        with self.lock:
            prefix='['+name+']'
            while answer.lstrip().startswith(prefix):answer=answer.lstrip()[len(prefix):].lstrip()
            self.turns.append((name,user[:2000],answer[:3000]));self.turns=self.turns[-self.max_turns:]
            while len(self.turns)>1 and sum(len(u)+len(a) for _,u,a in self.turns)>self.max_chars:self.turns.pop(0)
    def messages(self):
        with self.lock:
            return [m for name,user,answer in self.turns for m in ({'role':'user','content':user},{'role':'assistant','content':'['+name+'] '+answer})]
    def snapshot(self):
        with self.lock:return list(self.turns)
    def clear(self):
        with self.lock:self.turns.clear()

    def restore(self,rows):
        """Restore all actual team speakers after each user, within normal bounds."""
        self.clear();pending=None
        for row in rows:
            if row['name']=='You':pending=row['text']
            elif pending is not None:self.append(row['name'],pending,row['text'])
