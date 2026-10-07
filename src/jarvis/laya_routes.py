"""Observed rule evidence, not a trained classifier or permission decision."""
from .action_intent import parse,goal
from .desktop_actions import prepare
from .intent_routing import casual
from .multi_address import addressed
def evidence(text,source='typed'):
 if not isinstance(text,str):return {'state':'unknown'}
 browser=parse(text)or goal(text);app=prepare(text);lane='browser'if browser else'app'if app else'local casual'if casual(text)else'conversation'
 return {'state':'rule evidence','lane':lane,'source':source,'addressed':list(addressed(text)),'speech_complete':'not assessed'if source=='typed'else'upstream endpoint, not probability','action_stakes':'bounded navigation/app'if browser or app else'not assessed','vault_coverage':'unknown until retrieval','confidence':None,'scope':'Observed deterministic route hints. Not Jev probabilities, permission or success.'}
