'use strict';
// Adapted verbatim tone/SOUNDS from Bigfoot95f7ffdb renderer/engine.js. GPL-3.0-or-later.
(()=>{let context=null;
  function tone(c, { freq, start, dur, type = 'sine', gain = 0.12, to = null, lp = null }) {
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, start);
    if (to) osc.frequency.exponentialRampToValueAtTime(to, start + dur * 0.9);
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(gain, start + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    let node = osc;
    if (lp) {
      const f = c.createBiquadFilter();
      f.type = 'lowpass';
      f.frequency.value = lp;
      osc.connect(f);
      node = f;
    }
    node.connect(g).connect(c.destination);
    osc.start(start);
    osc.stop(start + dur + 0.05);
  }

  const SOUNDS = {
    'listen-start': (c, t) => { tone(c, { freq: 587, start: t, dur: 0.11, gain: 0.09 }); tone(c, { freq: 880, start: t + 0.07, dur: 0.16, gain: 0.1 }); },
    'listen-stop': (c, t) => { tone(c, { freq: 880, start: t, dur: 0.1, gain: 0.08 }); tone(c, { freq: 587, start: t + 0.06, dur: 0.15, gain: 0.08 }); },
    done: (c, t) => {
      [659, 831, 988].forEach((f, i) => tone(c, { freq: f, start: t + i * 0.07, dur: 0.35, type: 'triangle', gain: 0.07 }));
      tone(c, { freq: 1319, start: t + 0.21, dur: 0.5, gain: 0.03 });
    },
    error: (c, t) => {
      tone(c, { freq: 392, start: t, dur: 0.14, type: 'triangle', gain: 0.11, lp: 1800 });
      tone(c, { freq: 294, start: t + 0.13, dur: 0.24, type: 'triangle', gain: 0.11, lp: 1800 });
    },
    attention: (c, t) => { tone(c, { freq: 1047, start: t, dur: 0.28, gain: 0.07 }); tone(c, { freq: 1568, start: t, dur: 0.18, gain: 0.025 }); },
  };


 window.jarvisSound=(name)=>{if(localStorage.getItem('jarvis-ui-sounds')!=='on'||!SOUNDS[name])return;try{context=context||new AudioContext();if(context.state!=='running')return;SOUNDS[name](context,context.currentTime+.01)}catch{}};
 window.jarvisEnableSound=async()=>{try{context=context||new AudioContext();await context.resume();window.jarvisSound('done')}catch{}};
})();
