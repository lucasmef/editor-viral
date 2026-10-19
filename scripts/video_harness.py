"""Local video pipeline. Automatic checks do not certify editorial quality."""
import argparse, hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def binary(name):
    override = os.environ.get(name.upper())
    if override: return override
    if name == 'ffmpeg' and (ROOT/'.local-bin/ffmpeg').exists(): return str(ROOT/'.local-bin/ffmpeg')
    found = shutil.which(name)
    if found: return found
    candidates = list((ROOT/'node_modules/.pnpm').glob(f'@remotion+compositor-*/node_modules/@remotion/compositor-*/{name}'))
    if candidates: return str(candidates[0])
    raise ValueError(f'{name} não encontrado. Configure {name.upper()}.')

def probe(path):
    exe = binary('ffprobe')
    env = dict(os.environ)
    if (Path(exe).parent/'libavdevice.dylib').exists():
        env['DYLD_LIBRARY_PATH'] = str(Path(exe).parent)
    result = subprocess.run([exe, '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_frames,color_space,color_transfer,color_primaries,sample_rate,channels,time_base,duration_ts,bits_per_sample', '-of', 'json', str(path)], capture_output=True, text=True, check=True, env=env)
    return json.loads(result.stdout)

def public_file(value, public_root=None):
    if not isinstance(value,str) or not value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('Mídia deve ter caminho relativo dentro de public/.')
    return (Path(public_root) if public_root else ROOT/'public')/value

def validate(p, final=False, media=True, public_root=None):
    errors, pending = [], []
    def require(ok, msg):
        if not ok: errors.append(msg)
    def integer(x): return type(x) is int
    def interval(start,duration,limit): return integer(start) and integer(duration) and start>=0 and duration>0 and start+duration<=limit
    require(p.get('schemaVersion')==1,'schemaVersion deve ser 1')
    for key in ('width','height','fps','durationInFrames'):
        require(integer(p.get(key)) and p[key]>0,f'{key} deve ser inteiro positivo')
    if errors: return {'errors':errors,'pending':pending,'ready':False}
    total=p['durationInFrames'];fps=p['fps']
    if final: require((p['width'],p['height'],fps)==(1440,2560,60),'Master deste projeto deve ser 1440×2560 a 60 fps')
    require(p.get('timingStatus') in ('draft','reviewed'),'timingStatus inválido')
    layout=p.get('layout',{})
    require(isinstance(layout.get('labels'),list),'Rótulos do layout ausentes')
    caption_box=layout.get('caption',{})
    require(all(isinstance(caption_box.get(k),(int,float)) and math.isfinite(caption_box[k]) for k in ('x','y','width','fontSize')),'Área da legenda inválida')
    for label in layout.get('labels',[]):
        require(isinstance(label.get('text'),str) and all(isinstance(label.get(k),(int,float)) and math.isfinite(label[k]) for k in ('x','y')),'Rótulo inválido')
    if p.get('timingStatus')!='reviewed': pending.append('Sincronização ainda provisória')
    mode=p.get('editorialMode','fashion')
    require(mode in ('fashion','no-looks'),'Modo editorial inválido')
    stages=['cuts','timing','stills','captions','visual','audio']
    if mode=='no-looks' and not any(s.get('layers') for s in p.get('scenes',[])):stages.remove('stills')
    for stage in stages:
        review=p.get('reviews',{}).get(stage,{})
        evidence=review.get('evidence')
        if review.get('status')!='passed' or not evidence or not (ROOT/evidence).is_file(): pending.append(f'Revisão documentada pendente: {stage}')
    def exists(src):
        try:
            path=public_file(src, public_root)
            if not path.is_file(): errors.append(f'Mídia não encontrada: {src}'); return None
            return path
        except ValueError as e: errors.append(str(e)); return None
    shots=p.get('shots',[]);cursor=0
    if shots:
        for s in shots:
            valid=all(integer(s.get(k)) for k in ('from','inFrame','outFrame'))
            require(valid,'Corte com quadros inválidos')
            if not valid: continue
            require(s['from']==cursor,'Cortes devem cobrir a timeline sem lacunas/sobreposição')
            require(0<=s['inFrame']<s['outFrame'],'Corte com limites inválidos')
            cursor=s['from']+s['outFrame']-s['inFrame']
            path=exists(s.get('src'))
            if path and media:
                info=probe(path); duration=float(info['format']['duration'])
                require(s['outFrame']/fps<=duration+1/fps,'Corte ultrapassa a duração da fonte')
        require(cursor==total,'Cortes não cobrem a duração do projeto')
    elif p.get('source'):
        path=exists(p['source'])
        if path and media: require(float(probe(path)['format']['duration'])+1/fps>=total/fps,'Fonte menor que a timeline')
    else: pending.append('Nenhuma gravação/corte ligado à timeline')
    ids=set();cursor=0
    for scene in p.get('scenes',[]):
        require(interval(scene.get('from'),scene.get('duration'),total),'Cena fora da timeline')
        require(scene.get('from')==cursor,'Cenas devem ser contíguas, sem sobreposição')
        cursor=scene.get('from',0)+scene.get('duration',0)
        if not scene.get('layers') and mode!='no-looks': pending.append(f"Cena sem stills: {scene.get('id')}")
        for layer in scene.get('layers',[]):
            lid=layer.get('id');require(bool(lid) and lid not in ids,'IDs de camadas devem ser únicos');ids.add(lid)
            require(interval(layer.get('from'),layer.get('duration'),scene['duration']),f'Camada fora da cena: {lid}')
            rect=layer.get('rect',{})
            valid=all(isinstance(rect.get(k),(int,float)) and math.isfinite(rect[k]) for k in ('x','y','width','height'))
            require(valid,f'Retângulo inválido: {lid}')
            if valid: require(rect['x']>=0 and rect['y']>=0 and rect['width']>0 and rect['height']>0 and rect['x']+rect['width']<=p['width'] and rect['y']+rect['height']<=p['height'],f'Camada cortada pela tela: {lid}')
            require(layer.get('transition') in ('cut','fade'),f'Transição desconhecida: {lid}')
            if layer.get('transition')=='fade':require(integer(layer.get('fadeFrames')) and 0<layer['fadeFrames']<=layer['duration'],f'Fade inválido: {lid}')
            src=layer.get('src')
            crop=layer.get('crop')
            if crop is not None:
                valid_crop=all(isinstance(crop.get(k),(int,float)) and math.isfinite(crop[k]) for k in ('x','y','width','height','imageWidth','imageHeight'))
                require(valid_crop,f'Janela do atlas inválida: {lid}')
                if valid_crop: require(crop['x']>=0 and crop['y']>=0 and crop['width']>0 and crop['height']>0 and crop['x']+crop['width']<=crop['imageWidth'] and crop['y']+crop['height']<=crop['imageHeight'],f'Janela ultrapassa o atlas: {lid}')
            if not src: pending.append(f'Still pendente: {lid}');continue
            path=exists(src)
            if path and media:
                from PIL import Image
                try:
                    with Image.open(path) as im:
                        require(im.format=='PNG',f'Still deve ser PNG: {src}')
                        if crop is not None: require(im.size==(crop.get('imageWidth'),crop.get('imageHeight')),f'Dimensões do atlas divergentes: {src}')
                        extrema=im.convert('RGBA').getchannel('A').getextrema()
                        require(extrema[0]<255 and extrema[1]>0,f'Still sem transparência útil: {src}')
                except OSError: errors.append(f'Imagem inválida: {src}')
    require(cursor==total,'Cenas não cobrem a duração do projeto')
    captions=p.get('captions',[]);end=0
    if not captions: pending.append('Legendas ainda não sincronizadas')
    for c in captions:
        require(interval(c.get('from'),c.get('duration'),total),'Legenda fora da timeline')
        require(c.get('from',-1)>=end,'Legendas fora de ordem ou sobrepostas')
        require(isinstance(c.get('text'),str) and bool(c['text'].strip()),'Legenda vazia')
        end=c.get('from',0)+c.get('duration',0)
    return {'errors':errors,'pending':pending,'ready':not errors and not pending,'mode':'master' if final else 'draft'}

def verify(path,project=None,decode=False):
    info=probe(path);errors=[]
    video=next((s for s in info['streams'] if s['codec_type']=='video'),{})
    audio=next((s for s in info['streams'] if s['codec_type']=='audio'),{})
    if str(video.get('profile')) not in ('Standard','2'): errors.append('Perfil ProRes não é Standard/422')
    expected={'codec_name':'prores','width':1440,'height':2560,'pix_fmt':'yuv422p10le','color_space':'bt709'}
    for key,value in expected.items():
        if video.get(key)!=value:errors.append(f'{key}: {video.get(key)} != {value}')
    for key in ('r_frame_rate','avg_frame_rate'):
        n,d=map(int,video.get(key,'0/1').split('/'))
        if not d or abs(n/d-60)>1e-6:errors.append(f'{key} não é 60 fps')
    if audio.get('codec_name') not in ('pcm_s16le','pcm_s24le','pcm_f32le') or audio.get('sample_rate')!='48000' or audio.get('channels')!=2:errors.append('Áudio deve ser PCM estéreo 48kHz')
    if project and abs(float(info['format']['duration'])-project['durationInFrames']/project['fps'])>1/60+.001:errors.append('Duração exportada diverge da timeline')
    if decode:subprocess.run([binary('ffmpeg'),'-v','error','-xerror','-i',str(path),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
    return {'technical_pass':not errors,'errors':errors,'metadata':info,'editorial_review':'not automated'}

def main():
    cli=argparse.ArgumentParser();sub=cli.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('inspect');a.add_argument('video',type=Path)
    a=sub.add_parser('validate');a.add_argument('--project',type=Path,default=ROOT/'src/empty-project.json');a.add_argument('--final',action='store_true')
    a=sub.add_parser('render');a.add_argument('--project',type=Path,default=ROOT/'src/empty-project.json');a.add_argument('--final',action='store_true');a.add_argument('--frames',help='Intervalo inclusivo, somente para prévia');a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('verify');a.add_argument('video',type=Path);a.add_argument('--project',type=Path);a.add_argument('--decode',action='store_true')
    args=cli.parse_args()
    if args.cmd=='inspect':result=probe(args.video)
    elif args.cmd=='verify':result=verify(args.video,json.loads(args.project.read_text()) if args.project else None,args.decode)
    else:
        p=json.loads(args.project.read_text());result=validate(p,args.final)
        if args.cmd=='render':
            raise ValueError('Use scripts/studio.py render VIDEO; o render legado foi desativado para respeitar armazenamento e revisões.')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if result.get('errors') or (args.cmd=='validate' and args.final and not result['ready']) or (result.get('verification',{}).get('technical_pass') is False) else 0

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,KeyError,TypeError,OSError,subprocess.CalledProcessError) as exc:print(f'Erro: {exc}',file=sys.stderr);sys.exit(2)
