"""Validate the real frozen newline protocol, including setup progress before reply."""
import json,subprocess,sys

def validate(lines):
 final=[];progress=0
 for line in lines:
  row=json.loads(line)
  if row.get('event')=='progress':
   if final:raise ValueError('Progress after final reply')
   data=row.get('data')
   if not isinstance(data,dict):raise ValueError('Invalid progress data')
   percent=data.get('percent')
   if percent is not None and(type(percent)not in (int,float)or not 0<=percent<=100):raise ValueError('Invalid progress percent')
   progress+=1
  else:final.append(row)
 if len(final)!=1:raise ValueError('Expected exactly one final response')
 data=final[0]
 if data.get('ok')is not True or data.get('data',{}).get('model_bytes')!=1525787092:raise ValueError('Embedding frozen final reply failed: '+str(data)[:500])
 return {'ok':True,'progress_events':progress,'final':data}

if __name__=='__main__':
 result=subprocess.run([sys.argv[1]],input=json.dumps({'action':'check','consent':True})+'\n',capture_output=True,text=True,timeout=180)
 if result.returncode:raise RuntimeError('Frozen EXE exited '+str(result.returncode)+': '+result.stderr[-1200:])
 report=validate(result.stdout.splitlines());print(json.dumps(report),flush=True)
