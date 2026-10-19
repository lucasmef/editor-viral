"""Restore evicted venv package files from verified, same-version local uv cache.

Does not remove originals, change versions, or download packages. Bytecode is
excluded; callers can use a fresh pycache_prefix while iCloud is unavailable.
"""
import argparse, base64, csv, hashlib, io, json, os
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--apply', action='store_true')
p.add_argument('--report', type=Path, required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
installed=root/'.venv/lib/python3.12/site-packages'
cache=Path('/Users/lucas/.cache/uv/archive-v0')
evicted=lambda x: x.exists() and bool(x.stat().st_flags & 0x40000000)
packages={d.name:d for archive in cache.iterdir() if archive.is_dir()
          for d in archive.glob('*.dist-info') if not evicted(d/'RECORD')}
report={'applied':a.apply,'restored':[],'unavailable':[]}
for info in installed.glob('*.dist-info'):
    source_info=packages.get(info.name)
    if not source_info: continue
    base=source_info.parent
    for rel,expected,size in csv.reader(io.StringIO((source_info/'RECORD').read_text())):
        dest=installed/rel; source=base/rel
        if '..' in Path(rel).parts or not evicted(dest): continue
        if not expected.startswith('sha256=') or not source.is_file() or evicted(source):
            report['unavailable'].append(str(dest)); continue
        content=source.read_bytes()
        actual=base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip('=')
        if actual!=expected.split('=',1)[1] or len(content)!=int(size):
            raise ValueError('Cache integrity mismatch: '+str(source))
        if a.apply:
            temp=dest.with_name(dest.name+'.verified-restore.tmp')
            temp.write_bytes(content);temp.chmod(dest.stat().st_mode & 0o777)
            os.replace(temp,dest)
        report['restored'].append({'path':str(dest),'source':str(source),'sha256':hashlib.sha256(content).hexdigest()})
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(report,indent=2))
print(json.dumps({'restored':len(report['restored']),'unavailable':len(report['unavailable']),'report':str(a.report)}))
