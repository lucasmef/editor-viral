"""Offline cache/config/render interface for hair finishing. No job mutation or model inference.

Use hair_analyze.py to create inputs for a new video. This command can also pack
existing MatAnyone alpha sequences, so controls never require a second inference.
"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time
import wave
from pathlib import Path

import hair_controls as hc
import video_harness as vh
import hair_base

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def resource_file(path, relative_to):
    p = Path(path)
    p = p.resolve() if p.is_absolute() else (relative_to/p).resolve()
    hc.require(p.is_file(), f'Missing asset: {p}')
    return dict(path=str(p), sha256=hc.sha(p))


def verify_asset(asset):
    hc.require(hc.sha(asset['path']) == asset['sha256'], f"Cached asset changed: {asset['path']}")


def all_assets(cache):
    for scene in cache['scenes']:
        for key in ('roiVideo', 'fullVideo', 'donorVideo', 'patchMask'):
            yield scene[key]
        yield from scene['alpha']
        yield from scene.get('protection', [])


def video_info(path, size, frames, fps):
    import cv2
    cap = cv2.VideoCapture(str(path))
    try:
        actual = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]
        hc.require(cap.isOpened() and actual == size and abs(cap.get(cv2.CAP_PROP_FPS)-fps) < .001,
                   f'Video dimensions/fps mismatch: {path}')
        # Matroska duration rounds to milliseconds; its estimated frame count may
        # be one high. Decode rather than treating that estimate as ground truth.
        if int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) != frames:
            count=0
            while cap.read()[0]:count+=1
            hc.require(count==frames,f'Video frame count mismatch: {path}')
    finally:
        cap.release()


def load_mask(path, size, float_patch=False):
    import cv2
    import numpy as np
    p = Path(path)
    if float_patch and p.suffix == '.npy':
        a = np.load(p, allow_pickle=False)
        hc.require(a.dtype == np.float32, 'Float patch must be float32')
    else:
        a = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        hc.require(a is not None and a.dtype == np.uint16, f'Mask must be a 16-bit gray PNG: {path}')
        a = a.astype(np.float32)/65535
    hc.require(a.shape == (size[1], size[0]) and np.isfinite(a).all()
               and a.min() >= 0 and a.max() <= 1, f'Invalid mask shape/range: {path}')
    return a


def pack(plan_path, project_path, output):
    """Seal a prepared cache, rejecting stale cuts and missing/wrong masks."""
    plan_path = Path(plan_path).resolve(); output = Path(output).resolve()
    hc.require(not output.exists(), 'Cache manifest already exists')
    plan = read(plan_path); project = read(project_path); binding = hc.edit_binding(project)
    hc.require(plan.get('schemaVersion') == 1 and project['fps'] == 60, 'V1 requires schema 1 / 60 fps')
    hc.require(plan.get('binding') == binding, 'Prepared inputs belong to another cut')
    hc.require([s['id'] for s in plan['scenes']] == [s['id'] for s in binding['scenes']], 'Scene order mismatch')
    import numpy as np
    scenes = []; source_hashes = {}
    for p, cut in zip(plan['scenes'], binding['scenes']):
        frames = cut['frames']; scene = {**cut}
        for k in ('roi', 'alphaSize', 'nativeSize', 'fullSize', 'donorRoi', 'donorSize', 'detailBox'):
            scene[k] = p[k]
            hc.require(isinstance(p[k], list) and len(p[k]) == (4 if k in ('roi', 'donorRoi', 'detailBox') else 2)
                       and all(type(x) is int for x in p[k]), f'Invalid geometry: {k}')
        for k in ('nativeSize', 'fullSize', 'alphaSize', 'donorSize'):
            hc.require(all(0 < x <= 8192 for x in scene[k]), f'Invalid {k}')
        for rect, canvas in [('roi','nativeSize'), ('donorRoi','nativeSize'), ('detailBox','alphaSize')]:
            x,y,w,h=scene[rect]; cw,ch=scene[canvas]
            hc.require(x>=0 and y>=0 and w>0 and h>0 and x+w<=cw and y+h<=ch, f'{rect} outside canvas')
        nw,nh=scene['nativeSize']; fw,fh=scene['fullSize']
        hc.require(fw*nh == fh*nw and fw%2 == fh%2 == 0, 'Full preview must keep source aspect / even dimensions')
        source = Path(p['source']); source = source if source.is_absolute() else plan_path.parent/source
        if str(source) not in source_hashes:
            source_hashes[str(source)] = hc.sha(source)
        scene['source'] = dict(path=str(source.resolve()), sha256=source_hashes[str(source)])
        hc.require(cut['mediaId'] == 'm-'+scene['source']['sha256'], 'Source differs from the project media ID')
        for k in ('roiVideo', 'fullVideo', 'donorVideo', 'patchMask'):
            scene[k] = resource_file(p[k], plan_path.parent)
        for key, size in [('roiVideo','alphaSize'),('fullVideo','fullSize'),('donorVideo','donorSize')]:
            video_info(scene[key]['path'], scene[size], frames, 60)
        directory=Path(p['alphaDir']); directory=directory if directory.is_absolute() else plan_path.parent/directory
        expected=[directory/f'{i:04}.png' for i in range(frames)]
        hc.require(set(directory.glob('*.png')) == set(expected), 'Missing, extra or misnumbered alpha masks')
        scene['alpha'] = [resource_file(f, plan_path.parent) for f in expected]
        scene['protection'] = [resource_file(f, plan_path.parent) for f in p.get('protection', [])]
        hc.require(len(scene['protection']) in (0,1,frames), 'Protection must be empty, static, or one mask per frame')
        for asset in scene['alpha'] + scene['protection']:
            load_mask(asset['path'],scene['alphaSize'])
        patch=load_mask(scene['patchMask']['path'],scene['alphaSize'],True)
        scene['background']=hc.background_settings(p.get('background',{}))
        hc.donor_maps(scene, scene['background'], hc.prepare_patch(patch, scene['background']))
        scenes.append(scene)
    hc.require(len({tuple(s['fullSize']) for s in scenes}) == 1, 'Full preview size must be constant')
    provenance = plan.get('provenance', {})
    cache=dict(schemaVersion=1,kind='hair-alpha-cache',binding=binding,scenes=scenes,
               fps=60,frames=sum(s['frames'] for s in scenes),color='bt709-rgb8',
               provenance=provenance,sourceHashVerified=True)
    cache['cacheId']=hc.digest(cache);output.parent.mkdir(parents=True,exist_ok=True);write(output,cache)
    return dict(cache=str(output),cacheId=cache['cacheId'],frames=cache['frames'])


def validate(cache_path, config_path, project_path):
    cache=read(cache_path)
    hc.require(cache.get('schemaVersion')==1 and cache.get('kind')=='hair-alpha-cache', 'Invalid cache schema')
    hc.require(cache['cacheId']==hc.digest({k:v for k,v in cache.items() if k!='cacheId'}), 'Cache manifest changed')
    hc.require(cache['binding']==hc.edit_binding(read(project_path)), 'Cache belongs to another cut; reanalyze/realign')
    for asset in all_assets(cache):verify_asset(asset)
    config=read(config_path);settings=hc.validate_config(config,cache)
    for scene in cache['scenes']:
        b=settings[scene['id']]['background']
        patch=hc.prepare_patch(load_mask(scene['patchMask']['path'],scene['alphaSize'],True),b)
        hc.donor_maps(scene,b,patch)
    return cache,config,settings


def init_config(cache_path, output):
    cache=read(cache_path)
    config=dict(schemaVersion=1,cacheId=cache['cacheId'],defaults=dict(alpha=hc.ALPHA,intensity=1.,background={}),
                scenes={s['id']:dict(intervals=[],bypass=[]) for s in cache['scenes']})
    hc.validate_config(config,cache);write(output,config)
    return dict(config=str(output),cacheId=cache['cacheId'])


def encoder(path, size, fps):
    w,h=size
    return subprocess.Popen([vh.binary('ffmpeg'),'-v','error','-n','-f','rawvideo','-pix_fmt','bgr24',
        '-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-vf',
        'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
        '-c:v','libx264','-preset','fast','-crf','14','-pix_fmt','yuv420p','-colorspace','bt709',
        '-color_primaries','bt709','-color_trc','bt709','-bsf:v',
        'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
        '-movflags','+faststart+write_colr',str(path)],stdin=subprocess.PIPE)


def label(image, text):
    import cv2
    out=image.copy();cv2.rectangle(out,(0,0),(out.shape[1],28),(12,12,12),-1)
    cv2.putText(out,text,(7,20),0,.52,(245,245,245),1,cv2.LINE_AA);return out


def selection(cache, scene_id, frames):
    hc.require(not frames or scene_id is not None,'--frames requires --scene')
    hc.require(scene_id is None or scene_id in [s['id'] for s in cache['scenes']], 'Unknown scene')
    result=[]
    for scene in cache['scenes']:
        if scene_id and scene['id']!=scene_id:continue
        start,end=(map(int,frames.split(':')) if frames else (0,scene['frames']))
        hc.require(0<=start<end<=scene['frames'],'Invalid --frames, expected half-open from:to')
        result.append((scene,start,end))
    return result


def verify_outputs(out, sizes, frames, fps, pcm, pcm_codec='pcm_s16le'):
    import cv2
    result=[]
    for name,size in sizes.items():
        p=out/name;video_info(p,size,frames,fps);cap=cv2.VideoCapture(str(p));count=0
        while cap.read()[0]:count+=1
        cap.release();hc.require(count==frames,'Incomplete output decode')
        info=vh.probe(p);v=next(s for s in info['streams'] if s['codec_type']=='video')
        hc.require(all(v[k]=='bt709' for k in ('color_space','color_transfer','color_primaries')),'Output color mismatch')
        result.append(dict(file=name,sha256=hc.sha(p),frames=count,size=size))
    actual=hair_base.audio(out/'result-pcm.mov',pcm_codec)
    hc.require(actual==pcm,'PCM samples changed')
    return result


def render(cache_path, config_path, project_path, output, scene_id=None, frames=None, save_masks=False,
           base_video=None, quality='preview'):
    import cv2
    import numpy as np
    started=time.perf_counter();cache,config,settings=validate(cache_path,config_path,project_path)
    hc.require(quality in ('preview','production'),'Unknown hair quality')
    fullsize=cache['scenes'][0]['fullSize']; fw,fh=fullsize
    if quality=='production':
        project=read(project_path)
        hc.require(fullsize==[project['width'],project['height']], 'Production cache must match project size; no sample upscale')
    upstream=hair_base.inspect(base_video,fullsize,cache['frames']) if base_video else None
    selected=selection(cache,scene_id,frames);out=Path(output).resolve()
    hc.require(not out.exists(),'Output directory already exists; choose a new revision')
    out.mkdir(parents=True);write(out/'config.json',config)
    # Diagnostics use a fixed 2-column canvas across scenes with differing ROI sizes.
    sizes={'result':fullsize,'comparison':[fw*2,fh],'edges':[1168,420],'masks':[1168,420]}
    writers={};caps=[];rows=[];pcm=[];count=0;base_reader=None
    offsets={};cursor=0
    for s in cache['scenes']:offsets[s['id']]=cursor;cursor+=s['frames']
    pcm_codec=upstream['codec'] if upstream else 'pcm_s16le'
    try:
        writers={name:encoder(out/(name+'-silent.mp4'),size,cache['fps']) for name,size in sizes.items()}
        if quality=='production':writers['production']=hair_base.production_encoder(out/'production-silent.mov',fullsize)
        if upstream:base_reader=hair_base.Reader(base_video,fullsize)
        for scene,start,end in selected:
            sid=scene['id'];cfg=settings[sid];aw,ah=scene['alphaSize'];x,y,rw,rh=scene['roi'];nw,nh=scene['nativeSize']
            patch=hc.prepare_patch(load_mask(scene['patchMask']['path'],scene['alphaSize'],True),cfg['background'])
            maps=hc.donor_maps(scene,cfg['background'],patch)
            affine=np.array([[rw/aw*fw/nw,0,(x+.5*rw/aw)*fw/nw-.5],
                             [0,rh/ah*fh/nh,(y+.5*rh/ah)*fh/nh-.5]],np.float32)
            caps=[cv2.VideoCapture(scene[k]['path']) for k in ('roiVideo','fullVideo','donorVideo')]
            # Seek-by-frame on millisecond Matroska time bases can skip/duplicate
            # a boundary frame. Decode the prefix to keep ROI/donor/alpha exact.
            for cap in caps:
                for _ in range(start):hc.require(cap.read()[0],'Cached prefix ended early')
            protection=scene.get('protection',[])
            if save_masks:(out/('alpha-'+sid)).mkdir()
            for i in range(start,end):
                decoded=[cap.read() for cap in caps];hc.require(all(ok for ok,_ in decoded),'Cached video ended early')
                image,full,donor=[f for _,f in decoded]
                raw=load_mask(scene['alpha'][i]['path'],scene['alphaSize'])
                protect=load_mask(protection[0 if len(protection)==1 else i]['path'],scene['alphaSize']) if protection else None
                alpha,strength=hc.frame_controls(raw,cfg,i,protect)
                processed,effective,plate=hc.composite(image,donor,alpha,patch,strength,maps,cfg['background'])
                hc.require(np.array_equal(processed[effective==0],image[effective==0]),'Protected RGB changed before encoding')
                delta=cv2.warpAffine(processed.astype(np.float32)-image.astype(np.float32),affine,(fw,fh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
                result=np.clip(np.rint(full.astype(np.float32)+delta),0,255).astype(np.uint8)
                if base_reader:
                    full=base_reader.read(offsets[sid]+i)
                    result=hair_base.compose(full,plate,effective,affine)
                if strength==0:hc.require(np.array_equal(result,full),'Bypass is not exact')
                bx,by,bw,bh=scene['detailBox'];box=(slice(by,by+bh),slice(bx,bx+bw))
                pair=np.hstack([label(cv2.resize(image[box],(584,420)),'Original'),label(cv2.resize(processed[box],(584,420)),'Hair controls / '+sid)])
                gray=cv2.cvtColor(np.rint(alpha*255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
                changed=cv2.cvtColor(np.rint(effective*255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
                diagnostic=np.hstack([label(cv2.resize(gray[box],(584,420)),'Adjusted alpha'),label(cv2.resize(changed[box],(584,420)),'Fixed patch x (1-alpha)')])
                ims={'result':result,'comparison':np.hstack([label(full,'Original'),label(result,'Hair controls')]),'edges':pair,'masks':diagnostic}
                for name,im in ims.items():writers[name].stdin.write(im.tobytes())
                if quality=='production':writers['production'].stdin.write(result.tobytes())
                if save_masks:cv2.imwrite(str(out/('alpha-'+sid)/f'{i:04}.png'),np.rint(alpha*65535).astype(np.uint16))
                if count==0 or i%60==0 or i==end-1:
                    cv2.imwrite(str(out/f'edge-{sid}-{i:04}.jpg'),pair);cv2.imwrite(str(out/f'frame-{sid}-{i:04}.jpg'),result)
                rows.append(dict(frame=count,scene=sid,localFrame=i,sourceFrame=scene['inFrame']+i,
                                 intensity=float(strength),alphaDecreasedPixels=int(np.count_nonzero(alpha+1e-7<raw)),
                                 bypassRgbExact=bool(np.array_equal(result,full)) if strength==0 else None,
                                 upstreamProtectedRgbExact=True if base_reader else None))
                count+=1
            for cap in caps:cap.release()
            caps=[]
            # V1 cache contract deliberately requires PCM16 stereo, no silent down-conversion.
            info=vh.probe(scene['fullVideo']['path']);audio=next(s for s in info['streams'] if s['codec_type']=='audio')
            hc.require(audio['codec_name']=='pcm_s16le' and audio['sample_rate']=='48000' and audio['channels']==2,
                       'Hair cache audio must be PCM16 stereo 48kHz; do not down-convert another finishing master')
            samples=hair_base.audio(base_video,pcm_codec,offsets[sid]+start,offsets[sid]+end) if upstream else subprocess.check_output([vh.binary('ffmpeg'),'-v','error','-i',scene['fullVideo']['path'],
                '-map','0:a:0','-af',f'atrim=start_sample={start*800}:end_sample={end*800},asetpts=PTS-STARTPTS',
                '-f','s16le','-c:a','pcm_s16le','-'])
            hc.require(len(samples)==(end-start)*800*2*hair_base.PCM[pcm_codec][1],'Audio/cut length mismatch');pcm.append(samples)
            print(f'rendered {sid} [{start},{end})',flush=True,file=sys.stderr)
        for p in writers.values():p.stdin.close();hc.require(p.wait()==0,'Encoder failed')
        raw_pcm=b''.join(pcm)
        if base_reader:base_reader.close();base_reader=None
        audio_path=out/('audio.mov' if upstream else 'audio.wav')
        if upstream:hair_base.audio_file(audio_path,raw_pcm,pcm_codec)
        else:
            with wave.open(str(audio_path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(raw_pcm)
        for name in sizes:
            subprocess.run([vh.binary('ffmpeg'),'-v','error','-n','-i',str(out/(name+'-silent.mp4')),'-i',str(audio_path),
                '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart+write_colr',str(out/(name+'.mp4'))],check=True)
        video_path=out/('production-silent.mov' if quality=='production' else 'result-silent.mp4')
        subprocess.run([vh.binary('ffmpeg'),'-v','error','-n','-i',str(video_path),'-i',str(audio_path),
            '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a',pcm_codec,str(out/'result-pcm.mov')],check=True)
        outputs=verify_outputs(out,{**{n+'.mp4':s for n,s in sizes.items()},'result-pcm.mov':fullsize},count,60,raw_pcm,pcm_codec)
        verified=hair_base.inspect(out/'result-pcm.mov',fullsize,count)
        if quality=='production':
            v=next(v for v in vh.probe(out/'result-pcm.mov')['streams'] if v['codec_type']=='video')
            hc.require(v['codec_name']=='prores' and str(v['profile']) in ('Standard','2') and
                       v['pix_fmt']=='yuv422p10le','Production intermediate must be ProRes 422 Standard')
        if upstream:hc.require(hc.sha(base_video)==upstream['sha256'],'Upstream changed during hair render')
        for asset in all_assets(cache):verify_asset(asset)
        hc.require(cache['binding']==hc.edit_binding(read(project_path)),'Cut changed during render')
        write(out/'metrics.json',rows)
        report=dict(version=hc.VERSION,technicalPass=True,cacheId=cache['cacheId'],configSha256=hc.sha(out/'config.json'),
                    binding=cache['binding'],selection=[dict(scene=s['id'],start=a,end=b) for s,a,b in selected],
                    fullCut=scene_id is None,frames=count,fps=60,size=fullsize,pcmBitExact=True,outputs=outputs,
                    seconds=time.perf_counter()-started,peakPythonRssBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    scripts={n:hc.sha(ROOT/'scripts'/n) for n in ('hair_controls.py','hair_finish.py','hair_base.py')},
                    upstream=upstream,quality=quality,pcmCodec=pcm_codec,ptsVerified=True,
                    productionIntermediate=quality=='production',
                    visualAcceptance='pending',continuousPlaybackByAssistant='not confirmed',sourceAlphaUnchanged=True,
                    productionMaster=False,modelInferenceRun=False)
        write(out/'report.json',report)
        return report
    except BaseException as error:
        # Persist the cause before cleanup: FFmpeg may otherwise wait for stdin
        # forever after SIGTERM while its raw-video pipe is still open.
        write(out/'failed.json',dict(error=str(error),technicalPass=False))
        if base_reader:base_reader.close()
        for cap in caps:cap.release()
        for p in writers.values():
            try:
                if p.stdin and not p.stdin.closed:p.stdin.close()
            except (BrokenPipeError,OSError):pass
        for p in writers.values():
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait()
        raise



def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('pack');p.add_argument('--plan',required=True);p.add_argument('--project',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('init');p.add_argument('--cache',required=True);p.add_argument('--out',required=True)
    for name in ('validate','render'):
        p=sub.add_parser(name);p.add_argument('--cache',required=True);p.add_argument('--config',required=True);p.add_argument('--project',required=True)
        if name=='render':
            p.add_argument('--out',required=True);p.add_argument('--scene');p.add_argument('--frames');p.add_argument('--save-masks',action='store_true')
            p.add_argument('--base-video');p.add_argument('--quality',choices=['preview','production'],default='preview')
    args=parser.parse_args()
    if args.command=='pack':result=pack(args.plan,args.project,args.out)
    elif args.command=='init':result=init_config(args.cache,args.out)
    elif args.command=='validate':
        cache,_,_=validate(args.cache,args.config,args.project);result=dict(valid=True,cacheId=cache['cacheId'],frames=cache['frames'])
    else:result=render(args.cache,args.config,args.project,args.out,args.scene,args.frames,args.save_masks,args.base_video,args.quality)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as error:
        print(f'Error: {error}',file=sys.stderr);sys.exit(2)
