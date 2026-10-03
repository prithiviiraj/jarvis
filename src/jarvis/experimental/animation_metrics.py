"""Animation callback statistics. These never measure display presentation FPS."""
import math

def percentile(values,q):
    data=sorted(values)
    if not data:raise ValueError('No samples')
    at=(len(data)-1)*q;lo=int(at);hi=min(lo+1,len(data)-1)
    return data[lo]+(data[hi]-data[lo])*(at-lo)

def summarize(starts,costs):
    if len(starts)<3 or len(costs)!=len(starts):raise ValueError('At least three matched samples required')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in starts+costs):raise ValueError('Invalid samples')
    gaps=[(b-a)*1000 for a,b in zip(starts,starts[1:])]
    if min(gaps)<=0 or min(costs)<0:raise ValueError('Invalid clock/order')
    ms=[x*1000 for x in costs]
    return {'callbacks':len(starts),'duration_s':starts[-1]-starts[0],
      'callback_rate_hz':(len(starts)-1)/(starts[-1]-starts[0]),
      'interval_ms':{'p50':percentile(gaps,.5),'p95':percentile(gaps,.95),'max':max(gaps)},
      'draw_update_cpu_ms':{'p50':percentile(ms,.5),'p95':percentile(ms,.95),'max':max(ms)},
      'interval_over_16_667_ms_pct':100*sum(x>1000/60 for x in gaps)/len(gaps),
      'interval_over_33_333_ms_pct':100*sum(x>1000/30 for x in gaps)/len(gaps),
      'display_fps_measured':False}
