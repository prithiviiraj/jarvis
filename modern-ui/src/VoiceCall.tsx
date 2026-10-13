export function VoiceActivity({input,output,active,speaking}:{input:number,output:number,active:boolean,speaking:boolean}){
 const level=Math.min(1,Math.max(0,speaking?output:active?input:0));const strength=Math.sqrt(level)*2;
 return <div className={'live-voice-wave '+(speaking?'playback':'capture')} data-level={level.toFixed(3)} aria-label={speaking?'Playback activity':active?'Microphone activity':'Audio inactive'}>{Array.from({length:13},(_,i)=><i key={i} style={{height:3+Math.min(27,strength*(12+(i%5)*4))+'px'}}/>)}</div>;
}
