// Derived from jhmeel/Bigfoot95f7ffdb, GPL-3.0-or-later. See third-party/bigfoot/NOTICE.md.
export type Point={x:number,y:number};
export type Spring={pos:Point,vel:Point};
export function followStep(state:Spring,cursor:Point,dt:number,bounds:Point,reduced=false):Spring{
 if(![cursor.x,cursor.y,dt,bounds.x,bounds.y].every(Number.isFinite)||bounds.x<=0||bounds.y<=0)throw Error('Invalid companion coordinates');
 const target={x:Math.max(24,Math.min(bounds.x-24,cursor.x+35)),y:Math.max(24,Math.min(bounds.y-24,cursor.y+25))};
 if(reduced||state.pos.x<0)return{pos:target,vel:{x:0,y:0}};
 const pos={...state.pos},vel={...state.vel},k=(2*Math.PI/.2)**2,c=2*.6*Math.sqrt(k),h=Math.max(0,Math.min(dt,1/30))/4;
 for(let i=0;i<4;i++){vel.x+=(-k*(pos.x-target.x)-c*vel.x)*h;vel.y+=(-k*(pos.y-target.y)-c*vel.y)*h;pos.x+=vel.x*h;pos.y+=vel.y*h}
 pos.x=Math.max(24,Math.min(bounds.x-24,pos.x));pos.y=Math.max(24,Math.min(bounds.y-24,pos.y));return{pos,vel};
}
export function smoothPath(pts:Point[]):string{
 if(pts.length>4096||pts.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)))throw Error('Invalid drawing points');
 if(!pts.length)return'';
 if(pts.length<3)return `M${pts.map(p=>`${p.x},${p.y}`).join(' L')}`;
 let d=`M${pts[0].x},${pts[0].y}`;
 for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;d+=` C${p1.x+(p2.x-p0.x)/6},${p1.y+(p2.y-p0.y)/6} ${p2.x-(p3.x-p1.x)/6},${p2.y-(p3.y-p1.y)/6} ${p2.x},${p2.y}`}
 return d;
}
