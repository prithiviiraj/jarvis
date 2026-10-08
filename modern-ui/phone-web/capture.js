class Capture extends AudioWorkletProcessor{process(inputs){const x=inputs[0]?.[0];if(x)this.port.postMessage(x.slice());return true}}registerProcessor('jarvis-capture',Capture);
