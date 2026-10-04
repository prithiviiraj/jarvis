"""Model output is never permission. Explicit deterministic narrow read-only scope."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ReadScope:
 goal:str
 allowed_operations:tuple
 page_ready:bool
 observed_link_ids:tuple

def gate(scope,proposal):
 if not isinstance(scope,ReadScope)or not scope.goal.strip():raise ValueError('Explicit scoped owner goal required')
 if not isinstance(scope.allowed_operations,tuple)or any(x not in ('CLICK','SCROLL_DOWN','SCROLL_UP','WAIT')for x in scope.allowed_operations):raise ValueError('Only narrow read-only proposals supported')
 if getattr(proposal,'executed',False)or not getattr(proposal,'needs_review',False):raise ValueError('Model cannot claim execution or bypass review')
 op=proposal.operation
 if op not in scope.allowed_operations:raise ValueError('Operation outside owner scope')
 if op!='WAIT'and scope.page_ready is not True:raise ValueError('Page is not ready')
 if op=='CLICK':
  if not isinstance(scope.observed_link_ids,tuple)or proposal.target_id not in scope.observed_link_ids:raise ValueError('No current safe observed link target')
  # Caller still must bind this ID to fresh exact HTTPS href and show owner review.
 elif proposal.target_id is not None:raise ValueError('Unexpected target')
 return {'operation':op,'target_id':proposal.target_id,'needs_review':True,'executed':False}
