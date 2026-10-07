import React,{useEffect,useMemo,useState} from 'react';
export type GraphNode={id:string,label:string,category:string,preview:string};
export type GraphData={nodes:GraphNode[],edges:{source:string,target:string}[],state:string,truncated?:boolean,scope:string};
const palette=['#77c4c7','#d4bc75','#8ab5a0','#bda0bc','#9caed0','#a4c9cd'];
export function KnowledgeUniverse({data,query,onFocus}:{data?:GraphData,query:string,onFocus:(node:GraphNode|null)=>void}){
 const[folder,setFolder]=useState('');const[focus,setFocus]=useState<string|null>(null);const[compact,setCompact]=useState(window.innerWidth<580);
 useEffect(()=>{const f=()=>setCompact(window.innerWidth<580);window.addEventListener('resize',f);return()=>window.removeEventListener('resize',f)},[]);
 const nodes=data?.nodes||[],edges=data?.edges||[];
 const groups=useMemo(()=>[...new Set(nodes.map(n=>n.category))].sort(),[nodes]);
 const degree=useMemo(()=>{const m=new Map<string,number>();for(const e of edges){m.set(e.source,(m.get(e.source)||0)+1);m.set(e.target,(m.get(e.target)||0)+1)}return m},[edges]);
 const selected=nodes.find(n=>n.id===focus);
 const neighbors=useMemo(()=>new Set(edges.filter(e=>e.source===focus||e.target===focus).flatMap(e=>[e.source,e.target]).filter(x=>x!==focus)),[edges,focus]);
 const visible=useMemo(()=>{
  if(selected)return [selected,...nodes.filter(n=>neighbors.has(n.id)).sort((a,b)=>(degree.get(b.id)||0)-(degree.get(a.id)||0)).slice(0,compact?3:8)];
  // Real folder lanes; high-link notes first. No decorative or inferred edges.
  return (folder?[folder]:groups.slice(0,compact?2:4)).flatMap(g=>nodes.filter(n=>n.category===g).sort((a,b)=>(degree.get(b.id)||0)-(degree.get(a.id)||0)||a.label.localeCompare(b.label)).slice(0,3));
 },[nodes,groups,selected,neighbors,degree,folder,compact]);
 const points=visible.map((n,i)=>{
  const lane=groups.indexOf(n.category),column=selected?(i===0?(compact?0:1):(i-1)%(compact?2:3)):(folder?[folder]:groups.slice(0,compact?2:4)).indexOf(n.category);
  const row=selected?(i===0?0:1+Math.floor((i-1)/(compact?2:3))):visible.slice(0,i).filter(x=>x.category===n.category).length;
  return {...n,x:selected?25+column*(compact?219:265):38+column*219,y:selected?76+row*112:112+row*118,color:palette[lane%palette.length]};
 });
 useEffect(()=>{if(focus&&!nodes.some(n=>n.id===focus)){setFocus(null);onFocus(null)}},[nodes,focus]);
 useEffect(()=>{if(!query)return;const q=query.toLowerCase();const hit=nodes.find(n=>q.includes(n.label.toLowerCase())||q.includes(n.category.toLowerCase())||(/plan|schedule|calendar/.test(q)&&/planning|calendar/.test(n.category.toLowerCase())));if(hit){setFocus(hit.id);onFocus(hit)}},[query,nodes]);
 function reset(){setFocus(null);onFocus(null)}
 const shownEdges=edges.filter(e=>visible.some(n=>n.id===e.source)&&visible.some(n=>n.id===e.target));
 return <section className={'knowledge-universe practical-graph'+(selected?' graph-focused':'')} aria-label="Living knowledge graph">
 <div className="graph-caption"><span>{selected?'NOTE CONNECTIONS':'VAULT ATLAS'}</span><h2>{selected?.label||'A map you can work with'}</h2><p>{selected?neighbors.size+' linked notes · explicit Obsidian links':'Real folders. Named notes. Explicit connections.'}</p></div>
 {nodes.length>0&&!selected&&<select className="atlas-folder-filter" aria-label="Knowledge folder" value={folder} onChange={e=>setFolder(e.target.value)}><option value="">Folder overview</option>{groups.map(g=><option key={g}>{g}</option>)}</select>}
 <svg viewBox={compact?"0 0 470 470":"0 0 940 650"} role="img" aria-label={nodes.length+' real knowledge nodes'} onWheel={()=>selected&&reset()} onKeyDown={e=>e.key==='Escape'&&reset()}>
 <defs><pattern id="atlas-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#21404b" strokeWidth=".5" opacity=".25"/></pattern><linearGradient id="atlas-bg" x2="1" y2="1"><stop stopColor="#0c1720"/><stop offset="1" stopColor="#070e14"/></linearGradient></defs>
 <rect width="940" height="650" fill="url(#atlas-bg)"/><rect width="940" height="650" fill="url(#atlas-grid)"/>
 <g className="atlas-content">
 {!selected&&(folder?[folder]:groups.slice(0,compact?2:4)).map((g,i)=><g key={g}><rect x={25+i*219} y="54" width="209" height="402" rx="14" fill="#0c192180" stroke="#25404b" strokeDasharray="3 6"/><text x={40+i*219} y="80" fill={palette[i%palette.length]} fontSize="13" fontWeight="600">{g.slice(0,23)}</text><text x={40+i*219} y="97" fill="#6e8c9b" fontSize="9">{nodes.filter(n=>n.category===g).length} notes · folder</text></g>)}
 {shownEdges.map((e,i)=>{const a=points.find(n=>n.id===e.source)!,b=points.find(n=>n.id===e.target)!;return <path className="atlas-link" key={i} d={`M${a.x+96} ${a.y+44} C${a.x+96} ${a.y+105},${b.x+96} ${b.y-40},${b.x+96} ${b.y+44}`} fill="none" stroke={selected?'#72bcb7':'#416d7a'} strokeWidth={selected?1.6:1} opacity={selected?.65:.32}/>})}
 {points.map(n=><g className={'atlas-note'+(n.id===focus?' selected':'')} key={n.id} transform={`translate(${n.x},${n.y})`} tabIndex={0} role="button" aria-label={'Knowledge note '+n.label} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setFocus(n.id);onFocus(n)}if(e.key==='Escape')reset()}} onClick={()=>{setFocus(n.id);onFocus(n)}}>
 <rect className="note-card" width="192" height="88" rx="9" fill={n.id===focus?'#15333d':'#10212c'} stroke={n.id===focus?'#8ed7cc':'#2a4655'}/><path d="M13 17h11l5 5v14H13z M24 17v6h5" stroke={n.color} fill="none" strokeWidth="1.1"/><text x="37" y="24" fill={n.color} fontSize="8.5" letterSpacing=".7">{n.category.slice(0,22).toUpperCase()}</text>
 <text x="13" y="48" fill="#d6e5ea" fontSize="12" fontWeight="500">{n.label.length>25?n.label.slice(0,24)+'…':n.label}</text><text x="13" y="67" fill="#7c9cab" fontSize="9">{n.preview.replace(/^#+\s*/,'').replace(/\n/g,' ').slice(0,32)||'Local Markdown note'}</text><text x="178" y="78" textAnchor="end" fill="#9cc9c7" fontSize="8">{degree.get(n.id)||0} links</text>
 </g>)}
 </g></svg>
 {!nodes.length&&<div className="graph-empty"><h2>{data?.state==='ready'?'Your vault is empty':'Your knowledge universe'}</h2><p>{data?.state==='ready'?'Add a note in Obsidian to begin.':'Connect Obsidian in Settings to reveal real notes.'}</p><small>No invented nodes</small></div>}
 {nodes.length>0&&<div className="atlas-footer">{visible.length} of {nodes.length} notes shown · {selected?'Linked neighborhood. Escape or scroll for overview.':'Most connected notes per folder. Select a note to inspect its links.'}{data?.truncated?' · bounded scan':''}</div>}
 </section>
}
