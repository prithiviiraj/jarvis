import{useEffect,useRef,useState}from'react';import ForceGraph3D,{type ForceGraph3DInstance,type NodeObject}from'3d-force-graph';
export type GraphNode={id:string,label:string,category:string,preview:string};
export type GraphData={nodes:GraphNode[],edges:{source:string,target:string}[],state:string,truncated?:boolean,scope:string};
const colors=['#60d2a7','#62a9e0','#dcb353','#b98bda','#d773a9','#b9d2d5'];
export function KnowledgeUniverse({data,activity='idle',sourceIds=[],onFocus}:{data?:GraphData,query:string,activity?:string,area?:string,sourceIds?:string[],onSearch?:(query:string)=>void,onFocus:(node:GraphNode|null)=>void}){
 const root=useRef<HTMLDivElement>(null);const graph=useRef<ForceGraph3DInstance<NodeObject&GraphNode&{color?:string,weight?:number}>|null>(null);const focusRef=useRef(onFocus);focusRef.current=onFocus;const[failed,setFailed]=useState(false);const[focused,setFocused]=useState<string|null>(null);const nodes=data?.nodes||[],edges=data?.edges||[];const categories=[...new Set(nodes.map(n=>n.category))].sort();
 useEffect(()=>{
  if(!root.current)return;let g:ForceGraph3DInstance<NodeObject&GraphNode&{color?:string,weight?:number}>|null=null;let observer:ResizeObserver|undefined;
  try{
   g=new ForceGraph3D(root.current,{controlType:'orbit'})as unknown as ForceGraph3DInstance<NodeObject&GraphNode&{color?:string,weight?:number}>;graph.current=g;
   g.backgroundColor('#04090c').showNavInfo(false).nodeId('id').nodeLabel(n=>{const label=document.createElement('span');label.textContent=String(n.label||'');return label})
    .nodeColor(n=>String(n.color||'#70c9b5')).nodeVal(n=>Number(n.weight||2)).nodeOpacity(.88).linkColor(()=> '#3c786b').linkOpacity(.18).linkWidth(.5).enableNodeDrag(false)
    .onNodeClick(n=>{const note={id:String(n.id),label:String(n.label),category:String(n.category),preview:String(n.preview||'')};setFocused(note.id);focusRef.current(note);const x=Number(n.x||0),y=Number(n.y||0),z=Number(n.z||0);const distance=Math.hypot(x,y,z)||1;g?.cameraPosition({x:x+x/distance*90,y:y+y/distance*90,z:z+z/distance*90},{x,y,z},1100)})
    .onBackgroundClick(()=>{setFocused(null);focusRef.current(null);g?.zoomToFit(1000,75)});
   observer=new ResizeObserver(rows=>{const r=rows[0].contentRect;if(r.width&&r.height)g?.width(r.width).height(r.height)});observer.observe(root.current);
   const media=window.matchMedia('(prefers-reduced-motion: reduce)');const controls=g.controls()as{autoRotate:boolean,autoRotateSpeed:number};const motion=()=>{controls.autoRotate=!media.matches;root.current?.setAttribute('data-motion',media.matches?'still':'live')};motion();controls.autoRotateSpeed=.15;media.addEventListener('change',motion);const original=observer.disconnect.bind(observer);observer.disconnect=()=>{media.removeEventListener('change',motion);original()};
  }catch{setFailed(true)}
  return()=>{observer?.disconnect();g?._destructor();graph.current=null}
 },[]);
 useEffect(()=>{
  const g=graph.current;if(!g)return;const degree=new Map<string,number>();for(const e of edges){degree.set(e.source,(degree.get(e.source)||0)+1);degree.set(e.target,(degree.get(e.target)||0)+1)}
  const ids=new Set(nodes.slice(0,500).map(n=>n.id));g.graphData({nodes:nodes.slice(0,500).map(n=>({...n,color:colors[categories.indexOf(n.category)%colors.length],weight:Math.min(12,2+(degree.get(n.id)||0)*.5)})),links:edges.filter(e=>ids.has(e.source)&&ids.has(e.target)).map(e=>({...e}))});g.cooldownTicks(100);const timer=setTimeout(()=>g.zoomToFit(900,80),1200);return()=>clearTimeout(timer)
 },[JSON.stringify(data)]);
 useEffect(()=>{const hit=nodes.find(n=>sourceIds.includes(n.id));if(hit&&hit.id!==focused){focusRef.current(hit);setFocused(hit.id)}},[sourceIds.join('|')]);
 return <section className="knowledge-universe reference-graph" aria-label="Living knowledge graph" data-activity={activity}><div className="graph-3d" ref={root}/><div className="graph-caption"><span>YOUR NOTES</span><h2>{nodes.length?'Your connected world':'Make this space yours'}</h2><p>{nodes.length?'Choose a note to explore its connections.':'Connect your notes to begin. Nothing is invented here.'}</p></div><aside className="graph-spaces" aria-label="Your note spaces">{categories.slice(0,7).map((c,i)=><div key={c} style={{color:colors[i%colors.length]}}>{c}</div>)}</aside>{failed&&<div className="graph-empty"><h2>Simple note view</h2><p>Your graphics display could not start. Your notes still work.</p>{nodes.slice(0,8).map(n=><div tabIndex={0} key={n.id} onClick={()=>onFocus(n)} onKeyDown={e=>e.key==='Enter'&&onFocus(n)}>{n.label}</div>)}</div>}<div className="graph-source-status">{nodes.length} real notes · {edges.length} saved links{data?.truncated?' · showing part of your notes':''}</div></section>
}
