"""Explicit local notes checkpoint. No cloud summary or silent context clearing."""
import datetime,os,tempfile
from pathlib import Path
def checkpoint(memory,directory):
    snapshot=memory.messages()
    if not snapshot:raise ValueError('No completed conversation to save.')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');destination=directory/('JARVIS-session-'+stamp+'.md')
    text='# JARVIS session notes\n\nLocal conversation checkpoint, not independently verified facts.\n\n## Recent recap\n'
    for m in snapshot[-8:]:text+='- '+m['role']+': '+m['content'][:300].replace('\n',' ')+'\n'
    text+='\n## Saved conversation\n'
    for m in snapshot:text+='\n### '+m['role']+'\n'+m['content']+'\n'
    fd,tmp=tempfile.mkstemp(dir=directory,prefix='.jarvis-',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,destination)
    finally:Path(tmp).unlink(missing_ok=True)
    memory.clear();return destination
