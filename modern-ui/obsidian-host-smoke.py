"""Actual installed Obsidian Canvas acceptance in isolated Windows runner, never bundled."""
import pathlib,tempfile,subprocess,os,json,time,hashlib,urllib.request,sys
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'src'))
from jarvis.obsidian_vault import Vault,NAME
url='https://github.com/obsidianmd/obsidian-releases/releases/download/v1.9.14/Obsidian-1.9.14.exe';digest='e6b8f82ccfcda4553a35efdfd17a56935b08543e82078d5aa1404d282cecf9ac'
installer=pathlib.Path(tempfile.gettempdir())/'obsidian-fixture-1.9.14.exe'
if not installer.exists():urllib.request.urlretrieve(url,installer)
assert hashlib.sha256(installer.read_bytes()).hexdigest()==digest,'Official installer checksum mismatch'
install=pathlib.Path(tempfile.gettempdir())/'obsidian-host-fixture'
subprocess.run([str(installer),'/S','/D='+str(install)],check=True,timeout=120)
exe=install/'Obsidian.exe';assert exe.is_file()
with tempfile.TemporaryDirectory()as fixture:
 base=pathlib.Path(fixture);vault=Vault(base/'config.json',lambda:base);vault.create(NAME,True);vault.sync([],{'agents':[]},{},force=True);root=base/NAME
 profile=base/'profile';profile.mkdir();(profile/'obsidian.json').write_text(json.dumps({'vaults':{'fixture':{'path':str(root),'ts':int(time.time()*1000),'open':True}}}),encoding='utf-8')
 (root/'.obsidian').mkdir(exist_ok=True);(root/'.obsidian/app.json').write_text(json.dumps({'alwaysUpdateLinks':False}),encoding='utf-8')
 p=subprocess.Popen([str(exe),'--user-data-dir='+str(profile),'--remote-debugging-port=9229','--disable-gpu','--no-sandbox'])
 try:
  deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   try:
    with urllib.request.urlopen('http://127.0.0.1:9229/json/version',timeout=1)as r:json.load(r)
    break
   except Exception:time.sleep(.3)
  else:raise RuntimeError('Obsidian debugging endpoint unavailable')
  with sync_playwright()as pw:
   browser=pw.chromium.connect_over_cdp('http://127.0.0.1:9229');pages=[page for context in browser.contexts for page in context.pages];page=next((x for x in pages if x.url.startswith('app://')),pages[0]);page.wait_for_function('window.app && app.vault && app.workspace',timeout=40000)
   # App exists before its vault index is ready. Confirm actual fixture path and file.
   try:
    page.wait_for_function("()=>app.vault.getAbstractFileByPath('Brain of Brain.canvas') && app.vault.getFiles().length>=13",timeout=35000)
    actual=page.evaluate("()=>app.vault.adapter.getBasePath()")
    assert pathlib.Path(actual).resolve()==root.resolve(),('Wrong fixture vault',actual,str(root))
   except Exception:
    page.screenshot(path='ui-evidence/actual-obsidian-readiness-failure.png')
    pathlib.Path('ui-evidence/actual-obsidian-readiness-failure.json').write_text(json.dumps(page.evaluate("()=>({url:location.href,path:app.vault.adapter.getBasePath?.(),files:app.vault.getFiles().map(f=>f.path),text:document.body.innerText.slice(0,6000)})"),indent=2),encoding='utf-8')
    raise
   # Test-owned fixture navigation only; no note edits or external plugins.
   page.evaluate("async()=>{const f=app.vault.getAbstractFileByPath('Brain of Brain.canvas');if(!f)throw Error('Fixture canvas missing');await app.workspace.getLeaf(false).openFile(f);}")
   page.wait_for_function("app.workspace.activeLeaf?.view?.getViewType()==='canvas'",timeout=15000)
   page.wait_for_selector('.canvas-node',timeout=15000)
   result=page.evaluate("()=>({version:app.getVersion?.(),type:app.workspace.activeLeaf.view.getViewType(),nodes:document.querySelectorAll('.canvas-node').length,canvas:app.workspace.activeLeaf.view.getData?.()})")
   assert result['nodes']==13,result
   fixture_canvas=json.loads((root/'Brain of Brain.canvas').read_text(encoding='utf-8'))
   assert len(fixture_canvas['nodes'])==13 and len(fixture_canvas['edges'])==12
   result['source_edges']=len(fixture_canvas['edges'])
   if result.get('canvas'):assert len(result['canvas']['nodes'])==13 and len(result['canvas']['edges'])==12
   page.screenshot(path='ui-evidence/actual-obsidian-canvas.png',full_page=False)
   pathlib.Path('ui-evidence/actual-obsidian-canvas-checks.json').write_text(json.dumps({'scope':'Actual Obsidian1.9.14 Windows fixture host, not owner laptop','installer_url':url,'sha256':digest,'result':result},indent=2),encoding='utf-8')
   browser.close()
 finally:
  # Electron subprocesses can keep fixture Cookies locked after parent termination.
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
  time.sleep(.5)
print('Actual Windows Obsidian Canvas13nodes/12links gate passed')
