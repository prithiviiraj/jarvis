"""Frozen local vault and voice-command preparation acceptance, not hardware proof."""
import tempfile,pathlib,subprocess,json,os,queue,threading,time

def run(core):
 with tempfile.TemporaryDirectory()as t:
  root=pathlib.Path(t);vault=root/'notes';vault.mkdir();(vault/'.obsidian').mkdir();(vault/'seed.md').write_text('Tamil local fixture வணக்கம்',encoding='utf-8')
  env=dict(os.environ);env['JARVIS_DATA_DIR']=str(root/'data')
  p=subprocess.Popen([core],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',env=env);q=queue.Queue()
  def drain():
   for line in p.stdout:q.put(line)
  threading.Thread(target=drain,daemon=True).start()
  def call(command,**extra):
   p.stdin.write(json.dumps(dict(command=command,**extra))+'\n');p.stdin.flush();return json.loads(q.get(timeout=15))
  try:
   assert not call('vault-connect',vault_folder=str(vault))['ok']
   assert call('vault-connect',vault_folder=str(vault),consent=True)['data']['vault']['connected']
   r=call('vault-search',query='வணக்கம்');assert r['data']['vault']['results'][0]['name']=='seed.md'
   assert call('vault-read',note_name='seed.md')['data']['vault']['note']=='Tamil local fixture வணக்கம்'
   assert not call('vault-read',note_name='../outside.md')['ok']
   assert not call('vault-create',note_name='new.md',note_text='review')['ok']
   assert call('vault-create',note_name='new.md',note_text='review',confirm=True)['ok'];assert(vault/'new.md').read_text()=='review'
   assert not call('vault-create',note_name='new.md',note_text='overwrite',confirm=True)['ok']
   assert call('vault-disconnect')['data']['vault']['connected']is False
   assert call('browser-mode',consent=True)['ok']
   pending=call('browser-preview',text='Jarvis browser open example.com')['data']['browser']['pending'];assert pending=={'command':'open','value':'https://example.com'}
   assert not call('browser-run',confirm=True,reviewed={'command':'search','value':'wrong'})['ok']
   assert not call('browser-preview',text='browser open localhost')['ok']
   pending=call('browser-preview',text='browser open example.com')['data']['browser']['pending']
   assert call('browser-run',confirm=True,reviewed=pending)['ok']
   deadline=time.monotonic()+35
   while time.monotonic()<deadline:
    state=call('status')['data']['browser']['status']
    if state['state']in ('ready','error'):break
    time.sleep(.2)
   assert state['state']=='ready',state
   assert state['url'].startswith('https://example.com')and'Example Domain'in state['title'],state
   assert call('browser-preview',text='browser read links')['ok']
   deadline=time.monotonic()+20
   while time.monotonic()<deadline:
    state=call('status')['data']['browser']['status']
    if state['state']in ('ready','error'):break
    time.sleep(.2)
   assert state['state']=='ready'and state['links'],state
   row=state['links'][0];assert row['url'].startswith('https://')
   assert call('browser-preview',text='browser choose link '+row['id'])['ok']
   review=call('status')['data']['browser']['pending']
   assert review['value']==row['url'],review
   pending=call('browser-preview',text='browser scroll down')['data']['browser']['pending']
   assert call('browser-run',confirm=True,reviewed=pending)['ok']
   assert call('pause')['data']['browser']['enabled']is False
   call('close');p.wait(10)
   return {'frozen_vault':True,'read_search_create_no_overwrite':True,'outside_paths_rejected':True,'browser_voice_parse':True,'changed_review_rejected':True,'pause_browser_mode_off':True,'actual_Edge_navigation':True,'observed_links_and_exact_review':True,'physical_microphone':False}
  finally:
   if p.poll()is None:p.kill()
