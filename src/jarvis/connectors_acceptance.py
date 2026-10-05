"""Frozen local vault and voice-command preparation acceptance, not hardware proof."""
import tempfile,pathlib,subprocess,json,os,queue,threading,time,http.server

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
   r=call('vault-search',query='வணக்கம்');assert r['data']['vault']['results'][0]['name']=='seed.md';assert r['data']['vault']['search']['complete']and r['data']['vault']['search']['scanned']==1
   assert call('vault-read',note_name='seed.md')['data']['vault']['note']=='Tamil local fixture வணக்கம்'
   assert call('vault-preview',text='obsidian search வணக்கம்')['data']['vault']['results'][0]['name']=='seed.md'
   assert call('vault-preview',text='Lyra vault read seed.md')['data']['vault']['note']=='Tamil local fixture வணக்கம்'
   assert not call('vault-preview',text='obsidian read ../outside.md')['ok']
   assert not call('vault-preview',text='obsidian create new.md')['ok']
   assert not call('vault-read',note_name='../outside.md')['ok']
   (vault/'.private').mkdir();(vault/'.private/hidden.md').write_text('hidden fixture')
   assert not call('vault-read',note_name='.private/hidden.md')['ok']
   assert not call('vault-create',note_name='.private/new.md',note_text='hidden',confirm=True,reviewed={'vault_folder':str(vault.resolve()),'note_name':'.private/new.md','note_text':'hidden'})['ok']
   assert not call('vault-create',note_name='new.md',note_text='review',confirm=True,reviewed={'vault_folder':str(vault.resolve()),'note_name':'new.md','note_text':'changed'})['ok']
   assert not call('vault-create',note_name='new.md',note_text='review')['ok']
   assert call('vault-create',note_name='new.md',note_text='review',confirm=True,reviewed={'vault_folder':str(vault.resolve()),'note_name':'new.md','note_text':'review'})['ok'];assert(vault/'new.md').read_text()=='review'
   assert not call('vault-create',note_name='new.md',note_text='overwrite',confirm=True,reviewed={'vault_folder':str(vault.resolve()),'note_name':'new.md','note_text':'overwrite'})['ok']
   for i in range(31):(vault/f'match-{i:03}.md').write_text('bounded-search',encoding='utf-8')
   limited=call('vault-search',query='bounded-search')['data']['vault'];assert limited['search']['reason']=='result-limit'and limited['search']['complete']is False and len(limited['results'])==30
   assert call('vault-disconnect')['data']['vault']['connected']is False;assert call('status')['data']['vault']['search']=={}
   assert not call('vault-preview',text='obsidian read seed.md')['ok']
   assert call('browser-mode',consent=True)['ok']
   assert not call('browser-preview',text='browser scroll down')['ok']
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
   assert not call('laya-mode')['ok'];assert call('laya-mode',consent=True)['data']['laya']['enabled']
   blocked=call('chat',text='Reo find the observed documentation link')['data'];assert blocked['reo_log'][-1]['state']=='blocked';assert blocked['browser']['pending']is None
   direct=call('chat',text='Lyra scroll slightly')['data'];assert direct['browser']['pending']['command']=='scroll-down-small';assert direct['reo_log'][-1]['state']=='review';assert direct['browser']['status']['url']==state['url']
   assert call('laya-stop')['data']['browser']['pending']is None
   assert call('laya-mode',consent=True)['data']['laya']['enabled']
   blank=call('chat',text='Reo open browser')['data']['browser']['pending'];assert blank=={'command':'open-window','value':''}
   assert call('status')['data']['browser']['status']['url']==state['url']
   assert not call('browser-run',reviewed=blank)['ok']
   assert call('browser-run',confirm=True,reviewed=blank)['ok']
   deadline=time.monotonic()+15
   while time.monotonic()<deadline:
    bs=call('status')['data']['browser']['status']
    if bs['state']=='ready':break
    time.sleep(.1)
   assert bs['url']=='about:blank',bs
   assert call('browser-preview',text='browser open example.com')['ok']
   review=call('status')['data']['browser']['pending'];assert call('browser-run',confirm=True,reviewed=review)['ok']
   deadline=time.monotonic()+20
   while time.monotonic()<deadline:
    bs=call('status')['data']['browser']['status']
    if bs['state']=='ready':break
    time.sleep(.1)
   assert call('browser-links')['ok']
   deadline=time.monotonic()+10
   while time.monotonic()<deadline:
    state=call('status')['data']['browser']['status']
    if state['state']=='ready'and state['links']:break
    time.sleep(.1)
   assert call('laya-propose',goal='Read the observed documentation link')['ok']
   deadline=time.monotonic()+8
   while time.monotonic()<deadline:
    result=call('status')['data']
    if not result['laya']['busy']:break
    time.sleep(.05)
   assert not result['laya']['busy']and result['laya']['error'],result['laya']
   assert result['browser']['pending']is None,result['browser']
   assert result['browser']['status']['url']==state['url'],result['browser']
   assert call('laya-stop')['data']['browser']['pending']is None

   assert call('browser-preview',text='browser choose link '+row['id'])['ok']
   review=call('status')['data']['browser']['pending']
   assert review['value']==row['url'],review
   assert call('browser-run',confirm=True,reviewed=review)['ok']
   deadline=time.monotonic()+30
   while time.monotonic()<deadline:
    state=call('status')['data']['browser']['status']
    if state['state']in ('ready','error'):break
    time.sleep(.2)
   assert state['state']=='ready',state
   assert state['url']=='https://www.iana.org/help/example-domains'and state['title']=='Example Domains',state
   pending=call('browser-preview',text='browser scroll down')['data']['browser']['pending']
   assert pending['expected_url']==state['url']
   assert call('browser-run',confirm=True,reviewed=pending)['ok']
   assert call('pause')['data']['browser']['enabled']is False
   call('close');p.wait(10)
   return {'frozen_inbuilt_laya_unloaded_refuses_proposal_no_autonomous_action':True,'frozen_vault':True,'bounded_search_completeness_and_result_limit':True,'explicit_local_vault_voice_parse_read_search':True,'read_search_create_no_overwrite':True,'outside_paths_rejected':True,'hidden_paths_read_create_rejected':True,'changed_vault_review_rejected':True,'browser_voice_parse':True,'scroll_exact_page_bound':True,'changed_review_rejected':True,'pause_browser_mode_off':True,'actual_Edge_navigation':True,'observed_links_and_exact_review':True,'actual_observed_link_navigation':True,'actual_final_url':state['url'],'physical_microphone':False}
  finally:
   if p.poll()is None:p.kill()
