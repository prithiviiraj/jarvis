"""Obsidian native Canvas map of separate owner-editable local areas."""
import json
AREAS=[('Agents','Agents index.md','Separate agent nodes'),('Planning','Planning/Today.md','Today and future plans'),('Calendar','Calendar/Home.md','Local calendar, no sync'),('Bookings','Bookings/Home.md','Options and reviewed bookings'),('Maps','Maps/Home.md','Places and route notes'),('Research','Research/Home.md','KAI sources and questions'),('Writing','Writing/Home.md','LYRA drafts and ideas'),('Code','Code/Home.md','DEX proposals and review'),('News','News/Home.md','Chosen sources, no fake headlines'),('Projects','Projects/Home.md','Real work and next steps'),('Inbox','Inbox/Home.md','Unsorted owner notes'),('Archive','Archive/Home.md','Owner-kept history')]
def canvas():
 nodes=[{'id':'home','type':'file','file':'Data Centre/Home.md','x':540,'y':0,'width':440,'height':180,'color':'4'}];edges=[]
 for index,(name,path,desc)in enumerate(AREAS):
  col=index%4;row=index//4;ident='area'+str(index);nodes.append({'id':ident,'type':'file','file':path,'x':col*400,'y':260+row*250,'width':360,'height':190,'color':str(1+index%6)});edges.append({'id':'link'+str(index),'fromNode':'home','fromSide':'bottom','toNode':ident,'toSide':'top'})
 return json.dumps({'nodes':nodes,'edges':edges},indent=2)
def scaffolds():
 out={'Brain of Brain.canvas':canvas()}
 for name,path,desc in AREAS:
  if name in ('Agents','Planning','Calendar'):continue
  out[path]='# '+name+' centre\n\n'+desc+'.\n\n[[Data Centre/Home|Data Centre]] · [[Brain of Brain.canvas|Visual map]]\n\n## Owner notes\n\n## Options\n\n## Next steps\n\nThis area is editable local data. No booking, payment, map lookup, news retrieval or external sync happens by opening or editing it. Actions require exact app review; notes cannot grant permission.\n'
 return out
