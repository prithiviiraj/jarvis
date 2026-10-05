"""NumPy80-bin Slaney log-mel features, verified against WhisperFeatureExtractor.
Independent equations; avoids packaging Transformers/Torch for8MB turn model.
"""
def features(audio):
 import numpy as np
 a=np.asarray(audio,dtype=np.float32).reshape(-1)[-128000:]
 if a.size<128000:a=np.pad(a,(128000-a.size,0))
 a=(a-a.mean())/np.sqrt(a.var()+1e-7)
 def mel(hz):return hz/(200/3)if hz<1000 else 15+np.log(hz/1000)/(np.log(6.4)/27)
 def hz(m):return m*(200/3)if m<15 else 1000*np.exp((m-15)*(np.log(6.4)/27))
 centers=np.array([hz(x)for x in np.linspace(mel(0),mel(8000),82)])
 freqs=np.linspace(0,8000,201);left=(freqs[:,None]-centers[:-2])/(centers[1:-1]-centers[:-2]);right=(centers[2:]-freqs[:,None])/(centers[2:]-centers[1:-1]);bank=np.maximum(0,np.minimum(left,right))*(2/(centers[2:]-centers[:-2]))
 padded=np.pad(a.astype(np.float64),(200,200),mode='reflect');frames=np.lib.stride_tricks.sliding_window_view(padded,400)[::160];window=np.hanning(401)[:-1];power=np.abs(np.fft.rfft(frames*window,axis=1))**2
 log=np.log10(np.maximum(1e-10,bank.T@power.T))[:,:-1];log=np.maximum(log,log.max()-8);return ((log+4)/4).astype(np.float32)[None,:,:]
