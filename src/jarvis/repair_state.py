"""Grounded repair options. No self-modifying source or inferred authority."""
def repair_state(state):
 options=[];camera=state.get('awareness',{});game=state.get('game',{});voice=state.get('voice_setup',{});laya=state.get('laya',{});brains=state.get('brains',{})
 if voice.get('checked')and not voice.get('ready'):options.append({'kind':'voice-check','title':'Check local voice files','reason':voice.get('status','Speech files are not ready'),'scope':'Checks pinned files. No microphone or download.'})
 if game.get('enabled')and game.get('analysis_error'):options.append({'kind':'game-retry','title':'Retry screen understanding','reason':game['analysis_error'],'scope':'Retries the next current local frame. No new sensor or cloud permission.'})
 if camera.get('camera')=='error':options.append({'kind':'camera-help','title':'Check camera access','reason':camera.get('camera_master_status','Camera could not start'),'scope':'Open Windows Camera privacy yourself, allow desktop apps, and close another app using the camera. Camera is not restarted here.'})
 if camera.get('camera')=='on'and camera.get('vision')=='off':options.append({'kind':'local-brain-check','title':'Check the local vision connection','reason':camera.get('camera_master_status','Camera presence is on but vision is not ready'),'scope':'Reads model metadata only. It does not load a model or upload an image.'})
 if laya.get('engine',{}).get('error'):options.append({'kind':'laya-check','title':'Check Laya files','reason':str(laya['engine']['error'])[:240],'scope':'Checks pinned assets. No browser action or download.'})
 return {'options':options,'scope':'Current app evidence and narrow reviewed recovery only. New code and capabilities remain proposals, not automatic installs.'}
