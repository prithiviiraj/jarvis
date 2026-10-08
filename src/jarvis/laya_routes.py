"""Observed rule evidence, not a trained classifier or permission decision."""
from .action_intent import parse,goal
from .desktop_actions import prepare
from .intent_routing import casual
from .multi_address import addressed
def evidence(text,source='typed',endpoint=None,retrieval=None):
 from .decision_layer import assess
 row=assess(text,source,endpoint,retrieval)
 # Preserve original outward labels for established clients/tests.
 if row['state']!='unknown':
  row['state']='rule evidence'
  if row['vault_coverage']=='unknown until exact-query retrieval':row['vault_coverage']='unknown until retrieval'
  if source=='typed':row['speech_complete']='not assessed'
  elif endpoint is None:row['speech_complete']='upstream endpoint, not probability'
 return row
