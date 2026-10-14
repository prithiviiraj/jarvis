"""Allowlisted runtime log measurements. Never return raw logs, paths or credentials."""
import re,math,subprocess
from .changed_image_latency import ImageProfile

class MeasuredImageProfile(ImageProfile):
 def __init__(self,spawn=None):super().__init__();self.spawn=spawn or subprocess.Popen
 def __call__(self,args,**kwargs):
  if any(x in args for x in ('--verbosity','--log-verbosity','-lv','--verbose','--log-verbose','-v')):raise ValueError('Unexpected existing logging policy')
  if any(x in args for x in ('--image-min-tokens','--image-max-tokens','--mtmd-batch-max-tokens')):raise ValueError('Unexpected existing image policy')
  return self.spawn(list(args)+['--image-min-tokens','1024','--image-max-tokens','2048','--mtmd-batch-max-tokens','1024','--log-verbosity','5'],**kwargs)


NUMBER=r'([0-9]{1,18}(?:\.[0-9]{1,12})?)'

def measurements(raw):
 if not isinstance(raw,str):raise ValueError('Runtime log text required')
 offload=[{'loaded':int(a),'total':int(b)}for a,b in re.findall(r'offloaded (\d+)/(\d+) layers to GPU',raw)]
 # Only documented backend labels are accepted, not arbitrary source text.
 names=re.findall(r'CLIP using ([A-Za-z0-9_.-]{1,24}) backend',raw)
 backends=[x for x in names if re.fullmatch(r'(?:CPU|CUDA\d*|Vulkan\d*|Metal|ROCm\d*|SYCL\d*|HIP\d*)',x,re.I)]
 image_encode=[float(x)for x in re.findall(r'image slice encoded in '+NUMBER+r' ms',raw)]
 image_decode=[float(x)for x in re.findall(r'image decoded \(batch \d+/\d+\) in '+NUMBER+r' ms',raw)]
 image_total=[float(x)for x in re.findall(r'image processed in '+NUMBER+r' ms',raw)]
 timing=[{'stage':a,'ms':float(b)}for a,b in re.findall(r'(prompt eval|eval) time\s*=\s*'+NUMBER+r' ms',raw)]
 image_encode=[x for x in image_encode if math.isfinite(x)]
 image_decode=[x for x in image_decode if math.isfinite(x)]
 image_total=[x for x in image_total if math.isfinite(x)]
 timing=[x for x in timing if math.isfinite(x['ms'])]
 return {'decoder_offload':offload,'projector_backends':backends,'image_encoding_ms':image_encode,'image_decoding_ms':image_decode,'image_processing_ms':image_total,'text_timings':timing,'gpu_offload_confirmed':any(x['loaded']>0 for x in offload),'projector_gpu_confirmed':any(x.upper()!='CPU'for x in backends),'scope':'Observed numeric runtime log evidence only. Missing rows mean not observed, not CPU or zero latency. Decoder and projector evidence are independent.'}
