import pathlib,sys,json,html
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.vault_canvas import canvas
j=json.loads(canvas());out=['<!doctype html><html><head><style>body{margin:0;background:#161b23;color:#dae4ef;font:18px Segoe UI,Arial}.board{position:relative;width:1420px;height:1160px;margin:32px}.node{position:absolute;box-sizing:border-box;background:#202935;border:1px solid #46576b;border-radius:18px;padding:22px}.section{background:transparent;border:0;padding:4px 12px;color:#86bcb5}h2{margin:0 0 12px;font-size:26px}p{line-height:1.4;font-size:18px;color:#aabccd}.link{color:#87d6c7;font-size:18px;margin-top:24px}.home{text-align:center;background:#263b3e;border-color:#78a9a0}.label{position:absolute;top:2px;right:8px;color:#96a6b4;font-size:13px}</style></head><body><div class="board"><div class="label">Canvas geometry preview from generated JSON · native Obsidian not verified</div>']
for n in j['nodes']:
 cls='section'if n['id'].startswith('section')else'home'if n['id']=='home'else''
 if n['type']=='file':title='Brain of Brain';desc='Your local data centre';link='Open the visual map and managed notes'
 else:
  parts=n['text'].split('\n');title=parts[0].lstrip('# ');desc=next((x for x in parts[1:]if x and not x.startswith('[[')),'');link=next((x.split('|')[-1].rstrip(']')for x in parts if x.startswith('[[')),'')
 out.append(f'<div class="node {cls}" style="left:{n["x"]}px;top:{n["y"]}px;width:{n["width"]}px;height:{n["height"]}px"><h2>{html.escape(title)}</h2><p>{html.escape(desc)}</p><div class="link">{html.escape(link)}</div></div>')
out.append('</div></body></html>');pathlib.Path('ui-evidence/canvas-geometry.html').write_text(''.join(out));pathlib.Path('ui-evidence/canvas-source.json').write_text(json.dumps(j,indent=2))
