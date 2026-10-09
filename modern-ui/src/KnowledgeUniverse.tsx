import React,{useEffect,useMemo,useState} from 'react';
export type GraphNode={id:string,label:string,category:string,preview:string};
export type GraphData={nodes:GraphNode[],edges:{source:string,target:string}[],state:string,truncated?:boolean,scope:string};
const palette=['#77c4c7','#d4bc75','#8ab5a0','#bda0bc','#9caed0','#a4c9cd'];
export function KnowledgeUniverse({data,query,activity='idle',area='',sourceIds=[],onSearch,onFocus}:{data?:GraphData,query:string,activity?:string,area?:string,sourceIds?:string[],onSearch?:(query:string)=>void,onFocus:(node:GraphNode|null)=>void}){
 const[live,setLive]=useState(true);const[phase,setPhase]=useState(0);const[reduced,setReduced]=useState(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{const media=window.matchMedia('(prefers-reduced-motion: reduce)');const change=()=>setReduced(media.matches);media.addEventListener('change',change);return()=>media.removeEventListener('change',change)},[]);
 useEffect(()=>{if(!live||reduced||document.hidden)return;const timer=setInterval(()=>{if(!document.hidden)setPhase(p=>(p+.018)%(Math.PI*2))},80);return()=>clearInterval(timer)},[live,reduced]);
 const[search,setSearch]=useState('');const[yaw,setYaw]=useState(-.22);const[tilt,setTilt]=useState(.12);const[flat,setFlat]=useState(false);const[folder,setFolder]=useState('');const[focus,setFocus]=useState<string|null>(null);const[compact,setCompact]=useState(window.innerWidth<580);
 useEffect(()=>{const f=()=>setCompact(window.innerWidth<580);window.addEventListener('resize',f);return()=>window.removeEventListener('resize',f)},[]);
 const nodes=data?.nodes||[],edges=data?.edges||[];
 const groups=useMemo(()=>[...new Set(nodes.map(n=>n.category))].sort(),[nodes]);
 const degree=useMemo(()=>{const m=new Map<string,number>();for(const e of edges){m.set(e.source,(m.get(e.source)||0)+1);m.set(e.target,(m.get(e.target)||0)+1)}return m},[edges]);
 const selected=nodes.find(n=>n.id===focus);
 const neighbors=useMemo(()=>new Set(edges.filter(e=>e.source===focus||e.target===focus).flatMap(e=>[e.source,e.target]).filter(x=>x!==focus)),[edges,focus]);
 const visible=useMemo(()=>{
  if(selected)return [selected,...nodes.filter(n=>neighbors.has(n.id)).sort((a,b)=>(degree.get(b.id)||0)-(degree.get(a.id)||0)).slice(0,compact?3:8)];
  // Real folder lanes; high-link notes first. No decorative or inferred edges.
  return (folder?[folder]:groups.slice(0,compact?3:8)).flatMap(g=>nodes.filter(n=>n.category===g).sort((a,b)=>(degree.get(b.id)||0)-(degree.get(a.id)||0)||a.label.localeCompare(b.label)).slice(0,compact?3:4));
 },[nodes,groups,selected,neighbors,degree,folder,compact]);
 // Orbit positions animate real nodes. Geometry does not imply extra relationships.
 const points=visible.map((n,i)=>{
  const lane=groups.indexOf(n.category),color=palette[lane%palette.length];
  if(flat)return {...n,x:compact?30+(i%2)*218:30+(i%4)*220,y:70+Math.floor(i/(compact?2:4))*110,scale:1,depth:0,color};
  const angle=i*2.399963+phase*.22+yaw,radius=visible.length<10?150:100+Math.sqrt(i/Math.max(1,visible.length))*235;
  const z=Math.sin(angle+phase)*135,depth=z*Math.cos(tilt),scale=760/(760-depth);
  const cx=compact?235:465,cy=compact?210:245;
  const x=selected?(i===0?cx:cx+Math.cos(angle)*170):cx+Math.cos(angle)*radius*(compact?.65:1);
  const y=selected?(i===0?cy:cy+Math.sin(angle)*155):cy+Math.sin(angle)*radius*.66+Math.sin(phase+i*.7)*8;
  return {...n,x:cx+(x-cx)*scale,y:cy+(y-cy)*scale,scale,depth,color};
 }).sort((a,b)=>a.depth-b.depth);
 useEffect(()=>{if(focus&&!nodes.some(n=>n.id===focus)){setFocus(null);onFocus(null)}},[nodes,focus]);
 useEffect(()=>{const hit=nodes.find(n=>sourceIds.includes(n.id));if(hit){setFocus(hit.id);onFocus(hit)}},[sourceIds.join('|')]);
 function reset(){setFocus(null);onFocus(null)}
 const shownEdges=edges.filter(e=>visible.some(n=>n.id===e.source)&&visible.some(n=>n.id===e.target));
 return <section className={'knowledge-universe practical-graph neural-live'+(selected?' graph-focused':'')} aria-label="Living knowledge graph" data-activity={activity} data-area={area} data-motion={live&&!reduced?'live':'still'}>
 <div className="graph-caption"><span>{selected?'SOURCE FOCUS':'NEURAL LIVE'}</span><h2>{selected?.label||'Your living knowledge universe'}</h2><p>{selected?neighbors.size+' linked notes · explicit Obsidian links':'Real notes in motion. Only explicit links carry knowledge.'}</p></div>
 {nodes.length>0&&!selected&&<select className="atlas-folder-filter" aria-label="Knowledge folder" value={folder} onChange={e=>setFolder(e.target.value)}><option value="">Folder overview</option>{groups.map(g=><option key={g}>{g}</option>)}</select>}
 <div className="atlas-navigation"><form onSubmit={e=>{e.preventDefault();if(search.trim())onSearch?.(search.trim())}}><input aria-label="Find knowledge source" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Find a local note..." maxLength={100}/><button aria-label="Search knowledge sources" disabled={!onSearch||!search.trim()}>Find</button></form><div><button onClick={()=>setLive(!live)} disabled={reduced}>{live?'Pause motion':'Resume motion'}</button><button aria-label="Rotate knowledge left" onClick={()=>setYaw(yaw-.18)}>↶</button><button aria-label="Rotate knowledge right" onClick={()=>setYaw(yaw+.18)}>↷</button><button aria-label="Tilt knowledge view" onClick={()=>setTilt(tilt>.25?-.12:tilt+.12)}>Tilt</button><button onClick={()=>setFlat(!flat)}>{flat?'Neural view':'Flat view'}</button>{selected&&<button onClick={reset}>Overview</button>}</div></div>
 <svg viewBox={compact?"0 0 470 470":"0 0 940 650"} role="img" aria-label={nodes.length+' real knowledge nodes'} onWheel={()=>selected&&reset()} onKeyDown={e=>e.key==='Escape'&&reset()}>
 <defs><pattern id="atlas-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#21404b" strokeWidth=".5" opacity=".25"/></pattern><linearGradient id="atlas-bg" x2="1" y2="1"><stop stopColor="#0c1720"/><stop offset="1" stopColor="#070e14"/></linearGradient></defs>
 <rect width="940" height="650" fill="url(#atlas-bg)"/><rect width="940" height="650" fill="url(#atlas-grid)"/>
 <g className="atlas-content">
 <title>{flat?'Flat note map':'Interactive perspective view of real note planes'}</title>
 {!flat&&<g className="neural-orbits" aria-hidden="true"><ellipse cx={compact?235:465} cy={compact?210:245} rx={compact?185:330} ry={compact?150:215}/><ellipse cx={compact?235:465} cy={compact?210:245} rx={compact?125:235} ry={compact?100:145}/><circle cx={compact?235:465} cy={compact?210:245} r="35"/><text x={compact?235:465} y={compact?214:249} textAnchor="middle">{area?area.toUpperCase():activity==='idle'?'CORE':activity.toUpperCase()}</text></g>}
 {shownEdges.map((e,i)=>{const a=points.find(n=>n.id===e.source)!,b=points.find(n=>n.id===e.target)!;return <path className="atlas-link" key={i} d={`M${a.x} ${a.y} C${a.x} ${a.y+105},${b.x} ${b.y-40},${b.x} ${b.y}`} fill="none" stroke={selected?'#72bcb7':'#416d7a'} strokeWidth={selected?1.6:1} opacity={selected?.65:.32}/>})}
 {points.map(n=><g className={'atlas-note'+(n.id===focus?' selected':'')} key={n.id} transform={`translate(${n.x},${n.y}) scale(${n.scale})`} tabIndex={0} role="button" aria-label={'Knowledge note '+n.label} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setFocus(n.id);onFocus(n)}if(e.key==='Escape')reset()}} onClick={()=>{setFocus(n.id);onFocus(n)}}>
 {flat?<><rect className="note-card" x="-92" y="-40" width="184" height="80" rx="9" fill="#10212c" stroke={n.color}/><text x="-80" y="-16" fill={n.color} fontSize="9">{n.category.slice(0,22).toUpperCase()}</text><text x="-80" y="6" fill="#d6e5ea" fontSize="12">{n.label.slice(0,25)}</text><text x="-80" y="24" fill="#7c9cab" fontSize="9">{degree.get(n.id)||0} explicit links</text></>:<><circle className="neural-halo" r={n.id===focus?30:20} fill="none" stroke={n.color} opacity=".3"/><circle className="neural-node" r={n.id===focus?9:5+(degree.get(n.id)||0)*.2} fill={n.color}/><text y="35" textAnchor="middle" fill="#c8e0e5" fontSize="11">{n.label.slice(0,25)}</text><text y="49" textAnchor="middle" fill={n.color} fontSize="7" letterSpacing="1">{n.category.toUpperCase().slice(0,20)}</text></>}

 </g>)}
 </g></svg>
 {!nodes.length&&<div className="graph-empty"><h2>{data?.state==='ready'?'Your vault is empty':'Your knowledge universe'}</h2><p>{data?.state==='ready'?'Add a note in Obsidian to begin.':'Connect Obsidian in Settings to reveal real notes.'}</p><small>No invented nodes</small></div>}
 {nodes.length>0&&<div className="atlas-footer">{visible.length} of {nodes.length} notes shown · {selected?'Linked neighborhood. Escape or scroll for overview.':'Animated positions, not autonomous thinking. Find searches beyond this bounded view.'}{data?.truncated?' · bounded scan':''}</div>}
 </section>
}
