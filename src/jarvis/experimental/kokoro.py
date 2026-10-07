"""Evaluation-only adapter, not enabled by application. Direct ONNX plus isolated native MIT G2P. No GPL imports."""
import json,subprocess,threading,queue
from pathlib import Path
class VoiceError(RuntimeError):pass
class NativeG2P:
    def __init__(self,exe,data):
        data=Path(data)
        self.lock=threading.Lock();self.lines=queue.Queue(maxsize=4);self.closed=False
        self.process=subprocess.Popen([str(exe),str(data/'lexicon_full.json'),str(data/'phonemizer_en_us.bin'),str(data/'tagger.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=0x08000000 if __import__('os').name=='nt' else 0)
        def drain():
            try:
                while True:
                    line=self.process.stdout.readline(8193)
                    if not line:break
                    if len(line)>8192:break
                    try:self.lines.put(line.strip(),timeout=.5)
                    except queue.Full:break
            finally:
                try:self.lines.put_nowait(None)
                except queue.Full:pass
        self.thread=threading.Thread(target=drain,daemon=True);self.thread.start()
        try:
            if self.lines.get(timeout=15)!='READY':raise VoiceError('Native voice frontend did not start.')
        except Exception:self.close();raise VoiceError('Native voice frontend unavailable.') from None
    def phonemize(self,text):
        if not isinstance(text,str) or not text or len(text.encode('utf-8'))>1000 or '\n' in text or '\r' in text or '\0' in text:raise VoiceError('Speech clause is invalid or too long.')
        with self.lock:
            if self.closed or self.process.poll() is not None:raise VoiceError('Native voice frontend stopped.')
            try:
                self.process.stdin.write(text+'\n');self.process.stdin.flush();value=self.lines.get(timeout=10)
                if not value or value=='ERROR':raise VoiceError('Pronunciation unavailable.')
                return value
            except Exception:self.close();raise VoiceError('Native voice frontend failed. No speech generated.') from None
    def close(self):
        self.closed=True
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=2)
        for pipe in (self.process.stdin,self.process.stdout):
            try:pipe.close()
            except Exception:pass

_SESSIONS={};_SESSION_LOCK=threading.RLock()

class KokoroSynth:
    def __init__(self,model,voice,config,g2p):
        import numpy as np,onnxruntime as ort
        self.np=np;self.g2p=g2p;self.lock=_SESSION_LOCK
        opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
        with _SESSION_LOCK:
            key=str(model)
            if key not in _SESSIONS:_SESSIONS[key]=ort.InferenceSession(key,sess_options=opts,providers=['CPUExecutionProvider'])
            self.session=_SESSIONS[key]
        self.vocab=json.loads(Path(config).read_text(encoding='utf-8'))['vocab']
        # Approved-format raw style matrices, not pickle or unknown archive execution.
        self.voice=np.fromfile(str(voice),dtype='<f4').reshape(510,256)
        inputs={x.name:x.type for x in self.session.get_inputs()}
        if inputs.get('input_ids')!='tensor(int64)' or inputs.get('style')!='tensor(float)' or inputs.get('speed')!='tensor(float)':raise VoiceError('Unsupported model input schema.')
    def synthesize(self,text,speed=1.0):
        if not .7<=speed<=1.4:raise VoiceError('Speed out of range.')
        with self.lock:
            phones=self.g2p.phonemize(text)
            if not 1<=len(phones)<=510 or any(c not in self.vocab for c in phones):raise VoiceError('Pronunciation is too long or unsupported.')
            tokens=[self.vocab[c] for c in phones];np=self.np
            audio=self.session.run(None,{'input_ids':np.array([[0,*tokens,0]],np.int64),'style':self.voice[len(tokens)-1].reshape(1,256),'speed':np.array([speed],np.float32)})[0].reshape(-1)
            if not 0<len(audio)<=24000*40 or not np.isfinite(audio).all():raise VoiceError('Voice output is invalid.')
            return np.clip(audio,-1,1).astype(np.float32),24000

    def synthesize_stream(self,text,speed=1.0,max_chars=120):
        """Yield bounded local synthesis chunks, not token-streaming within ONNX.
        Split only at punctuation/word boundaries. Existing per-chunk validation stays.
        """
        from ..streaming import sentences
        if not isinstance(text,str) or not 40<=max_chars<=220:raise VoiceError('Invalid voice stream input.')
        for part in sentences(iter(text),max_chars=max_chars):
            audio,sr=self.synthesize(part,speed)
            yield part,audio,sr
