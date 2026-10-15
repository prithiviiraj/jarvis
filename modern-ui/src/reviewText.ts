// Presentation only. Exact original objects remain bound to confirmation callbacks.
const names:Record<string,string>={url:'Page',value:'Destination',source_url:'News page',expected_url:'Current page',action:'Action',command:'Action',model_id:'Model',model:'Model',repo:'Repository',sha256:'Content fingerprint',size_bytes:'Download bytes',bytes:'Bytes',consent:'Permission',confirm:'Confirmation',text:'Text',scope:'Limits',payload:'Details',before:'Current content',values:'Cell text',pending:'Review',result:'Result',enabled:'Enabled'};
function label(key:string){return names[key]||key.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/[_-]+/g,' ').replace(/^./,c=>c.toUpperCase())}
export function reviewText(value:unknown,depth=0):string{
 if(value===null||value===undefined)return 'None';
 if(typeof value==='string')return value;
 if(typeof value==='boolean')return value?'Yes':'No';
 if(typeof value==='number')return String(value);
 if(Array.isArray(value))return value.length?value.map((v,i)=>String(i+1)+'. '+reviewText(v,depth+1)).join('\n'):'No items';
 if(typeof value==='object')return Object.entries(value as Record<string,unknown>).map(([key,v])=>label(key)+': '+(v!==null&&typeof v==='object'?'\n'+reviewText(v,depth+1).split('\n').map(row=>'  '+row).join('\n'):reviewText(v,depth+1))).join('\n');
 return 'Unavailable';
}
