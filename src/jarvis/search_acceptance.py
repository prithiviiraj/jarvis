"""Explicit frozen optional English search acceptance using temporary synthetic vault."""
def run():
 import pathlib,tempfile,time,json
 from .experimental.static_vault_search import SearchSetup,search,ASSETS
 from .obsidian import Vault
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True);setup=SearchSetup();worker=setup.start(consent=True);worker.join(90)
 assert not setup.busy and setup.model is not None,setup.error
 with tempfile.TemporaryDirectory()as t:
  root=pathlib.Path(t);(root/'.obsidian').mkdir();(root/'dinner.md').write_text('Reserve a restaurant table for four people.');(root/'school.md').write_text('Wind turbines turn moving air into electricity.');(root/'.secret.md').write_text('secret dinner');start=time.perf_counter();r=search(Vault(root),'book dinner for four',setup.model,True);seconds=time.perf_counter()-start;assert r['results'][0]['name']=='dinner.md';assert len(r['results'])==2
  try:search(Vault(root),'மருந்து',setup.model,True)
  except ValueError:pass
  else:raise AssertionError('Tamil must stay exact-search only')
 report={'frozen_executable':bool(getattr(__import__('sys'),'frozen',False)),'actual_model2vec_CPU':True,'bytes':sum(v[0]for v in ASSETS.values()),'temporary_vault_top1':'dinner.md','seconds':seconds,'hidden_excluded':True,'Tamil_rejected':True,'scope':'two easy synthetic English notes only; no private vault, user-laptop or broad accuracy proof'};setup.stop();(out/'frozen-search-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
