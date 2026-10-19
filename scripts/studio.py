"""Versioned local editing jobs. Temporary render copies are cleaned; no editorial deletion or automatic approval."""
import argparse, copy, hashlib, json, os, re, shutil, subprocess, sys, uuid, time
from datetime import datetime, timezone
from pathlib import Path
import video_harness as vh
import caption_rules
import voice_connector
import hair_connector
import finishing_windows
import storage
from render_cache import render_workspace, stage_copy
from pipeline_cache import Metrics
ROOT=Path(__file__).resolve().parents[1]
STAGES=('preproduction','production','postproduction')
DOCS=('project.json','brief.json','looks.json','style.json','finishing.json')

def now():return datetime.now(timezone.utc).isoformat()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,data,exclusive=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if exclusive:
  with p.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2)
 else:
  tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));os.replace(tmp,p)
def safe_id(value):
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',value):raise ValueError('ID inválido')
 return value
def paths():return storage.roots(ROOT)
def jobhome(job):return paths()['edit']/safe_id(job)
def jobdir(job):return jobhome(job)/'project'
def catalog_path():return paths()['edit']/'_editor/media.json'
def public_dir():return paths()['cache']/'staging'
def output_path(path):return storage.external_output(ROOT,path)
def persistent_path(path):
 p=output_path(path)
 if (ROOT/'studio/storage.json').exists() and p.is_relative_to(paths()['cache'].resolve()):raise ValueError('Acabamento associado não pode ficar em Cache; executar em Edit')
 return p
def run_dir(job,kind):return jobhome(job)/kind/(now().replace(':','-')+'-'+uuid.uuid4().hex[:8])
def log(job,action,**details):
 p=jobdir(job)/'history';p.mkdir(parents=True,exist_ok=True)
 write(p/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'-'+uuid.uuid4().hex[:8]+'.json'),{'at':now(),'action':action,**details},True)
def registry():
 p=catalog_path();return read(p) if p.exists() else {'schemaVersion':1,'media':{}}
def register(path,kind,archive=None,inspect=True):
 path=Path(path).resolve();h=sha(path);mid='m-'+h
 r=registry()
 if mid not in r['media']:
  r['media'][mid]={'sha256':h,'kind':kind,'filename':path.name,'bytes':path.stat().st_size,'locations':[],'archiveLocations':[],'metadata':vh.probe(path) if inspect and kind in ('original','proxy','audio','video') else None}
 m=r['media'][mid]
 if str(path) not in m['locations']:m['locations'].append(str(path))
 if archive and archive not in m['archiveLocations']:m['archiveLocations'].append(archive)
 # Small persistent assets are content-addressed copies, not references to disposable renders.
 if kind in ('still','font','sfx'):
  dest=paths()['soundfx' if kind=='sfx' else 'assets']/'_catalog'/(h+path.suffix.lower());dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copy2(path,dest)
  if str(dest) not in m['locations']:m['locations'].insert(0,str(dest))
 write(catalog_path(),r);return mid

def resolve(mid,verify=True):
 m=registry()['media'].get(mid)
 if not m:raise ValueError('Mídia desconhecida: '+mid)
 for s in m['locations']:
  p=Path(s)
  if p.is_file() and (not verify or sha(p)==m['sha256']):return p
 raise ValueError('Mídia offline ou modificada: '+m['filename'])
def relink(mid,path,archive=False):
 r=registry();m=r['media'][mid];p=Path(path).resolve()
 if sha(p)!=m['sha256']:raise ValueError('Arquivo diferente: SHA-256 não corresponde; reconexão recusada')
 if str(p) not in m['locations']:m['locations'].append(str(p))
 if archive:
  m['verifiedArchive']={'path':str(p),'sha256':m['sha256'],'verifiedAt':now()}
 write(catalog_path(),r);return {'mediaId':mid,'path':str(p),'matched':True}
def load(job):return {n:read(jobdir(job)/n) for n in DOCS}
def engine():
 paths=[ROOT/'package.json',ROOT/'pnpm-lock.yaml',ROOT/'remotion.config.ts']+sorted((ROOT/'src').glob('*.ts*'))+sorted((ROOT/'scripts').glob('*.py'))+sorted((ROOT/'scripts').glob('*.cjs'))
 return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}
def media_ids(d):
 p=d['project.json'];ids=set()
 for s in p['scenes']:
  ids.add(s['clip']['mediaId'])
  if s['clip'].get('proxy'):ids.add(s['clip']['proxy']['mediaId'])
  ids.update(l['mediaId'] for l in s['layers'] if l.get('mediaId'))
  ids.update(l['premiereMediaId'] for l in s['layers'] if l.get('premiereMediaId'))
 ids.update(l['mediaId'] for l in d['style.json']['layout']['labels'] if l.get('mediaId'))
 ids.update(c['mediaId'] for c in d['finishing.json'].get('soundEffects',[]) if c.get('mediaId'))
 for key in ('audioMediaId','videoMediaId'):
  if d['finishing.json'].get(key):ids.add(d['finishing.json'][key])
 window_output=d['finishing.json'].get('windows',{})
 if window_output.get('videoMediaId'):ids.add(window_output['videoMediaId'])
 hair_output=d['finishing.json'].get('hair',{}).get('output',{})
 if hair_output.get('mediaId'):ids.add(hair_output['mediaId'])
 return sorted(ids)
def fingerprints(d):
 p=d['project.json'];pre=digest({'brief':d['brief.json'],'looks':d['looks.json'],'format':[p['width'],p['height'],p['fps']],'cuts':[{'id':s['id'],'clip':{k:v for k,v in s['clip'].items() if k!='proxy'},'duration':s['duration'],'script':s['script']} for s in p['scenes']]})
 if 'editorialMode' in p:pre=digest({'pre':pre,'editorialMode':p['editorialMode']})
 prod=digest({'pre':pre,'scenes':p['scenes'],'requireLookReview':p.get('requireLookReview',False),'style':d['style.json'],'engine':engine()})
 return {'preproduction':pre,'production':prod,'postproduction':digest({'production':prod,'finishing':d['finishing.json']})}
def checkpoint(job,note):
 d=load(job);r=registry();ids=media_ids(d)
 missing=[m for m in ids if m not in r['media']]
 if missing:raise ValueError('IDs não registrados: '+str(missing))
 snapshot={'schemaVersion':1,'job':job,'documents':d,'engine':engine(),'media':{m:{k:v for k,v in r['media'][m].items() if k not in ('locations','verifiedArchive')} for m in ids}}
 rev=digest(snapshot)[:20];directory=jobdir(job)/'revisions'/rev
 if not directory.exists():
  directory.mkdir(parents=True)
  write(directory/'snapshot.json',snapshot,True)
  for rel in snapshot['engine']:
   dest=directory/'engine'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
 log(job,'checkpoint',revision=rev,note=note);return rev

def read_snapshot(job,revision):
 directory=jobdir(job)/'revisions'/safe_id(revision);snapshot=read(directory/'snapshot.json')
 if digest(snapshot)[:20]!=revision:raise ValueError('Snapshot alterado; checksum inválido')
 for rel,h in snapshot['engine'].items():
  if sha(directory/'engine'/rel)!=h:raise ValueError('Motor arquivado alterado')
 return snapshot

def init_job(job,brief,mode='fashion'):
 if mode not in ('fashion','no-looks'):raise ValueError('Modo editorial inválido')
 if jobdir(job).exists():raise ValueError('Projeto já existe')
 docs={'project.json':{'schemaVersion':2,'videoId':job,'width':1440,'height':2560,'fps':60,'scenes':[]},'brief.json':{'text':brief},'looks.json':{'state':'planning','options':[]},'style.json':read(ROOT/'studio/default-style.json'),'finishing.json':{'audioGainDb':0,'retouch':'pending','color':'pending','soundEffects':[]}}
 if mode=='no-looks':
  docs['project.json'].update(editorialMode=mode,requireLookReview=False)
  docs['looks.json']={'state':'not-applicable','reason':'Explicit no-looks editorial mode','options':[]}
  docs['style.json']=read(ROOT/'studio/no-looks-style.json')
 profile=voice_connector.defaults(sys.modules[__name__]) if mode=='fashion' else None
 if profile:docs['finishing.json']['voiceNeural']=profile
 for n,d in docs.items():write(jobdir(job)/n,d,True)
 log(job,'created',brief=brief);return {'job':job,'stage':'preproduction'}

def records(job):
 return [read(p) for p in sorted((jobdir(job)/'approvals').glob('*.json'))]
def valid_record(rec,fp):
 try:return rec['fingerprint']==fp and sha(rec['evidence'])==rec['evidenceSha256'] and rec['decision']=='approved'
 except (OSError,KeyError):return False

def look_fingerprints(d):
 p=d['project.json'];result={}
 for scene in p['scenes']:
  layers={l['id']:l for l in scene['layers']}
  for look in scene.get('looks',[]):
   key=scene['id']+':'+look['id']
   if key in result or not look.get('layerIds') or any(x not in layers for x in look['layerIds']):raise ValueError('Look duplicado ou com camadas inválidas: '+key)
   result[key]=digest({'look':look,'layers':[layers[x] for x in look['layerIds']],'clip':scene['clip'],'duration':scene['duration'],'script':scene['script'],'events':scene.get('events',[]),'captions':scene.get('captions',[]),'style':d['style.json'],'format':[p['width'],p['height'],p['fps']],'engine':engine()})
 return result

def look_status(job,d=None):
 d=d or load(job);result={};rs=[read(p) for p in sorted((jobdir(job)/'look-reviews').glob('*.json'))]
 for key,fp in look_fingerprints(d).items():
  candidates=[r for r in rs if r['look']==key];last=candidates[-1] if candidates else None
  state='approved' if last and valid_record(last,fp) else ('stale' if last and last['decision']=='approved' else ('rejected' if last else 'pending'))
  result[key]={'state':state,'fingerprint':fp}
 return result

def review_look(job,key,evidence,reviewer,decision='approved'):
 states=look_status(job)
 if key not in states:raise ValueError('Look não cadastrado: '+key)
 e=Path(evidence).resolve();content=read(e)
 if not reviewer.strip() or not content.get('notes') or not content.get('userApproval'):raise ValueError('Revisão exige responsável, notas e decisão real do usuário')
 if content.get('fingerprint')!=states[key]['fingerprint']:raise ValueError('Evidência de outra versão do look')
 if decision=='approved' and any(content.get('checks',{}).get(k)!='passed' for k in ('styling','cutout','composition','timing')):raise ValueError('Revisão do look incompleta')
 record={'look':key,'fingerprint':states[key]['fingerprint'],'at':now(),'decision':decision,'reviewer':reviewer,'evidence':str(e),'evidenceSha256':sha(e)}
 write(jobdir(job)/'look-reviews'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),record,True);log(job,'look-review',**record);return record

def scene_frames(d,scene_id):
 cursor=0
 for scene in d['project.json']['scenes']:
  if scene['id']==scene_id:return f"{cursor}-{cursor+scene['duration']-1}"
  cursor+=scene['duration']
 raise ValueError('Cena inexistente: '+scene_id)

def status(job):
 d=load(job);fps=fingerprints(d);rs=records(job);states={}
 for stage in STAGES:
  candidates=[r for r in rs if r['stage']==stage];last=candidates[-1] if candidates else None
  states[stage]='approved' if last and valid_record(last,fps[stage]) else ('stale' if last and last['decision']=='approved' else 'pending')
 looks=look_status(job,d)
 if d['project.json'].get('requireLookReview') and (not looks or any(x['state']!='approved' for x in looks.values())):
  if states['production']=='approved':states['production']='blocked-by-looks'
 media=[]
 for mid in media_ids(d):
  try:p=resolve(mid);state='online'
  except ValueError:p=None;state='offline'
  media.append({'id':mid,'state':state,'path':str(p) if p else None})
 import editor_state
 return {'workflow':editor_state.resume(job),'job':job,'windows':d['finishing.json'].get('windows'),'hair':hair_connector.summary(sys.modules[__name__],d),'voice':voice_connector.summary(sys.modules[__name__],d,states),'looks':looks,'lookReviewRequired':d['project.json'].get('requireLookReview',False),'checkpoints':states,'next':next((s for s in STAGES if states[s]!='approved'),'final-review'),'media':media,'fingerprints':fps}
def approve(job,stage,evidence,reviewer,decision='approved'):
 if stage not in STAGES:raise ValueError('Etapa inválida')
 e=Path(evidence).resolve();content=read(e)
 # Evidence explicitly captures human approval and actual review coverage, not mere file presence.
 d=load(job)
 mode_errors=editorial_mode_errors(d)
 if mode_errors:raise ValueError('; '.join(mode_errors))
 required={'preproduction':['cuts','looks'],'production':['gestures','captions','stills','visual'],'postproduction':['audio','color','retouch']}[stage]
 if d['project.json'].get('editorialMode')=='no-looks':
  required=[k for k in required if k!='looks' and (k!='stills' or any(sc['layers'] for sc in d['project.json']['scenes']))]
 if not reviewer.strip() or not content.get('notes') or not content.get('userApproval'):raise ValueError('Informe responsável, notas e a aprovação real do usuário em userApproval')
 optional={'gestures','retouch','color'}
 if decision=='approved' and any(content.get('checks',{}).get(k) not in (('passed','not-applicable') if k in optional else ('passed',)) for k in required):raise ValueError('Revisão incompleta: '+', '.join(required))
 s=status(job)
 if decision=='approved' and stage=='production' and s['lookReviewRequired'] and (not s['looks'] or any(x['state']!='approved' for x in s['looks'].values())):raise ValueError('Revisões individuais de looks pendentes')
 if decision=='approved' and any(s['checkpoints'][x]!='approved' for x in STAGES[:STAGES.index(stage)]):raise ValueError('Checkpoint anterior pendente ou desatualizado')
 if content.get('fingerprint')!=s['fingerprints'][stage]:raise ValueError('Evidência deve identificar fingerprint atual da etapa')
 if decision=='approved' and stage=='postproduction':voice_connector.validate_attached(sys.modules[__name__],load(job),required=True)
 dest=jobdir(job)/'approvals'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
 record={'stage':stage,'fingerprint':s['fingerprints'][stage],'at':now(),'reviewer':reviewer,'decision':decision,'evidence':str(e),'evidenceSha256':sha(e)};write(dest,record,True);log(job,'review',**record);return record

def fork(job,revision,new):
 dest=jobdir(new)
 if dest.exists():raise ValueError('Destino já existe')
 snap=read_snapshot(job,revision)
 dest.mkdir(parents=True)
 for n,d in snap['documents'].items():
  d=copy.deepcopy(d)
  if n=='project.json':d['videoId']=new;d['parent']={'job':job,'revision':revision}
  write(dest/n,d,True)
 log(new,'fork',parent={'job':job,'revision':revision});return {'job':new,'engineMatches':snap['engine']==engine(),'approvals':'pending'}

def assemble(new,selections):
 """References are JOB:REVISION:SCENE, each pinned to an immutable snapshot."""
 if jobdir(new).exists():raise ValueError('Destino já existe')
 docs=None;scenes=[];origins=[];looks=[]
 for item in selections:
  job,rev,sid=item.split(':');snap=read_snapshot(job,rev);d=snap['documents'];p=d['project.json']
  if docs is None:docs=copy.deepcopy(d)
  elif docs['style.json']!=d['style.json']:raise ValueError('Estilos diferentes; escolher um estilo explicitamente antes de mesclar')
  if (p['width'],p['height'],p['fps'])!=(docs['project.json']['width'],docs['project.json']['height'],docs['project.json']['fps']):raise ValueError('Formatos incompatíveis; normalizar explicitamente antes de mesclar')
  s=copy.deepcopy(next(s for s in p['scenes'] if s['id']==sid));origin={'job':job,'revision':rev,'scene':sid};s['origin']=origin;s['id']=f'scene-{len(scenes)+1}';scenes.append(s);origins.append(origin);looks.append({'origin':origin,'plan':d['looks.json']})
 if not docs:raise ValueError('Selecione ao menos uma cena')
 docs['project.json'].update(videoId=new,scenes=scenes,origins=origins)
 docs['brief.json']={'intent':'Remontagem; conferir continuidade e estilo','origins':origins}
 docs['looks.json']={'inherited':looks};docs['finishing.json']={'audioGainDb':0,'retouch':'pending','color':'pending','soundEffects':[]}
 profile=voice_connector.defaults(sys.modules[__name__])
 if profile:docs['finishing.json']['voiceNeural']=profile
 for n,d in docs.items():write(jobdir(new)/n,d,True)
 log(new,'assemble',origins=origins);return {'job':new,'approvals':'pending'}

def editorial_mode_errors(d):
 p=d['project.json'];mode=p.get('editorialMode','fashion')
 if mode not in ('fashion','no-looks'):return ['Modo editorial inválido']
 if mode=='no-looks' and (p.get('requireLookReview') or any(sc.get('looks') for sc in p.get('scenes',[])) or d['looks.json'].get('options') or d['looks.json'].get('inherited')):
  return ['Modo sem looks incompatível com looks cadastrados ou revisão de looks obrigatória']
 return []

def validate_job(d):
 p=d['project.json'];errors=editorial_mode_errors(d);seen=set()
 if p.get('schemaVersion')!=2:errors.append('schemaVersion deve ser 2')
 for k in ('width','height','fps'):
  if type(p.get(k)) is not int or p[k]<=0:errors.append(k+' inválido')
 for s in p.get('scenes',[]):
  if s['id'] in seen:errors.append('Cena duplicada')
  seen.add(s['id']);dur=s['duration'];clip=s['clip']
  if type(dur) is not int or dur<=0:errors.append('Duração inválida')
  if type(clip.get('inFrame')) is not int or clip['inFrame']<0:errors.append('Corte inválido')
  events={e['id']:e for e in s.get('events',[])}
  if len(events)!=len(s.get('events',[])):errors.append('Eventos duplicados')
  for e in events.values():
   if e.get('kind') not in ('word','gesture') or type(e.get('frame')) is not int or not 0<=e['frame']<dur:errors.append('Evento fora da cena')
  for l in s['layers']:
   if l.get('anchor') and l['anchor'] not in events:errors.append('Âncora inexistente')
  for c in s.get('captions',[]):
   if type(c['from']) is not int or type(c['duration']) is not int or c['from']<0 or c['duration']<=0 or c['from']+c['duration']>dur:errors.append('Legenda fora da cena')
 if not p.get('scenes'):errors.append('Nenhuma cena')
 return errors

def stage_file(mid):
 path=resolve(mid);dest=public_dir()/'harness'/(mid+path.suffix.lower());dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.is_symlink():
  if dest.resolve()!=path:dest.unlink();dest.symlink_to(path)
 elif not dest.exists():dest.symlink_to(path)
 elif sha(dest)!=registry()['media'][mid]['sha256']:raise ValueError('Colisão em mídia preparada')
 return str(dest.relative_to(public_dir()))

def edit_hash(d):
 p=d['project.json']
 return digest({'fps':p['fps'],'clips':[{'mediaId':x['clip']['mediaId'],'inFrame':x['clip']['inFrame'],'duration':x['duration']} for x in p['scenes']]})

def attach_finish(job,kind,path,notes,automatic=False):
 if kind not in ('audio','video'):raise ValueError('Tipo inválido')
 path=persistent_path(path);d=load(job);mid=register(path,kind);finish=d['finishing.json'];finish[kind+'MediaId']=mid
 finish[kind+'EditHash']=edit_hash(d);finish[kind+'Notes']=notes
 if kind=='audio':
  finish['audioGainDb']=0;finish.pop('audioConnector',None)
  if not automatic and finish.get('voiceNeural'):finish['voiceNeural']['enabled']=False
 if kind=='video':finish.pop('videoConnector',None)
 write(jobdir(job)/'finishing.json',finish);log(job,'attach-finishing',kind=kind,mediaId=mid,notes=notes)
 return {'mediaId':mid,'editHash':edit_hash(d),'review':'pending'}

def archive_check(mid):
 m=registry()['media'][mid];archive=m.get('verifiedArchive');valid=False
 if archive:
  p=Path(archive['path']);valid=p.is_file() and sha(p)==m['sha256']
 return {'mediaId':mid,'verifiedCopyAccessible':valid,'archive':archive,'deletionPerformed':False,'note':'Conferência de cópia; não comprova backup independente ou retenção na nuvem. Nenhum comando apaga mídia.'}

def compile_job(d,master=False):
 errors=validate_job(d)
 if errors:raise ValueError('; '.join(errors))
 import face_connector
 face_connector.validate_attached(sys.modules[__name__],d)
 voice_connector.validate_attached(sys.modules[__name__],d,required=master)
 hair_media=hair_connector.validate_attached(sys.modules[__name__],d,master)
 windows=finishing_windows.compiled(sys.modules[__name__],d)
 source=d['project.json'];style=d['style.json'];finish=d['finishing.json']
 base=style['layout'].get('base')
 if base is not None:
  import math
  if not isinstance(base,dict) or set(base)!={'scale','x','y'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in base.values()) or not 1<=base['scale']<=1.5:raise ValueError('Enquadramento da base inválido')
  if abs(base['x'])>source['width']*(base['scale']-1)/2 or abs(base['y'])>source['height']*(base['scale']-1)/2:raise ValueError('Enquadramento expõe bordas da base')
 from render_finishing import compile_finishing
 sounds,grade=compile_finishing(sys.modules[__name__],d['project.json'],finish)
 gain=finish.get('audioGainDb',0)
 if type(gain) not in (int,float) or not -60<=gain<=30:raise ValueError('Ganho de áudio inválido')
 for kind in ('audio','video'):
  if finish.get(kind+'MediaId') and finish.get(kind+'EditHash')!=edit_hash(d):raise ValueError('Mídia tratada pertence a outro corte; refazer ou realinhar '+kind)
 p={k:source[k] for k in ('videoId','width','height','fps')}
 if 'editorialMode' in source:p['editorialMode']=source['editorialMode']
 if style.get('premiereCaptionPosition'):p['premiereCaptionPosition']=copy.deepcopy(style['premiereCaptionPosition'])
 p.update(schemaVersion=1,timingStatus='draft',source=None,shots=[],scenes=[],captions=[],reviews={},layout=copy.deepcopy(style['layout']),audioGainDb=finish.get('audioGainDb',0))
 for label in p['layout']['labels']:
  if label.get('mediaId'):label['src']=stage_file(label.pop('mediaId'))
 guides=style['layout'].get('lookGuides',{})
 if guides and (set(guides)!={'top','bottom'} or any(type(v) not in (int,float) for v in guides.values()) or not .06<=guides['top']<guides['bottom']<=.94):raise ValueError('Guias de altura inválidas')
 p['previewGuides']=None if master else dict(safeInset=.06,**({'lookTop':guides['top'],'lookBottom':guides['bottom']} if guides else {}))
 cursor=0
 for scene in source['scenes']:
  s=copy.deepcopy(scene);clip=s.pop('clip');dur=s['duration'];mid=clip['mediaId'];start=clip['inFrame']
  if windows:mid=windows['mediaId'];start=windows['starts'][s['id']]
  if not windows and not master and clip.get('proxy'):
   try:resolve(clip['proxy']['mediaId']);mid=clip['proxy']['mediaId'];start=clip['proxy']['inFrame']+clip['inFrame']-clip['proxy']['sourceInFrame']
   # A proxy covers only its recorded original interval.
   # Extending outside that interval must reconnect the original.
   
   except ValueError:pass
  path=stage_file(mid);info=vh.probe(public_dir()/path)
  if start<0 or (start+dur)/p['fps']>float(info['format']['duration'])+1/p['fps']:
   if windows:raise ValueError('Janela tratada truncada; não substituir por bruto')
   mid=clip['mediaId'];start=clip['inFrame'];path=stage_file(mid);info=vh.probe(public_dir()/path)
  if (start+dur)/p['fps']>float(info['format']['duration'])+1/p['fps']:raise ValueError('Corte ultrapassa mídia: '+scene['id'])
  p['shots'].append({'src':path,'from':cursor,'inFrame':start,'outFrame':start+dur})
  events={e['id']:e['frame'] for e in s.get('events',[])}
  for layer in s['layers']:
   layer['id']=s['id']+'-'+layer['id'];layer['src']=stage_file(layer.pop('mediaId')) if layer.get('mediaId') else None
   if layer.get('premiereMediaId'):layer['premiereSrc']=stage_file(layer.pop('premiereMediaId'))
   if layer.get('anchor'):
    layer['from']=events[layer['anchor']]+layer.get('offsetFrames',0);layer['duration']=dur-layer['from']
  captions=s.pop('captions',[])
  if style.get('captionPolicy',{}).get('continuous'):captions=caption_rules.continuous(captions,dur,first_frame=1 if cursor==0 else 0)
  for c in captions:p['captions'].append({**c,'from':cursor+c['from']})
  s['from']=cursor;p['scenes'].append(s);cursor+=dur
 p['soundEffects']=sounds;p['colorGrade']=grade
 p['durationInFrames']=cursor
 base_media=hair_media or finish.get('videoMediaId')
 if base_media:
  p['source']=stage_file(base_media);p['shots']=[]
  if abs(float(vh.probe(public_dir()/p['source'])['format']['duration'])-cursor/p['fps'])>1/p['fps']:raise ValueError('Vídeo tratado não alinhado à duração da timeline')
 if finish.get('audioMediaId'):
  p['audioSrc']=stage_file(finish['audioMediaId'])
  if abs(float(vh.probe(public_dir()/p['audioSrc'])['format']['duration'])-cursor/p['fps'])>1/p['fps']:raise ValueError('Áudio tratado não alinhado à duração da timeline')
 return p

def render(job,out,master=False,frames=None,scene=None,cut_only=False,preview_scale=0.5):
 metrics=Metrics();started=time.perf_counter()
 if preview_scale not in (0.5,1):raise ValueError('Escala de prévia inválida')
 if master and preview_scale!=0.5:raise ValueError('Escala de prévia é exclusiva de prévia')
 if master and cut_only:raise ValueError('--cut-only é exclusivo de prévia')
 d=load(job);s=status(job)
 if scene:
  if master or frames:raise ValueError('--scene é exclusivo de prévia e não combina com --frames')
  frames=scene_frames(d,scene)
 if master and any(v!='approved' for v in s['checkpoints'].values()):raise ValueError('Master bloqueado: checkpoints pendentes ou desatualizados')
 if master and frames:raise ValueError('Master deve ser completo')
 if master and tuple(d['project.json'][k] for k in ('width','height','fps'))!=(1440,2560,60):raise ValueError('Preset master deve ser 1440×2560 / 60 fps')
 d=voice_connector.prepare(sys.modules[__name__],job,master);s=status(job)
 p=compile_job(d,master)
 metrics.events.append({'stage':'prepare-compile','seconds':time.perf_counter()-started,'ok':True})
 if cut_only:
  for sc in p['scenes']:sc['layers']=[]
  p['soundEffects']=[]
  p['captions']=[];p['layout']={**p['layout'],'labels':[]}
 validation=vh.validate(p,False,public_root=public_dir())
 if master:
  validation['errors']+=caption_rules.violations(p['captions'],d['style.json'].get('captionPolicy',{}))
 if validation['errors']:raise ValueError('; '.join(validation['errors']))
 if master:
  pending=[x for x in validation['pending'] if not x.startswith(('Revisão documentada','Sincronização'))]
  if pending:raise ValueError('Materiais incompletos: '+'; '.join(pending))
 out=output_path(out) if out else run_dir(job,'candidates' if master else 'reviews')/('master.mov' if master else 'preview.mp4')
 if out.suffix.lower()!=('.mov' if master else '.mp4'):raise ValueError('Use .mov para master ou .mp4 para prévia')
 if any(x.exists() for x in (out,out.with_suffix('.project.json'),out.with_suffix('.report.json'))):raise ValueError('Saída ou registro já existe')
 revision=checkpoint(job,'Render '+out.name);out.parent.mkdir(parents=True,exist_ok=True)
 if master:p['timingStatus']='reviewed';p['reviews']={}
 write(out.with_suffix('.project.json'),p,True)
 with render_workspace(paths()['cache']) as render_public:
  sources={x['src'] for x in p['shots']}|{l['src'] for sc in p['scenes'] for l in sc['layers'] if l.get('src')}|{p[k] for k in ('source','audioSrc') if p.get(k)}
  sources.update(c['src'] for c in p.get('soundEffects',[]))
  sources.update(l['src'] for l in p['layout']['labels'] if l.get('src'))
  for src in sources:
   target=render_public/src
   with metrics.measure('stage-media',source=src) as measurement:measurement.update(stage_copy((public_dir()/src).resolve(),target))
  cmd=['pnpm','exec','remotion','render','src/index.ts','FashionVideo',str(out),'--props',str(out.with_suffix('.project.json')),'--concurrency=2','--public-dir',str(render_public),'--bundle-cache=false']
  cmd+=['--codec=prores','--prores-profile=standard','--pixel-format=yuv422p10le','--color-space=bt709','--image-format=png','--audio-codec=pcm-16','--audio-sample-rate=48000'] if master else ['--codec=h264',f'--scale={preview_scale}','--audio-sample-rate=48000','--color-space=bt709']
  if frames:cmd+=['--frames',frames]
  with metrics.measure('render'):subprocess.run(cmd,cwd=ROOT,check=True)
 with metrics.measure('verify-decode'):
  if master:verification=vh.verify(out,p,True)
  else:
   subprocess.run([vh.binary('ffmpeg'),'-v','error','-xerror','-i',str(out),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
   verification={'technical_pass':True,'metadata':vh.probe(out),'decode_pass':True}
 report={'job':job,'revision':revision,'fingerprints':s['fingerprints'],'master':master,'cutOnly':cut_only,'renderScale':1 if master else preview_scale,'output':str(out),'outputSha256':sha(out),'manifestSha256':sha(out.with_suffix('.project.json')),'frames':frames,'scene':scene,'verification':verification,'released':False,'performance':metrics.report()}
 write(out.with_suffix('.report.json'),report,True);log(job,'render',report=str(out.with_suffix('.report.json')))
 if not verification['technical_pass']:raise ValueError('Arquivo renderizado reprovado; consulte relatório')
 return report

def release(job,out,evidence,reviewer):
 out=Path(out).resolve();report=read(out.with_suffix('.report.json'));e=read(evidence);s=status(job)
 if not report['master'] or report['job']!=job or not report['verification']['technical_pass']:raise ValueError('Master elegível não encontrado')
 if report['fingerprints']!=s['fingerprints'] or any(v!='approved' for v in s['checkpoints'].values()):raise ValueError('Revisões desatualizadas')
 if sha(out)!=report['outputSha256'] or sha(out.with_suffix('.project.json'))!=report['manifestSha256']:raise ValueError('Master ou manifesto mudou depois da verificação')
 if e.get('outputSha256')!=sha(out) or not e.get('userApproval') or not e.get('notes') or not reviewer.strip() or any(e.get('checks',{}).get(k)!='passed' for k in ('visual','audio','completePlayback')):raise ValueError('Revisão final incompleta ou de outro arquivo')
 if not vh.verify(out,read(out.with_suffix('.project.json')),True)['technical_pass']:raise ValueError('Verificação final reprovada')
 result={'at':now(),'reviewer':reviewer,'outputSha256':sha(out),'reportSha256':sha(out.with_suffix('.report.json')),'evidenceSha256':sha(evidence),'evidence':str(Path(evidence).resolve()),'revision':report['revision']}
 destination=paths()['ready']/safe_id(job)/(report['revision']+'-'+report['outputSha256'][:12])/out.name
 destination.parent.mkdir(parents=True,exist_ok=True)
 if destination.exists():
  if sha(destination)!=report['outputSha256']:raise ValueError('Colisão em Prontos')
 else:
  temp=destination.with_name('.'+destination.name+'.'+uuid.uuid4().hex+'.tmp')
  shutil.copy2(out,temp)
  if sha(temp)!=report['outputSha256']:raise ValueError('Cópia final divergente')
  os.link(temp,destination);temp.unlink()
 result.update(output=str(out),publishedOutput=str(destination))
 write(jobdir(job)/'releases'/(sha(out)+'.json'),result,True);log(job,'release',**result);return result

def overview(job):
 s=status(job);d=load(job);p=d['project.json'];lines=[f'# Vídeo {job}', '', 'Resumo gerado. Dados editáveis nos JSONs desta pasta.', '', f"Próximo checkpoint: **{s['next']}**", '', '| Etapa | Estado |', '|---|---|']
 lines += [f'| {stage} | {state} |' for stage,state in s['checkpoints'].items()]
 lines += ['', f"Cabelo: **{s['hair']['state']}**. Configuração independente em finishing.json → hair."]
 if s['hair'].get('reason'):lines += [s['hair']['reason']]
 if s.get('windows'):lines += ['', 'Janelas visuais 4K associadas: '+s['windows']['work']]
 lines += ['', f"Cenas: {len(p['scenes'])}. Duração: {sum(x['duration'] for x in p['scenes'])/p['fps']:.2f} s.", '', '## Mídias', '']
 lines += [f"- {registry()['media'][m['id']]['filename']}: {m['state']}" for m in s['media']]
 lines += ['', '## Revisão por look', '']
 lines += [f"- {key}: {v['state']}" for key,v in s['looks'].items()]
 lines += ['', '## Histórico recente', '']
 for f in sorted((jobdir(job)/'history').glob('*.json'))[-10:]:
  event=read(f);lines.append(f"- {event['at']}: {event['action']} — {event.get('note',event.get('revision',''))}")
 (jobdir(job)/'STATUS.md').write_text('\n'.join(lines)+'\n');return s

def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
 sub.add_parser('paths')
 for c in ('resume','premiere-handoff','premiere-candidate','premiere-release','review-scenes'):
  a=sub.add_parser(c);a.add_argument('job')
  if c in ('premiere-handoff','premiere-candidate'):
   a.add_argument('--project',required=True);a.add_argument('--sequence',required=True)
  if c=='premiere-handoff':a.add_argument('--package',required=True)
  if c=='premiere-candidate':a.add_argument('--master',required=True);a.add_argument('--dependencies',required=True)
  if c=='premiere-release':a.add_argument('--candidate',required=True)
  if c in ('premiere-handoff','premiere-candidate','premiere-release'):a.add_argument('--evidence',required=True)
  if c=='review-scenes':a.add_argument('--plan',required=True);a.add_argument('--out',required=True)
 for c in ('window-init','window-publish'):
  a=sub.add_parser(c);a.add_argument('job');a.add_argument('--work',required=True)
  if c=='window-init':a.add_argument('--plan',required=True)
 a=sub.add_parser('init');a.add_argument('job');a.add_argument('--brief',required=True);a.add_argument('--mode',choices=['fashion','no-looks'],default='fashion')
 a=sub.add_parser('voice-process');a.add_argument('job');a.add_argument('--enable',action='store_true')
 a=sub.add_parser('review-look');a.add_argument('job');a.add_argument('look');a.add_argument('--evidence',required=True);a.add_argument('--reviewer',required=True);a.add_argument('--decision',choices=['approved','rejected'],default='approved')
 a=sub.add_parser('register');a.add_argument('path');a.add_argument('--kind',choices=['original','proxy','still','font','sfx','audio','video'],required=True);a.add_argument('--archive')
 a=sub.add_parser('archive-check');a.add_argument('media_id')
 a=sub.add_parser('attach-finish');a.add_argument('job');a.add_argument('kind',choices=['audio','video']);a.add_argument('path');a.add_argument('--notes',required=True);a.add_argument('--face-run');a.add_argument('--temporal-review');a.add_argument('--window-work')
 for c in ('face-base','face-prepare','face-render'):
  a=sub.add_parser(c);a.add_argument('job');a.add_argument('--work',required=c!='face-base');a.add_argument('--window-work')
  if c=='face-base':a.add_argument('--engine-root',default='/Users/lucas/Documents/Codex/rosto-natural')
  if c=='face-prepare':a.add_argument('--review',required=True)
  if c=='face-render':a.add_argument('--compare-cpu',action='store_true')
 for c in ('hair-setup','hair-prepare','hair-config','hair-render','hair-attach','hair-disable','hair-status'):
  a=sub.add_parser(c);a.add_argument('job');a.add_argument('--window-work')
  if c in ('hair-setup','hair-prepare'):a.add_argument('--python',default=str(hair_connector.DEFAULT_PYTHON))
  if c=='hair-setup':a.add_argument('--cache',required=True);a.add_argument('--config')
  if c=='hair-prepare':a.add_argument('--plan',required=True)
  if c in ('hair-prepare','hair-render','hair-attach'):a.add_argument('--work',required=c=='hair-attach')
  if c=='hair-config':
   group=a.add_mutually_exclusive_group(required=True);group.add_argument('--config');group.add_argument('--out')
  if c=='hair-render':
   a.add_argument('--scene');a.add_argument('--frames');a.add_argument('--save-masks',action='store_true');a.add_argument('--quality',choices=['preview','production'],default='preview')
 a=sub.add_parser('relink');a.add_argument('media_id');a.add_argument('path');a.add_argument('--verify-archive',action='store_true')
 for c in ('status','overview','checkpoint','compile','approve','render','release','gate'):
  a=sub.add_parser(c);a.add_argument('job')
  if c=='checkpoint':a.add_argument('--note',required=True)
  if c in ('compile','render'):a.add_argument('--master',action='store_true');a.add_argument('--out')
  if c=='render':a.add_argument('--frames');a.add_argument('--scene');a.add_argument('--cut-only',action='store_true');a.add_argument('--preview-scale',type=float,choices=[0.5,1],default=0.5)
  if c=='approve':a.add_argument('stage',choices=STAGES);a.add_argument('--decision',choices=['approved','rejected'],default='approved')
  if c in ('approve','release'):a.add_argument('--evidence',required=True);a.add_argument('--reviewer',required=True)
  if c=='release':a.add_argument('--out',required=True)
 a=sub.add_parser('fork');a.add_argument('job');a.add_argument('revision');a.add_argument('new')
 a=sub.add_parser('assemble');a.add_argument('new');a.add_argument('scenes',nargs='+')
 args=ap.parse_args()
 if args.cmd=='init':result=init_job(args.job,args.brief,args.mode)
 elif args.cmd=='voice-process':
  if args.enable:voice_connector.enable(sys.modules[__name__],args.job)
  result=voice_connector.process(sys.modules[__name__],args.job)
 elif args.cmd=='window-init':result=finishing_windows.initialize(sys.modules[__name__],args.job,args.plan,args.work)
 elif args.cmd=='window-publish':result=finishing_windows.publish(sys.modules[__name__],args.job,args.work)
 elif args.cmd=='paths':result={k:str(v) for k,v in paths().items()}
 elif args.cmd=='register':result=register(args.path,args.kind,args.archive)
 elif args.cmd=='archive-check':result=archive_check(args.media_id)
 elif args.cmd.startswith('hair-'):
  host=finishing_windows.Host(sys.modules[__name__],args.job,args.window_work) if args.window_work else sys.modules[__name__]
  if args.cmd=='hair-setup':result=hair_connector.setup(host,args.job,args.cache,args.config,args.python)
  elif args.cmd=='hair-prepare':result=hair_connector.prepare(host,args.job,args.plan,args.work or run_dir(args.job,'hair'),args.python)
  elif args.cmd=='hair-config':result=hair_connector.configure(host,args.job,args.config,args.out)
  elif args.cmd=='hair-render':result=hair_connector.render(host,args.job,args.work or run_dir(args.job,'hair'),args.scene,args.frames,args.save_masks,args.quality)
  elif args.cmd=='hair-attach':result=hair_connector.attach(host,args.job,args.work)
  elif args.cmd=='hair-disable':result=hair_connector.disable(host,args.job)
  else:result=hair_connector.summary(host,host.load(args.job))
 elif args.cmd.startswith('face-'):
  import face_connector as face
  host=finishing_windows.Host(sys.modules[__name__],args.job,args.window_work) if args.window_work else sys.modules[__name__]
  if args.cmd=='face-base':result=face.base(host,args.job,args.work or run_dir(args.job,'face'),args.engine_root)
  elif args.cmd=='face-prepare':result=face.prepare(host,args.job,args.work,args.review)
  else:result=face.render(host,args.job,args.work,args.compare_cpu)
 elif args.cmd=='attach-finish':
  if args.window_work and not (args.face_run and args.temporal_review):raise ValueError('Janelas exigem procedência facial e revisão temporal')
  if args.face_run or args.temporal_review:
   if args.kind!='video' or not args.face_run or not args.temporal_review:raise ValueError('Use video, --face-run e --temporal-review juntos')
   import face_connector as face
   host=finishing_windows.Host(sys.modules[__name__],args.job,args.window_work) if args.window_work else sys.modules[__name__]
   result=face.attach(host,args.job,args.path,args.notes,args.face_run,args.temporal_review)
  else:result=attach_finish(args.job,args.kind,args.path,args.notes)
 elif args.cmd=='relink':result=relink(args.media_id,args.path,args.verify_archive)
 elif args.cmd in ('resume','premiere-handoff','premiere-candidate','premiere-release'):
  import editor_state as es
  if args.cmd=='resume':result=es.resume(args.job)
  elif args.cmd=='premiere-handoff':result=es.record_handoff(args.job,args.project,args.sequence,args.package,args.evidence)
  elif args.cmd=='premiere-candidate':result=es.register_candidate(args.job,args.master,args.project,args.sequence,args.dependencies,args.evidence)
  else:result=es.release_candidate(args.job,args.candidate,args.evidence)
 elif args.cmd=='review-scenes':
  import scene_review
  result=scene_review.build(args.plan,persistent_path(args.out))
 elif args.cmd=='status':result=status(args.job)
 elif args.cmd=='overview':result=overview(args.job)
 elif args.cmd=='gate':
  import editor_state as es
  if es.resume(args.job)['authority']=='premiere':result=es.final_gate(args.job)
  else:
   result=status(args.job)
   if any(v!='approved' for v in result['checkpoints'].values()):print(json.dumps(result,ensure_ascii=False,indent=2));raise ValueError('Master bloqueado pelos checkpoints')
   p=compile_job(load(args.job),True);v=vh.validate(p,False,public_root=public_dir())
   if v['errors']:raise ValueError('; '.join(v['errors']))
   pending=[x for x in v['pending'] if not x.startswith(('Revisão documentada','Sincronização'))]
   if pending:raise ValueError('Materiais incompletos: '+'; '.join(pending))
   issues=caption_rules.violations(p['captions'],load(args.job)['style.json'].get('captionPolicy',{}))
   if issues:raise ValueError('; '.join(issues))
 elif args.cmd=='checkpoint':result=checkpoint(args.job,args.note)
 elif args.cmd=='approve':result=approve(args.job,args.stage,args.evidence,args.reviewer,args.decision)
 elif args.cmd=='fork':result=fork(args.job,args.revision,args.new)
 elif args.cmd=='assemble':result=assemble(args.new,args.scenes)
 elif args.cmd=='compile':result=compile_job(voice_connector.prepare(sys.modules[__name__],args.job,args.master),args.master);write(output_path(args.out) if args.out else paths()['cache']/args.job/('compiled-'+uuid.uuid4().hex+'.json'),result,True)
 elif args.cmd=='render':result=render(args.job,args.out,args.master,args.frames,args.scene,args.cut_only,args.preview_scale)
 elif args.cmd=='review-look':result=review_look(args.job,args.look,args.evidence,args.reviewer,args.decision)
 elif args.cmd=='release':result=release(args.job,args.out,args.evidence,args.reviewer)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError,TypeError,StopIteration,subprocess.CalledProcessError) as e:print('Erro: '+str(e),file=sys.stderr);sys.exit(2)
