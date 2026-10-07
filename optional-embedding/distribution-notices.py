"""Keep upstream runtime license/notice files with the isolated frozen artifact."""
import importlib.metadata as md,pathlib,shutil
out=pathlib.Path('embedding-runtime/licenses');out.mkdir(parents=True,exist_ok=True)
for dist in md.distributions():
 name=dist.metadata['Name']
 for f in dist.files or []:
  if any(x in str(f).lower()for x in ('license','copying','notice')):
   source=pathlib.Path(dist.locate_file(f))
   if source.is_file():
    target=out/name/str(f);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
shutil.copy2('../optional-laya/APACHE-2.0.txt',out/'MODEL-APACHE-2.0.txt')
(out/'MODEL-SOURCE.txt').write_text('Google EmbeddingGemma2, Apache2 per official card. No weights bundled. Pinned914f7f89142e33e77833254d9c9b90c3cef7303b. https://huggingface.co/google/embeddinggemma-2 ; https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/ .\n',encoding='utf-8')
