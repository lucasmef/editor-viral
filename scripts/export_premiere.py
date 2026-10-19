"""FCP7 XML handoff from a frozen compiled job; never mutates the job.
Static native masks are rasterized by the existing renderer, full-canvas RGBA.
"""
import argparse, copy, json, math, shutil, subprocess, xml.etree.ElementTree as E
from pathlib import Path
import studio as s

def run(args,log):
 with open(log,'w') as f: subprocess.run(list(map(str,args)),cwd=s.ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
def node(p,k,v=None,**attrs):
 n=E.SubElement(p,k,attrs)
 if v is not None:n.text=str(v)
 return n
def rate(p,fps):
 r=node(p,'rate');node(r,'timebase',fps);node(r,'ntsc','FALSE')
def legacy_main():
 ap=argparse.ArgumentParser();ap.add_argument('job');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--resume',action='store_true');a=ap.parse_args()
 out=s.persistent_path(a.out)
 if out.exists() and not a.resume:raise ValueError('Use a new output directory')
 out.mkdir(parents=True,exist_ok=True);media=out/'media';media.mkdir(exist_ok=True)
 snapshot=out/'snapshot.json'
 if snapshot.exists():p=s.read(snapshot)
 else:
  d=s.load(a.job);p=s.compile_job(d,False);s.write(snapshot,p,True);s.write(out/'source-job.json',d,True)
 if '"$expr"' in json.dumps(p):raise ValueError('Animated native expressions require animated interchange assets')
 if p['layout']['caption'].get('highlight')!='glow':raise ValueError('Only static glow captions are supported')
 items=[];clips=[];fps=p['fps'];dur=p['durationInFrames'];w=p['width'];h=p['height']
 def add(item,start,length,track,name):
  idx=len(items);items.append(item);clips.append(dict(index=idx,start=start,duration=length,track=track,name=name))
 maxlayers=max(len(sc['layers']) for sc in p['scenes'])
 for sc in p['scenes']:
  for j,l in enumerate(sc['layers']):
   if l.get('transition')=='fade' and l.get('fadeFrames',0):raise ValueError('Animated fades require alpha video')
   add(dict(kind='piece',layer=l),sc['from']+l['from'],l['duration'],j+1,l['id'])
 for j,label in enumerate(p['layout']['labels']):
  l=dict(id=label['text'],src=label['src'],label=label['text'],duration=1,transition='cut',fadeFrames=0,rect=dict(x=label['x']-label['width']/2,y=label['y'],width=label['width'],height=label['height']),crop=label.get('crop'))
  for sc in p['scenes']:
   start=min(x['from'] for x in sc['layers']) if p['layout'].get('revealOverlaysWithLooks') else 0
   add(dict(kind='piece',layer=l),sc['from']+start,sc['duration']-start,maxlayers+1+j,label['text'])
 for c in p['captions']:add(dict(kind='caption',word=c),c['from'],c['duration'],maxlayers+3,'Legenda — '+c['text'])
 add(dict(kind='guides'),0,dur,maxlayers+4,'GUIAS — DESLIGAR ANTES DA ENTREGA')
 props=out/'pieces.props.json';s.write(props,dict(project=p,items=items));s.write(out/'layers.json',clips)
 public=s.paths()['cache']/'premiere-export'/out.name/'public';public.mkdir(parents=True,exist_ok=True)
 sources={i['layer']['src'] for i in items if i['kind']=='piece'}
 for src in sources:
  dest=public/src;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copy2(s.public_dir()/src,dest)
 pngdir=media/'layers'
 if not (out/'pieces.complete').exists():
  run(['pnpm','exec','remotion','render','src/premiere.tsx','PremierePieces',pngdir,'--props',props,'--sequence','--image-format=png','--concurrency=2','--public-dir',public,'--bundle-cache=false'],out/'pieces.log')
  (out/'pieces.complete').write_text('ok')
 pngs=sorted(pngdir.glob('*.png'))
 if len(pngs)!=len(items):raise ValueError(f'PNG count {len(pngs)} != {len(items)}')
 # A 33^3 LUT implements the CSS filter order, including per-operation clipping.
 import numpy as np
 lut=out/'grade.cube';g=p.get('colorGrade') or {};sat=g.get('saturation',1);t=g.get('warmth',0)
 sm=np.array([[.213+.787*sat,.715-.715*sat,.072-.072*sat],[.213-.213*sat,.715+.285*sat,.072-.072*sat],[.213-.213*sat,.715-.715*sat,.072+.928*sat]])
 sep=(1-t)*np.eye(3)+t*np.array([[.393,.769,.189],[.349,.686,.168],[.272,.534,.131]])
 with lut.open('w') as f:
  f.write('TITLE "Studio CSS grade approximation"\nLUT_3D_SIZE 33\n')
  for b in range(33):
   for gg in range(33):
    for r in range(33):
     v=np.clip(np.array([r,gg,b])/32*g.get('brightness',1),0,1);v=np.clip((v-.5)*g.get('contrast',1)+.5,0,1);v=np.clip(sm@v,0,1);v=np.clip(sep@v,0,1)
     f.write(' '.join(f'{x:.8f}' for x in v)+'\n')
 # Preserve a reference to the untouched 4K treated source; grade/framing is baked
 # in a separate 4K interchange derivative, with all original source handles.
 shotpaths={x['src'] for x in p['shots']}
 if len(shotpaths)!=1:raise ValueError('This version requires a single conformed visual source')
 src=next(iter(shotpaths));original=s.resolve(Path(src).stem);s.write(out/'original-media.json',{'video':str(original),'sha256':s.sha(original)})
 basefile=media/'base-4k-cor-enquadramento.mov';base=p['layout']['base'];sw,sh=2160,3840
 if not basefile.exists():
  scale=base['scale'];nw=round(sw*scale/2)*2;nh=round(sh*scale/2)*2;cx=(nw-sw)/2-base['x']*sw/w;cy=(nh-sh)/2-base['y']*sh/h
  # Filter filename is local, no shell interpretation. LUT interpolates CSS, not Lumetri.
  filt=f"lut3d=file='{lut}':interp=tetrahedral,scale={nw}:{nh},crop={sw}:{sh}:{cx}:{cy},setsar=1"
  run([s.ROOT/'.local-bin/ffmpeg','-nostdin','-i',original,'-map','0:v:0','-an','-vf',filt,'-c:v','prores_ks','-profile:v','2','-pix_fmt','yuv422p10le','-threads','4','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',basefile],out/'base.log')
 # Audio is copied separately, never mixed into the footage.
 def audiofile(src):
  dest=media/Path(src).name
  if not dest.exists():shutil.copy2(s.public_dir()/src,dest)
  return dest
 voice=audiofile(p['audioSrc']);clickfiles={c['src']:audiofile(c['src']) for c in p.get('soundEffects',[])}
 root=E.Element('xmeml',version='5');seq=node(root,'sequence',id='sequence-'+s.safe_id(a.job));node(seq,'name',f'{a.job} — EDITAVEL — guias ligadas');node(seq,'duration',dur);rate(seq,fps)
 tc=node(seq,'timecode');rate(tc,fps);node(tc,'string','00:00:00:00');node(tc,'frame',0);node(tc,'displayformat','NDF')
 m=node(seq,'media');v=node(m,'video');fmt=node(node(v,'format'),'samplecharacteristics');rate(fmt,fps);node(fmt,'width',w);node(fmt,'height',h);node(fmt,'anamorphic','FALSE');node(fmt,'pixelaspectratio','square');node(fmt,'fielddominance','none')
 tracks=[node(v,'track') for _ in range(maxlayers+5)];aud=node(m,'audio');node(aud,'numOutputChannels',2);ats=[node(aud,'track',premiereTrackType='Stereo') for _ in range(2)]
 counter=0
 metadata={}
 def clip(track,path,name,start,length,sourcein=0,audio=False,scale=None):
  nonlocal counter
  counter+=1
  if path.suffix!='.png' and str(path) not in metadata:metadata[str(path)]=s.vh.probe(path)
  info=metadata.get(str(path))
  source_duration=math.ceil(float(info['format']['duration'])*fps) if info else dur
  c=node(track,'clipitem',id=f'clip-{counter}');node(c,'name',name);node(c,'enabled','TRUE');node(c,'duration',max(dur,sourcein+length));rate(c,fps);node(c,'start',start);node(c,'end',start+length);node(c,'in',sourcein);node(c,'out',sourcein+length)
  f=node(c,'file',id=f'file-{counter}');node(f,'name',path.name);node(f,'pathurl',path.as_uri());rate(f,fps);node(f,'duration',source_duration);fm=node(f,'media')
  if audio:
   c.set('premiereChannelType','stereo')
   am=node(fm,'audio');node(am,'channelcount',2);ac=node(am,'samplecharacteristics');node(ac,'depth',24 if info['streams'][0]['codec_name']=='pcm_s24le' else 16);node(ac,'samplerate',info['streams'][0]['sample_rate']);st=node(c,'sourcetrack');node(st,'mediatype','audio');node(st,'trackindex',1)
  else:
   vm=node(fm,'video');sc=node(vm,'samplecharacteristics');rate(sc,fps);node(sc,'width',sw if scale else w);node(sc,'height',sh if scale else h);node(sc,'anamorphic','FALSE');node(sc,'pixelaspectratio','square');node(sc,'fielddominance','none');node(c,'alphatype','straight')
   if path.suffix=='.png':node(f,'stillframe','TRUE')
   if scale:
    ef=node(node(c,'filter'),'effect');node(ef,'name','Basic Motion');node(ef,'effectid','basic');node(ef,'effectcategory','motion');node(ef,'effecttype','motion');node(ef,'mediatype','video');pa=node(ef,'parameter');node(pa,'parameterid','scale');node(pa,'name','Scale');node(pa,'value',scale)
  return c
 for shott in p['shots']:clip(tracks[0],basefile,'Raquel 4K — '+str(shott['from']),shott['from'],shott['outFrame']-shott['inFrame'],shott['inFrame'],scale=100*w/sw)
 for c in clips:clip(tracks[c['track']],pngs[c['index']],c['name'],c['start'],c['duration'])
 clip(ats[0],voice,'Voz tratada',0,dur,audio=True)
 for c in p.get('soundEffects',[]):
  if c['gainDb']!=0:raise ValueError('Nonzero SFX gain not yet supported')
  clip(ats[1],clickfiles[c['src']],'Clique',c['from'],c['duration'],audio=True)
 if p.get('audioGainDb',0)!=0:raise ValueError('Nonzero voice gain not supported')
 for tr in tracks+ats:node(tr,'enabled','TRUE');node(tr,'locked','FALSE')
 E.indent(root);xml=out/f'{a.job}-premiere.xml';E.ElementTree(root).write(xml,encoding='utf-8',xml_declaration=True)
 def ts(frame):
  ms=round(frame/fps*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (out/'legendas-editaveis.srt').write_text('\n\n'.join(f"{j+1}\n{ts(c['from'])} --> {ts(c['from']+c['duration'])}\n{c['text']}" for j,c in enumerate(p['captions']))+'\n')
 report={'snapshotSha256':s.sha(snapshot),'xmlSha256':s.sha(xml),'videoTracks':len(tracks),'audioTracks':2,'pieces':sum(len(sc['layers']) for sc in p['scenes']),'durationFrames':dur,'fps':fps,'xmlPathsExist':all(Path(__import__('urllib.parse',fromlist=['unquote']).unquote(n.text.removeprefix('file://'))).exists() for n in root.iter('pathurl')),'premiereImportVerified':False,'approved':False}
 s.write(out/'report.json',report);print(json.dumps(report,indent=2),flush=True)
def main():
 import sys
 if '--legacy' in sys.argv:
  sys.argv.remove('--legacy');return legacy_main()
 ap=argparse.ArgumentParser(description='Native Premiere package; no live project mutation')
 ap.add_argument('job');ap.add_argument('--snapshot',required=True,type=Path);ap.add_argument('--av-sources',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
 ap.add_argument('--caption-template',type=Path,default=s.ROOT/'studio/templates/premiere/palavra-101-v1.mogrt')
 ap.add_argument('--caption-approval',type=Path,default=s.ROOT/'studio/templates/premiere/palavra-101-v1.approval.json')
 ap.add_argument('--lut',type=Path)
 a=ap.parse_args()
 import premiere_package
 result=premiere_package.build(a.job,s.read(a.snapshot),s.read(a.av_sources),s.persistent_path(a.out),a.caption_template,a.caption_approval,lambda src:s.resolve(Path(src).stem),a.lut,s.paths()['cache'])
 print(json.dumps({'package':str(a.out/'package.json'),'clips':len(result['clips']),'captions':len(result['captions']),'importVerified':False},indent=2))
if __name__=='__main__':main()
