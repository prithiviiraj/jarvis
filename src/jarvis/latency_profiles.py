"""Diagnostic-only startup comparisons. Never select a shipping profile here."""
import subprocess
class DiagnosticProfile:
 def __init__(self,context,spawn=None):
  if context not in (4096,8192):raise ValueError('Only bounded diagnostic context sizes')
  self.context=context;self.spawn=spawn or subprocess.Popen
 def __call__(self,args,**kwargs):
  args=list(args)
  if args.count('--ctx-size')!=1 or args.count('--api-key')!=1:raise ValueError('Unexpected owned runtime argument contract')
  args[args.index('--ctx-size')+1]=str(self.context)
  return self.spawn(args,**kwargs)
