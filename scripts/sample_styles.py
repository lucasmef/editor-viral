"""Render up to three presentation options on one scene frame, without job edits.

Inputs are an immutable evidence options JSON and scene-local frame. Uses the
studio compiler, media staging and external destinations; never emits a master.
"""
import argparse,copy,json,shutil,subprocess,uuid
from pathlib import Path
import studio as s

p=argparse.ArgumentParser();p.add_argument('job');p.add_argument('--scene',required=True);p.add_argument('--frame',type=int,required=True);p.add_argument('--options',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
d=s.load(a.job);sc=next(x for x in d['project.json']['scenes'] if x['id']==a.scene)
if not 0<=a.frame<sc['duration']:raise ValueError('Frame fora da cena')
opts=s.read(a.options)
if not 1<=len(opts)<=3:raise ValueError('Use de uma a três opções')
out=s.output_path(a.out)
if out.exists():raise ValueError('Escolha diretório novo')
out.mkdir(parents=True);compiled=s.compile_job(d,False)
frame=sum(x['duration'] for x in d['project.json']['scenes'][:d['project.json']['scenes'].index(sc)])+a.frame
with s.render_workspace(s.paths()['cache']) as public:
 sources={x['src'] for x in compiled['shots']}|{l['src'] for x in compiled['scenes'] for l in x['layers'] if l.get('src')}
 for key in ('source','audioSrc'):
  if compiled.get(key):sources.add(compiled[key])
 sources.update(c['src'] for c in compiled.get('soundEffects',[]))
 for src in sources:
  dest=public/src;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s.public_dir()/src,dest)
 records=[]
 for i,option in enumerate(opts,1):
  props=copy.deepcopy(compiled);props['layout']=option['layout'];manifest=out/f'option-{i}.props.json';s.write(manifest,props,True)
  image=out/f'option-{i}.png'
  subprocess.run(['pnpm','exec','remotion','still','src/index.ts','FashionVideo',str(image),'--props',str(manifest),'--frame',str(frame),'--scale=0.5','--public-dir',str(public),'--bundle-cache=false'],cwd=s.ROOT,check=True)
  records.append({'option':i,'label':option['label'],'path':str(image),'sha256':s.sha(image),'manifestSha256':s.sha(manifest)})
s.write(out/'report.json',{'job':a.job,'scene':a.scene,'localFrame':a.frame,'timelineFrame':frame,'fingerprints':s.fingerprints(d),'options':records,'optionsInputSha256':s.sha(a.options),'approved':False},True)
print(json.dumps(records,indent=2))
