"""Explicit, journaled same-volume relocation; rollback on failure, no deletions.
Run only for the installation being migrated. Old 174 is retired, never activated.
"""
import json
from pathlib import Path
import studio as s


def relocate(plan, journal, fail_after=None):
    """Preflight all destinations before moving, record every move, rollback failures."""
    plan=[(Path(a),Path(b)) for a,b in plan if Path(a).exists() or Path(a).is_symlink()]
    for a,b in plan:
        if b.exists() or b.is_symlink():raise ValueError('Destino já existe: '+str(b))
        parent=b.parent
        while not parent.exists():parent=parent.parent
        if a.lstat().st_dev!=parent.stat().st_dev:raise ValueError('Volumes diferentes')
    moved=[]
    def save(state):s.write(journal,{'state':state,'moves':moved,'plan':[[str(a),str(b)] for a,b in plan]})
    save('prepared')
    try:
        for a,b in plan:
            b.parent.mkdir(parents=True,exist_ok=True)
            inode=a.lstat().st_ino
            a.rename(b)
            moved.append({'from':str(a),'to':str(b),'inode':inode})
            if b.lstat().st_ino!=inode:raise ValueError('Identidade de arquivo mudou')
            with Path(str(journal)+'.events.jsonl').open('a') as f:f.write(json.dumps(moved[-1])+'\n')
            if len(moved)%500==0:print(f'Migrados {len(moved)}/{len(plan)}',flush=True)
            if fail_after and len(moved)==fail_after:raise RuntimeError('injected failure')
        save('completed')
    except BaseException:
        for entry in reversed(moved):
            a,b=Path(entry['from']),Path(entry['to']);a.parent.mkdir(parents=True,exist_ok=True)
            if a.exists():raise RuntimeError('Rollback requer inspeção: origem ocupada')
            b.rename(a)
        save('rolled-back')
        raise
    return moved


def external_files(actions, code_root):
    import os
    result=[]; covered=[]
    for source,dest in actions:
        if not source.exists() and not source.is_symlink():continue
        if dest.is_relative_to(code_root):
            result.append((source,dest));covered.append(source);continue
        if source.is_file() or source.is_symlink():entries=[source]
        else:
            entries=[]
            for base,dirs,files in os.walk(source,followlinks=False):
                entries += [Path(base)/name for name in files]
                entries += [Path(base)/name for name in dirs if (Path(base)/name).is_symlink()]
        for entry in entries:
            if not any(entry.is_relative_to(old) for old in covered):
                result.append((entry,dest/entry.relative_to(source) if entry!=source else dest))
        covered.append(source)
    return result

def plan():
    root=s.ROOT;r=s.paths();archive=r['edit']/'_editor/research/migration-20261013'
    actions=[]
    for name in ('venv','vendor','models','requirements.lock.txt'):
        actions.append((root/'analysis/hair-validation/library-review-v09'/name,root/'.runtime/hair'/name))
    actions += [(root/'library/processors',root/'.runtime/processors'),
                (root/'.cache/whisper-small',root/'.runtime/models/whisper-small'),
                (root/'analysis',archive/'analysis'),(root/'out',archive/'outputs'),
                (root/'reviews',archive/'reviews'),(root/'references',r['assets']/'174/references'),
                (root/'public/stills',r['assets']/'174/legacy-options'),
                (root/'library/assets',r['assets']/'_catalog'),
                (root/'public',r['cache']/'migration-20261013/public'),
                (root/'.cache',r['cache']/'migration-20261013/editor-cache'),
                (root/'jobs',archive/'retired-jobs'),(root/'library',archive/'retired-library')]
    return external_files(actions,root)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    actions=plan()
    if a.apply:
        journal=s.paths()['edit']/'_editor/migrations/20261013-relocation-v3.json'
        if journal.exists():raise ValueError('Journal já existe: inspecionar antes de retomar')
        print(json.dumps(relocate(actions,journal),indent=2))
    else:print(json.dumps([[str(a),str(b)] for a,b in actions],indent=2))
