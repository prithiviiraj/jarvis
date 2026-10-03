"""Deterministic single-persona routing for local typed messages. No model call."""
import re
ROLES={'JARVIS':'team leader','NOVA':'secretary','KAI':'researcher','LYRA':'writer','DEX':'coder'}
KEYWORDS={
 'DEX':r'\b(code|coding|debug|debugging|python|javascript|typescript|function|programming|stacktrace|compiler|sql|git)\b',
 'LYRA':r'\b(write|writing|rewrite|poem|story|script|caption|subtitles|draft|essay)\b',
 'NOVA':r'\b(schedule|calendar|meeting|remind|reminder|appointment|agenda|briefing)\b',
 'KAI':r'\b(research|compare|comparison|investigate|sources|study|learn|explain)\b'}
def pick(text,selected='JARVIS'):
    if not isinstance(text,str) or not text.strip():raise ValueError('Text required')
    if selected not in ROLES:raise ValueError('Unknown selected profile')
    # Only direct address at the start is an explicit persona request.
    m=re.match(r'^\s*(?:hey\s+|hi\s+)?(jarvis|nova|kai|lyra|dex)\b',text,re.I)
    if m:return m.group(1).upper(),'direct address'
    matches=[n for n,pattern in KEYWORDS.items() if re.search(pattern,text,re.I)]
    if len(matches)==1:return matches[0],'topic match'
    return 'JARVIS','general or mixed topic'
