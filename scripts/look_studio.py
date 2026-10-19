"""Native Remotion look editing; ephemeral TSX, canonical job geometry autosave."""
import argparse, copy, fcntl, json, math, os, subprocess, time, uuid, socket
from pathlib import Path
import studio as st
import studio_native as native


def parse(path):
 r=subprocess.run(['node',str(st.ROOT/'scripts/studio_geometry.cjs'),str(path)],capture_output=True,text=True)
 if r.returncode:raise ValueError(r.stderr.strip())
 return json.loads(r.stdout)


def apply_geometry(d, compiled, edits):
 out=copy.deepcopy(d); expected={}
 for original,scene in zip(out['project.json']['scenes'],compiled['scenes']):
  for layer,view in zip(original['layers'],scene['layers']):expected[view['id']]=(layer,view['rect'])
 if len(edits)!=len(expected) or {e['id'] for e in edits}!=set(expected):raise ValueError('Lista de peças alterada; só posição e tamanho são editáveis')
 changes=[]
 for e in edits:
  if any(type(e.get(k)) not in (int,float) or not math.isfinite(e[k]) for k in ('x','y','scale')) or not 0<e['scale']<=10:raise ValueError('Geometria inválida')
  layer,base=expected[e['id']]
  rect={'x':e['x'],'y':e['y'],'width':base['width']*e['scale'],'height':base['height']*e['scale']}
  if min(rect['x'],rect['y'])<0 or rect['x']+rect['width']>out['project.json']['width'] or rect['y']+rect['height']>out['project.json']['height']:raise ValueError('Peça fora do quadro; volte para dentro das guias')
  if any(abs(rect[k]-layer['rect'][k])>1e-7 for k in rect):
   changes.append({'id':e['id'],'before':copy.deepcopy(layer['rect']),'after':rect});layer['rect']=rect
 return out,changes


def save_geometry(job, baseline, compiled, edits):
 current=st.load(job)
 if st.digest(current)!=st.digest(baseline):raise ValueError('Projeto mudou fora desta sessão. Reabra o editor para evitar sobrescrever alterações')
 updated,changes=apply_geometry(current,compiled,edits)
 if changes:
  # Immutable receipt preserves the previous state, even if the process stops during publication.
  receipt=st.jobdir(job)/'history'/(str(time.time_ns())+'-studio-geometry.json')
  st.write(receipt,{'at':st.now(),'action':'studio-geometry','beforeProject':current['project.json'],'afterProject':updated['project.json'],'changes':changes},True)
  st.write(st.jobdir(job)/'project.json',updated['project.json'])
 return updated,len(changes)


def generate(compiled, session, status_rel, production=None):
 st.write(session/'compiled.json',compiled)
 st.write(session/'production.json',production or compiled)
 rows=[]
 for scene in compiled['scenes']:
  for index,l in enumerate(scene['layers']):
   r=l['rect']; zero=copy.deepcopy(l);zero['rect']={**r,'x':0,'y':0}
   props=copy.deepcopy(l.get('native',{}).get('props',{'name':scene['id']+' · '+l['id'],'style':{'position':'absolute','left':0,'top':0,'width':r['width'],'height':r['height'],'translate':str(r['x'])+'px '+str(r['y'])+'px','scale':1,'transformOrigin':'0% 0%'}}))
   props.update({'from':scene['from']+l['from'],'durationInFrames':l['duration']})
   zero.pop('native',None)
   attrs=' '.join(k+'={'+native.expression(v)+'}' for k,v in props.items())
   rows.append('<Interactive.Div data-piece='+json.dumps(l['id'])+' '+attrs+'><Asset plainImage layer={'+json.dumps(zero)+'}/></Interactive.Div>')
 source=f'''import React from 'react';
import {{Composition, Interactive, registerRoot, useCurrentFrame, useVideoConfig, interpolate, interpolateColors, spring, Easing, getRemotionEnvironment}} from 'remotion';
import {{FashionVideo, Asset}} from {json.dumps(str(st.ROOT/'src/Root'))};
import {{StudioSaveStatus}} from {json.dumps(str(st.ROOT/'src/StudioSaveStatus'))};
import data from './compiled.json';
import production from './production.json';
const Looks = () => <>{chr(10).join(rows)}</>;
const Video = () => <><FashionVideo {{...(getRemotionEnvironment().isRendering?production:data) as any}} lookContent={{<Looks/>}}/>{{!getRemotionEnvironment().isRendering&&<StudioSaveStatus path={json.dumps(status_rel)}/>}}</>;
const Root = () => <Composition id="Looks{compiled['videoId']}" component={{Video}} width={{{compiled['width']}}} height={{{compiled['height']}}} fps={{{compiled['fps']}}} durationInFrames={{{compiled['durationInFrames']}}}/>;
registerRoot(Root);
'''
 (session/'index.tsx').write_text(source)
 return session/'index.tsx'


def browser_media(p):
 """Browser proxy only; production keeps the original 4K finishing association."""
 sources={s['src'] for s in p['shots']}
 if p.get('source'):sources.add(p['source'])
 for src in sources:
  if Path(src).suffix.lower() not in ('.mov','.mxf'):continue
  original=st.public_dir()/src
  rel='studio-proxies/'+Path(src).stem+'-1080.mp4';dest=st.public_dir()/rel
  if not dest.exists():
   dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_name(dest.stem+'-'+uuid.uuid4().hex+'.mp4')
   subprocess.run([st.vh.binary('ffmpeg'),'-v','error','-i',str(original),'-vf','scale=-2:1920','-c:v','libx264','-preset','ultrafast','-crf','20','-c:a','aac','-b:a','192k','-movflags','+faststart',str(tmp)],check=True)
   os.replace(tmp,dest)
  for shot in p['shots']:
   if shot['src']==src:shot['src']=rel
  if p.get('source')==src:p['source']=rel
 return p


def main():
 ap=argparse.ArgumentParser();ap.add_argument('job');ap.add_argument('--port',type=int,default=3174);args=ap.parse_args()
 st.safe_id(args.job)
 with socket.socket() as probe:
  if probe.connect_ex(('127.0.0.1',args.port))==0:raise SystemExit('Porta ocupada; escolha outra com --port')
 root=st.paths()['cache']/args.job/'look-studio';root.mkdir(parents=True,exist_ok=True)
 lock=(root/'active.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Já existe uma sessão de edição deste vídeo')
 baseline=st.load(args.job);compiled=st.compile_job(baseline);production=copy.deepcopy(compiled);compiled=browser_media(compiled)
 session=root/uuid.uuid4().hex;session.mkdir()
 (session/'node_modules').symlink_to(st.ROOT/'node_modules',target_is_directory=True)
 st.write(session/'package.json',{**st.read(st.ROOT/'package.json'),'name':'look-studio-session','private':True})
 st.write(session/'tsconfig.json',st.read(st.ROOT/'tsconfig.json'))
 (session/'remotion.config.ts').write_text("import {Config} from '@remotion/cli/config';\nConfig.setPublicDir("+json.dumps(str(st.public_dir()))+");\n")
 status_rel='studio-status/'+session.name+'.json';status_path=st.public_dir()/status_rel
 entry=generate(compiled,session,status_rel,production);initial=native.parse(entry);last=entry.read_bytes()
 compiled['_nativeMedia']={sc['id']+'-'+l['id']:l.get('mediaId') for sc in baseline['project.json']['scenes'] for l in sc['layers']}
 compiled['_nativeOriginal']=copy.deepcopy(baseline['project.json'])
 st.write(session/'baseline.json',baseline)
 st.write(session/'native-snapshot.json',compiled)
 state={'ok':True,'message':'Salvo no projeto · controles nativos'}
 rejected=None
 def publish():st.write(status_path,{**state,'at':int(time.time()*1000)})
 publish()
 child=subprocess.Popen(['node','--require',str(st.ROOT/'scripts/studio_loopback.cjs'),str(st.ROOT/'node_modules/@remotion/cli/remotion-cli.js'),'studio',str(entry),'--port',str(args.port),'--no-open'],cwd=session)
 print(json.dumps({'url':f'http://127.0.0.1:{args.port}/Looks{args.job}','session':str(session)},ensure_ascii=False),flush=True)
 try:
  while child.poll() is None:
   try:
    current=entry.read_bytes()
    if current!=last and current!=rejected:
     state={'ok':False,'message':'Salvando ajustes…'};publish();time.sleep(.35)
     if entry.read_bytes()!=current:continue
     recovery=st.jobdir(args.job)/'studio-recovery'/session.name
     recovery.mkdir(parents=True,exist_ok=True)
     pending=recovery/'pending.tsx';temp=pending.with_suffix('.tmp');temp.write_bytes(current);os.replace(temp,pending)
     data=native.parse(entry)
     baseline=native.save(args.job,baseline,compiled,initial,data)
     st.write(session/'baseline.json',baseline)
     state={'ok':True,'message':'Salvo no projeto · controles nativos'};last=current;rejected=None
    elif st.digest(st.load(args.job))!=st.digest(baseline):
     state={'ok':False,'message':'Projeto alterado externamente — reabra esta sessão'}
    elif current==last and not state['ok']:
     state={'ok':True,'message':'Salvo no projeto · alteração inválida desfeita'}
   except Exception as e:
    rejected=current
    state={'ok':False,'message':'NÃO SALVO · '+str(e)}
   publish();time.sleep(.65)
 finally:
  child.terminate();state={'ok':False,'message':'Sessão encerrada'};publish()

if __name__=='__main__':main()
