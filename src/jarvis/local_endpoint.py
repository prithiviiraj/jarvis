"""Single RAM-only owned llama.cpp route registry. No automatic start or fallback."""
import threading
_lock=threading.RLock();_runtime=None

def bind(runtime):
 global _runtime
 with _lock:
  if _runtime is not None and _runtime is not runtime:raise ValueError('Another managed runtime owns the route')
  _runtime=runtime

def unbind(runtime):
 global _runtime
 with _lock:
  if _runtime is runtime:_runtime=None

def managed_route():
 with _lock:runtime=_runtime
 if runtime is None:return None
 # A bound but unavailable owned runtime must never fall back to unrelated server.
 route=runtime.route()
 return {**route,'vision':True,'scope':'Owned session requires successful synthetic text and image generation tests'}
