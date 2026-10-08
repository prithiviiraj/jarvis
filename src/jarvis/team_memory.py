"""Bounded, memory-only shared conversation. No sensor or network access."""
import threading
from .personas import ROLES
class TeamMemory:
    def __init__(self,max_turns=12,max_chars=12000):
        self.lock=threading.RLock();self.turns=[];self.max_turns=max_turns;self.max_chars=max_chars;self.pending=None;self.unanswered=[]
    def append(self,name,user,answer):
        if name not in ROLES:raise ValueError('Unknown profile')
        if not isinstance(user,str) or not isinstance(answer,str):raise ValueError('Text required')
        with self.lock:
            self.pending=None
            prefix='['+name+']'
            while answer.lstrip().startswith(prefix):answer=answer.lstrip()[len(prefix):].lstrip()
            self.turns.append((name,user[:2000],answer[:3000]))
            while len(self.turns)>self.max_turns or (len(self.turns)>1 and sum(len(u)+len(a) for _,u,a in self.turns)>self.max_chars):
                self.turns.pop(0);self.unanswered=[(max(0,index-1),text)for index,text in self.unanswered if index>0]
    def messages(self):
        with self.lock:
            rows=[]
            for index,(name,user,answer)in enumerate(self.turns):
                rows.extend({'role':'user','content':text}for position,text in self.unanswered if position==index)
                rows.extend(({'role':'user','content':user},{'role':'assistant','content':'['+name+'] '+answer}))
            rows.extend({'role':'user','content':text}for position,text in self.unanswered if position>=len(self.turns))
            if self.pending:rows.append({'role':'user','content':self.pending})
            rows=rows[-self.max_turns*2:]
            while len(rows)>1 and sum(len(r['content'])for r in rows)>self.max_chars:rows.pop(0)
            if rows and len(rows[0]['content'])>self.max_chars:rows[0]={**rows[0],'content':rows[0]['content'][-self.max_chars:]}
            return rows
    def snapshot(self):
        with self.lock:return list(self.turns)
    def clear(self):
        with self.lock:self.turns.clear();self.pending=None;self.unanswered=[]

    def restore(self,rows):
        """Keep unmatched visible requests as context, never fabricate completion."""
        with self.lock:
            self.clear();pending=None;answered=False
            for row in rows:
                if row.get('name')=='You':
                    if pending is not None and not answered:self.unanswered.append((len(self.turns),pending))
                    pending=str(row.get('text',''))[:2000];answered=False
                elif pending is not None and row.get('name')in (*ROLES,'NOVA','SILA','REO') and isinstance(row.get('text'),str):
                    
                    name=row['name']
                    if name in ROLES:self.append(name,pending,row['text'])
                    else:self.turns.append((name,pending,row['text'][:3000]));self.turns=self.turns[-self.max_turns:]
                    answered=True
            if pending is not None and not answered:self.pending=pending
            self.unanswered=self.unanswered[-self.max_turns:]
            while self.unanswered and sum(len(t)for _,t in self.unanswered)>self.max_chars:self.unanswered.pop(0)
