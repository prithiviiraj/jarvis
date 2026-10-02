"""Bounded requests. Reasoning is never used as a final answer or spoken aloud."""
def payload(model,messages,stream=False,max_tokens=300):
    data={'model':model,'messages':messages,'stream':stream}
    if model in ('openai/gpt-oss-20b','openai/gpt-oss-120b'):
        data.update(max_completion_tokens=1024,reasoning_effort='low',include_reasoning=False)
    else:data['max_tokens']=max_tokens
    return data

def reply_metadata(data):
    choice=data['choices'][0];reason=choice.get('finish_reason')
    meta={'finish_category':reason if reason in ('stop','length','tool_calls','content_filter') else 'unknown'}
    usage=data.get('usage',{})
    if isinstance(usage,dict):
        details=usage.get('completion_tokens_details',{})
        for label,value in [('completion_tokens',usage.get('completion_tokens')),('reasoning_tokens',details.get('reasoning_tokens') if isinstance(details,dict) else None)]:
            if type(value) is int and 0<=value<=1000000:meta[label]=value
    return meta
