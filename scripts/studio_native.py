"""Canonical persistence for native Studio look properties."""
import copy,json,subprocess,time
from pathlib import Path
import studio as st

def parse(path):
 r=subprocess.run(['node',str(st.ROOT/'scripts/studio_native.cjs'),str(path)],capture_output=True,text=True)
 if r.returncode:raise ValueError(r.stderr.strip())
 return json.loads(r.stdout)

def expression(v):
 if isinstance(v,dict) and '$expr' in v:
  t=v['$expr']
  if t=='frame':return 'useCurrentFrame()'
  if t=='fps':return 'useVideoConfig().fps'
  if t=='undefined':return 'undefined'
  if t=='function':return v['fn']
  if t=='call':return v['fn']+'('+','.join(map(expression,v['args']))+')'
  if t=='unary':return '('+v['op']+expression(v['arg'])+')'
  if t=='binary':return '('+expression(v['a'])+v['op']+expression(v['b'])+')'
  if t=='conditional':return '('+expression(v['test'])+'?'+expression(v['yes'])+':'+expression(v['no'])+')'
  if t=='template':return '('+'+'.join(expression(x) for pair in zip(v['parts'],v['values']+[None]) for x in (pair if pair[1] is not None else pair[:1]))+')'
  raise ValueError('Expressão desconhecida')
 if isinstance(v,list):return '['+','.join(map(expression,v))+']'
 if isinstance(v,dict):return '{'+','.join(json.dumps(k)+':'+expression(x) for k,x in v.items())+'}'
 return json.dumps(v,ensure_ascii=False)

def apply(d,compiled,initial,edits):
 out=copy.deepcopy(d);origins={};known={e['id']:e for e in initial['layers']}
 # Original compiled snapshot is stable for the lifetime of the session.
 for scene in compiled['scenes']:
  current=next(s for s in out['project.json']['scenes'] if s['id']==scene['id'])
  source=next(s for s in compiled.get('_nativeOriginal',d['project.json'])['scenes'] if s['id']==scene['id'])
  for l in scene['layers']:
   local=l['id'][len(scene['id'])+1:]
   original=next((x for x in source['layers'] if x['id']==local),None)
   if original is None:
    # Deletion followed by undo: reconstruct from the session source.
    original=copy.deepcopy(l);original['id']=local;original.pop('src',None)
    original['mediaId']=compiled['_nativeMedia'][l['id']]
   origins[l['id']]=(scene,current,original,l)
 for s in out['project.json']['scenes']:s['layers']=[]
 counts={};mapping={}
 for e in edits['layers']:
  if e['id'] not in origins or e['assetSignature']!=known[e['id']]['assetSignature']:raise ValueError('Fonte da peça mudou; reabra para trocar mídia')
  scene,target,original,view=origins[e['id']];props=copy.deepcopy(e['props'])
  start=props.pop('from',0);duration=props.pop('durationInFrames',scene['duration'])
  if type(start) is not int or type(duration) is not int or duration<=0 or start<scene['from'] or start+duration>scene['from']+scene['duration']:raise ValueError('Entrada/saída deve permanecer dentro da cena: '+e['id'])
  # Native crop is separate from the immutable pixel extraction crop.
  for k in ('cropTop','cropBottom','cropLeft','cropRight'):
   v=props.get(k,0)
   if isinstance(v,(int,float)) and not 0<=v<=1:raise ValueError('Crop fora de 0–100%')
  layer=copy.deepcopy(original);counts[e['id']]=counts.get(e['id'],0)+1
  if counts[e['id']]>1:layer['id']+='-copy-'+str(counts[e['id']])
  layer['rect']=copy.deepcopy(view['rect'])
  layer['from']=start-scene['from'];layer['duration']=duration
  layer.pop('anchor',None);layer.pop('offsetFrames',None)
  layer['native']={'props':props}
  target['layers'].append(layer);mapping.setdefault((scene['id'],original['id']),[]).append(layer['id'])
 for s in out['project.json']['scenes']:
  s['looks']=copy.deepcopy(next(x for x in compiled.get('_nativeOriginal',d['project.json'])['scenes'] if x['id']==s['id']).get('looks',[]))
  for look in s.get('looks',[]):look['layerIds']=[new for old in look['layerIds'] for new in mapping.get((s['id'],old),[])];
  s['looks']=[x for x in s.get('looks',[]) if x['layerIds']]
 return out

def save(job,baseline,compiled,initial,edits):
 current=st.load(job)
 if st.digest(current)!=st.digest(baseline):raise ValueError('Projeto mudou fora desta sessão. Reabrir antes de continuar')
 updated=apply(current,compiled,initial,edits)
 if updated!=current:
  st.write(st.jobdir(job)/'history'/(str(time.time_ns())+'-studio-native.json'),{'at':st.now(),'action':'studio-native','beforeProject':current['project.json'],'afterProject':updated['project.json']},True)
  st.write(st.jobdir(job)/'project.json',updated['project.json'])
 return updated
