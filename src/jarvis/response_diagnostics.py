"""Bounded in-memory response metadata. Never retain prompt/output/audio/keys."""
import re
SAFE_PARTS={'text','output_text','input_text','image_url','image','audio','reasoning','thinking','tool_call','tool_calls'}
class ResponseDiagnostics:
 def __init__(self,model,attempt,mode):
  # Identifiers are not prose. Refuse arbitrary strings rather than copying them.
  self.data={'attempt':attempt,'mode':mode,'model':model if isinstance(model,str) and re.fullmatch(r'[A-Za-z0-9_./:@+-]{1,200}',model) else 'redacted','completion_limit':1024 if isinstance(model,str) and 'spark-x2.5' in model.lower() else 300,'response_category':'not_received','content_type':'unknown','recognized_text_chars':0,'content_value_types':[],'part_types':[],'finish_reason':'unknown','reasoning_fields':[],'reasoning_chars':0,'usage':{}}
 def header(self,value):
  self.data['content_type']='sse' if 'text/event-stream' in value.lower() else 'json' if 'application/json' in value.lower() else 'other'
 def observe(self,event):
  if not isinstance(event,dict):return
  if 'error' in event:self.data['response_category']='api_error'
  elif self.data['response_category']=='not_received':self.data['response_category']='parsed'
  usage=event.get('usage')
  if isinstance(usage,dict):
   for key in ('prompt_tokens','completion_tokens','total_tokens'):
    value=usage.get(key)
    if type(value)is int and 0<=value<=1000000:self.data['usage'][key]=value
   detail=usage.get('completion_tokens_details')
   if isinstance(detail,dict) and type(detail.get('reasoning_tokens'))is int and 0<=detail['reasoning_tokens']<=1000000:self.data['usage']['reasoning_tokens']=detail['reasoning_tokens']
  choices=event.get('choices')
  if not isinstance(choices,list)or not choices:return
  choice=choices[0]
  if not isinstance(choice,dict):return
  reason=choice.get('finish_reason')
  if reason in ('stop','length','tool_calls','content_filter'):self.data['finish_reason']=reason
  message=choice.get('delta') or choice.get('message') or {}
  if not isinstance(message,dict):return
  for field in ('reasoning','reasoning_content','thinking'):
   value=message.get(field)
   if isinstance(value,str)and value:
    if field not in self.data['reasoning_fields']:self.data['reasoning_fields'].append(field)
    self.data['reasoning_chars']=min(1000000,self.data['reasoning_chars']+len(value))
  content=message.get('content');kind='null'if content is None else'string'if isinstance(content,str)else'list'if isinstance(content,list)else'other'
  if kind not in self.data['content_value_types']:self.data['content_value_types'].append(kind)
  if isinstance(content,list):
   for part in content[:32]:
    label=part.get('type')if isinstance(part,dict)else None
    label=label if isinstance(label,str)and label in SAFE_PARTS else'unknown'
    if label not in self.data['part_types']:self.data['part_types'].append(label)
  from .chat_payload import answer_text
  self.data['recognized_text_chars']=min(12001,self.data['recognized_text_chars']+len(answer_text(content)))
  # Field presence only; never copy tool names, arguments or reasoning.
  if (any(message.get(k)for k in ('reasoning','reasoning_content','thinking')) or isinstance(content,str)and any(t in content.lower()for t in ('<think>','<analysis>'))) and not self.data['recognized_text_chars']:self.data['response_category']='reasoning_without_final_text'
  elif message.get('tool_calls') and not self.data['recognized_text_chars']:self.data['response_category']='tools_without_final_text'
 def snapshot(self):
  import copy
  result=copy.deepcopy(self.data)
  if result['recognized_text_chars'] and result['response_category']!='api_error':result['response_category']='final_text'
  elif result['reasoning_chars']and result['response_category']!='api_error':result['response_category']='reasoning_without_final_text'
  elif result['response_category']=='parsed'and not result['recognized_text_chars']:
   result['response_category']='unrecognized_content_parts'if any(p!='text'for p in result['part_types'])else'no_final_text'
  return result
