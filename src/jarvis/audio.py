"""Local 16kHz audio adapters. No file recordings, network or implicit consent."""
from collections import deque
import queue
import threading
import time

class AudioError(RuntimeError):pass

class SileroVad:
    def __init__(self,path):
        import numpy as np
        import onnxruntime as ort
        self.np=np
        opts=ort.SessionOptions();opts.intra_op_num_threads=1;opts.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(path),sess_options=opts,providers=['CPUExecutionProvider'])
        self.reset()
    def reset(self):
        self.state=self.np.zeros((2,1,128),dtype=self.np.float32)
        self.context=self.np.zeros((1,64),dtype=self.np.float32)
    def score(self,frame):
        x=self.np.asarray(frame,dtype=self.np.float32).reshape(1,-1)
        if x.shape[1]!=512:raise AudioError('Expected 512 samples at 16000Hz.')
        x=self.np.concatenate([self.context,x],axis=1)
        out,self.state=self.session.run(None,{'input':x,'state':self.state,'sr':self.np.array(16000,dtype=self.np.int64)})
        self.context=x[:,-64:];return float(out.reshape(-1)[0])

class Endpointer:
    """Pure streaming state. 32ms frames, pre-roll, silence timeout, hard length cap."""
    def __init__(self,threshold=.5,silence_frames=25,min_frames=6,max_frames=625):
        if not 0<threshold<1 or silence_frames<1 or min_frames<1 or max_frames<min_frames:raise ValueError('Invalid endpoint settings.')
        self.threshold=threshold;self.silence_frames=silence_frames;self.min_frames=min_frames;self.max_frames=max_frames
        self.reset()
    def reset(self):
        self.pre=deque(maxlen=5);self.frames=[];self.active=False;self.silence=0;self.voiced=0
    def feed(self,frame,score):
        voiced=score>=self.threshold
        if not self.active:
            self.pre.append(frame)
            if not voiced:return None
            self.active=True;self.frames=list(self.pre);self.voiced=1;return ('start',None)
        self.frames.append(frame);self.voiced+=int(voiced);self.silence=0 if voiced else self.silence+1
        if self.silence>=self.silence_frames or len(self.frames)>=self.max_frames:
            frames=self.frames if self.voiced>=self.min_frames else None
            self.reset();return ('utterance',frames)
        return None

class ContinuousMic:
    """Capture -> bounded queue -> VAD worker. Overflow fails closed, no callback inference."""
    def __init__(self,vad,on_utterance,on_state=lambda *a:None):
        self.vad=vad;self.on_utterance=on_utterance;self.on_state=on_state
        self.frames=queue.Queue(maxsize=100);self.stop_event=threading.Event();self.stream=None;self.thread=None
        self.accepting=False;self.endpointer=Endpointer();self.generation=0;self.lock=threading.RLock()
    def start(self,consent=False):
        if not consent:raise AudioError('Enable the microphone with session consent first.')
        if self.stream is not None:return
        import sounddevice as sd
        self.stop_event.clear();self.generation+=1;generation=self.generation
        def callback(data,count,when,status):
            if self.stop_event.is_set() or not self.accepting:return
            if status:
                self.stop_event.set();self.on_state('error','Microphone buffer failed. Listening stopped.');return
            try:self.frames.put_nowait((self.generation,data[:,0].copy()))
            except queue.Full:
                self.stop_event.set();self.on_state('error','Audio queue filled. Listening stopped.')
        try:
            self.stream=sd.InputStream(samplerate=16000,channels=1,dtype='float32',blocksize=512,callback=callback)
            self.accepting=True;self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start();self.stream.start()
            self.on_state('state','listening')
        except Exception:
            self.close();raise AudioError('Cannot open the microphone. Check Windows permission and input device.') from None
    def suspend(self):
        with self.lock:self.accepting=False;self.generation+=1;self.endpointer.reset();self.vad.reset()
    def resume(self):
        with self.lock:self.generation+=1;self.endpointer.reset();self.vad.reset();self.accepting=True
    def run(self):
        import numpy as np
        try:
            while not self.stop_event.is_set():
                try:generation,frame=self.frames.get(timeout=.1)
                except queue.Empty:continue
                with self.lock:
                    if not self.accepting or generation!=self.generation:continue
                    result=self.endpointer.feed(frame,self.vad.score(frame))
                if result:
                    if result[0]=='start':self.on_state('state','capturing')
                    elif result[1] is not None:
                        self.suspend()
                        audio=np.concatenate(result[1])
                        # Callback schedules inference elsewhere, never in the audio callback.
                        self.on_utterance(audio)
                    else:self.on_state('state','listening')
        except Exception:self.on_state('error','Voice detection failed. Listening stopped.')
        finally:
            self.stop_event.set()
            stream=self.stream
            if stream:
                try:stream.abort();stream.close()
                except Exception:pass
            self.stream=None;self.accepting=False
    def close(self):
        self.accepting=False;self.generation+=1;self.stop_event.set()
        stream=self.stream
        if stream:
            try:stream.abort();stream.close()
            except Exception:pass
        self.stream=None
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=2)
        while True:
            try:self.frames.get_nowait()
            except queue.Empty:break
        self.endpointer.reset();self.vad.reset()
