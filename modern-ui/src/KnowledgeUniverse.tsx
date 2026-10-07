import React,{useEffect,useMemo,useState} from 'react';
export type GraphNode={id:string,label:string,category:string,preview:string};
export type GraphData={nodes:GraphNode[],edges:{source:string,target:string}[],state:string,truncated?:boolean,scope:string};
const palette=['#6ba6df','#dfbf59','#65b99b','#d580ad','#ae91dd','#a4c9cd'];
export function KnowledgeUniverse({data,query,onFocus}:{data?:GraphData,query:string,onFocus:(node:GraphNode|null)=>void}){
 const[focus,setFocus]=useState<string|null>(null);const[drag,setDrag]=useState({x:0,y:0});
 const nodes=data?.nodes||[];const groups=useMemo(()=>[...new Set(nodes.map(n=>n.category))],[nodes]);
 const points=useMemo(()=>nodes.map((n,i)=>{const g=groups.indexOf(n.category),j=nodes.slice(0,i).filter(p=>p.category===n.category).length;const angle=j*2.399963;const radius=22+Math.sqrt(j)*19;const a=g/Math.max(1,groups.length)*Math.PI*2;return {...n,x:500+Math.cos(a)*205+Math.cos(angle)*radius,y:335+Math.sin(a)*150+Math.sin(angle)*radius*.8,color:palette[g%palette.length]}}),[nodes,groups]);
 useEffect(()=>{if(focus&&!nodes.some(n=>n.id===focus)){setFocus(null);onFocus(null)}},[nodes,focus]);
 useEffect(()=>{if(!query)return;const q=query.toLowerCase();const hit=nodes.find(n=>q.includes(n.label.toLowerCase())||q.includes(n.category.toLowerCase())||(/plan|schedule|calendar/.test(q)&&/planning|calendar/.test(n.category.toLowerCase())));if(hit){setFocus(hit.id);onFocus(hit)}},[query,nodes]);
 const selected=points.find(n=>n.id===focus);const scale=selected?1.8:1;const x=selected?500-selected.x*scale:drag.x;const y=selected?335-selected.y*scale:drag.y;
 return <section className="knowledge-universe" aria-label="Living knowledge graph"><svg viewBox="0 0 1000 670" role="img" aria-label={nodes.length+' real knowledge nodes'} onWheel={e=>{if(selected){setFocus(null);onFocus(null)}else setDrag(p=>({x:p.x-e.deltaX*.2,y:p.y-e.deltaY*.2}))}}>
 <defs><filter id="node-glow"><feGaussianBlur stdDeviation="2"/></filter><radialGradient id="space"><stop stopColor="#112225"/><stop offset="1" stopColor="#060a0d"/></radialGradient></defs><rect width="1000" height="670" fill="url(#space)"/>
 <g className="graph-camera" style={{transform:`translate(${x}px,${y}px) scale(${scale})`}}>{(data?.edges||[]).map((e,i)=>{const a=points.find(n=>n.id===e.source),b=points.find(n=>n.id===e.target);return a&&b?<line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#3d7975" strokeOpacity=".24"/>:null})}{points.map((n,i)=><g key={n.id} tabIndex={0} role="button" aria-label={'Knowledge note '+n.label} onKeyDown={e=>e.key==='Enter'&&(setFocus(n.id),onFocus(n))} onClick={()=>{setFocus(n.id);onFocus(n)}}><circle cx={n.x} cy={n.y} r={focus===n.id?9:3.5+i%4} fill={n.color} opacity={focus&&focus!==n.id ? .65 : 1}/>{(focus===n.id||points.length<25)&&<text x={n.x+10} y={n.y+4} fill="#ced9dc" fontSize="9">{n.label}</text>}</g>)}</g></svg>
 {!nodes.length&&<div className="graph-empty"><span className="empty-orbit"/><h2>{data?.state==='ready'?'Your vault is empty':'Your knowledge universe'}</h2><p>{data?.state==='ready'?'Add a note in Obsidian to begin.':'Connect Obsidian in Settings to reveal real notes.'}</p><small>No invented nodes</small></div>}
 <div className="graph-legend">{groups.map((g,i)=><span key={g}><i style={{background:palette[i%palette.length]}}/>{g}</span>)}</div><span className="graph-count">{nodes.length} notes{data?.truncated?' · bounded view':''}</span>
 </section>
}
