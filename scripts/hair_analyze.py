"""Create a reusable local MatAnyone 2 cache from an explicit per-scene analysis plan.

Requires the separately installed, pinned MatAnyone code/weights and manual seeds.
No automatic downloads, RGB foreground generation, makeup processing or job writes.
"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import hair_controls as hc
import hair_finish as finish
import video_harness as vh


def resolve(path, parent):
    p=Path(path)
    return p.resolve() if p.is_absolute() else (parent/p).resolve()


def source_metadata(path):
    exe=vh.binary('ffprobe');env=dict(os.environ)
    if (Path(exe).parent/'libavdevice.dylib').exists():env['DYLD_LIBRARY_PATH']=str(Path(exe).parent)
    return json.loads(subprocess.check_output([exe,'-v','error','-show_streams','-of','json',str(path)],env=env))


def analyze(plan_path, output):
    os.environ['HF_HUB_OFFLINE']='1';os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','1')
    import cv2
    import numpy as np
    import torch
    plan_path=Path(plan_path).resolve();plan=finish.read(plan_path);parent=plan_path.parent
    project_path=resolve(plan['project'],parent);project=finish.read(project_path);binding=hc.edit_binding(project)
    hc.require(plan.get('schemaVersion')==1 and project['fps']==60,'V1 requires schema 1 and a 60 fps project')
    hc.require([s['id'] for s in plan['scenes']]==[s['id'] for s in binding['scenes']], 'List every scene in cut order')
    code=resolve(plan['model']['code'],parent);weights=resolve(plan['model']['weights'],parent)
    device=plan['model'].get('device','mps');hc.require(device in ('mps','cpu'),'Supported devices: mps, cpu')
    hc.require(weights.is_file() and (code/'matanyone2/config').is_dir(),'Local model code/weights missing')
    hc.require(device!='mps' or torch.backends.mps.is_available(),'MPS unavailable; expose local GPU or explicitly choose cpu')
    checked=[]
    for spec,cut in zip(plan['scenes'],binding['scenes']):
        s=dict(spec)
        for key in ('source','seed','patchMask'):s[key]=str(resolve(spec[key],parent))
        s['protection']=[str(resolve(p,parent)) for p in spec.get('protection',[])]
        info=source_metadata(s['source']);v=next(x for x in info['streams'] if x['codec_type']=='video')
        from fractions import Fraction
        hc.require(abs(float(Fraction(v['avg_frame_rate']))-60)<.02,'Source fps differs from the 60 fps cut')
        hc.require(all(v.get(k)=='bt709' for k in ('color_space','color_transfer','color_primaries')),
                   'Only Rec.709 input is supported; normalize color explicitly before analysis')
        hc.require(v.get('color_range')=='tv' and v.get('sample_aspect_ratio','1:1') in ('1:1','N/A'),
                   'Source must be limited-range Rec.709 with square pixels')
        hc.require(not float(v.get('tags',{}).get('rotate',0)) and
                   all(not float(d.get('rotation',0)) for d in v.get('side_data_list',[])),
                   'Normalize rotation before drawing seeds/ROIs')
        audios=[x for x in info['streams'] if x['codec_type']=='audio']
        hc.require(len(audios)==1 and audios[0]['codec_name'] in ('aac','pcm_s16le')
                   and audios[0]['sample_rate']=='48000' and audios[0]['channels']==2,
                   'V1 source audio must be AAC or PCM16 stereo 48kHz; no implicit down-conversion of PCM24/float')
        duration=float(v.get('duration') or vh.probe(s['source'])['format']['duration'])
        hc.require((cut['inFrame']+cut['frames'])/60 <= duration+1e-6,
                   'Cut exceeds source duration; EOF padding cannot extend a cut')
        s['nativeSize']=[v['width'],v['height']]
        for key in ('roi','donorRoi'):
            x,y,w,h=s[key];nw,nh=s['nativeSize']
            hc.require(all(type(z)is int for z in s[key]) and x>=0 and y>=0 and w>0 and h>0 and x+w<=nw and y+h<=nh,
                       f'Invalid {key}')
        seed=cv2.imread(s['seed'],cv2.IMREAD_UNCHANGED)
        hc.require(seed is not None and seed.dtype==np.uint8 and seed.shape==(s['alphaSize'][1],s['alphaSize'][0])
                   and set(np.unique(seed)).issubset({0,255}) and 0<np.count_nonzero(seed)<seed.size,
                   'Seed must be a nonempty binary 8-bit PNG matching alphaSize')
        patch=finish.load_mask(s['patchMask'],s['alphaSize'],True)
        hc.donor_maps(s,hc.background_settings(s.get('background',{})),hc.prepare_patch(patch,hc.background_settings(s.get('background',{}))))
        checked.append(s)
    out=Path(output).resolve();hc.require(not out.exists(),'Analysis output already exists; use a new revision');out.mkdir(parents=True)
    started=time.perf_counter();sys.path.insert(0,str(code))
    from hydra import initialize_config_dir,compose
    from omegaconf import open_dict
    from matanyone2.model.matanyone2 import MatAnyone2
    from matanyone2.inference.inference_core import InferenceCore
    torch.set_num_threads(6)
    with initialize_config_dir(version_base='1.3',config_dir=str(code/'matanyone2/config')):cfg=compose(config_name='eval_matanyone_config')
    with open_dict(cfg):cfg.model.pretrained_resnet=False
    model=MatAnyone2(cfg,single_object=True).to(device).eval()
    model.load_weights(torch.load(weights,map_location=device,weights_only=True))
    records=[];prepared=[]
    for ci,(s,cut) in enumerate(zip(checked,binding['scenes']),1):
        start=cut['inFrame'];n=cut['frames'];aw,ah=s['alphaSize'];dw,dh=s['donorSize'];fw,fh=s['fullSize']
        for key,rect,size in [('roiVideo',s['roi'],[aw,ah]),('donorVideo',s['donorRoi'],[dw,dh]),('fullVideo',None,[fw,fh])]:
            path=out/f'{key}-{ci}.mkv';crop='crop='+':'.join(map(str,[rect[2],rect[3],rect[0],rect[1]]))+',' if rect else ''
            vf=crop+f'scale={size[0]}:{size[1]}:in_color_matrix=bt709:in_range=tv:out_range=pc,tpad=stop_mode=clone:stop_duration=0.05,fps=60,setpts=PTS-STARTPTS'
            # Flush fps at exact EOF; cap at the validated cut frame count.
            # A 60-frame CFR regression retains all 60 original decoded frames.
            # Match the approved donor's RGB24 conversion before lossless BGRA
            # packing. Negotiating BGRA directly selects a different scaler path.
            if key=='donorVideo':vf+=',format=bgr24'
            cmd=[vh.binary('ffmpeg'),'-v','error','-n','-ss',str(start/60),'-i',s['source'],'-t',str(n/60+.1),
                 '-vf',vf,'-frames:v',str(n),'-fps_mode','cfr','-r','60','-c:v','ffv1','-pix_fmt','bgr0']
            # -frames:v can stop audio muxing before the last audio packet.
            # Extract exact PCM separately, then mux without -shortest.
            cmd+=['-an']
            if key=='fullVideo':
                silent=out/f'fullVideo-silent-{ci}.mkv';audio=out/f'fullAudio-{ci}.wav'
                subprocess.run(cmd+[str(silent)],check=True)
                subprocess.run([vh.binary('ffmpeg'),'-v','error','-n','-ss',str(start/60),'-i',s['source'],
                    '-map','0:a:0','-af',f'atrim=end_sample={n*800},asetpts=N/SR/TB',
                    '-c:a','pcm_s16le','-ar','48000','-ac','2',str(audio)],check=True)
                import wave
                with wave.open(str(audio),'rb') as wav:
                    hc.require(wav.getnframes()==n*800,'Source audio shorter than requested cut')
                subprocess.run([vh.binary('ffmpeg'),'-v','error','-n','-i',str(silent),'-i',str(audio),
                    '-map','0:v:0','-map','1:a:0','-c','copy',str(path)],check=True)
            else:subprocess.run(cmd+[str(path)],check=True)
            s[key]=str(path)
        dest=out/f'alpha-{ci}';dest.mkdir();s['alphaDir']=str(dest)
        cap=cv2.VideoCapture(s['roiVideo']);processor=InferenceCore(model,cfg=model.cfg,device=torch.device(device));durations=[]
        with torch.inference_mode():
            for i in range(n):
                ok,frame=cap.read();hc.require(ok,'Input ended during inference')
                src=torch.from_numpy(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB).transpose(2,0,1).copy()).float().to(device)/255
                t=time.perf_counter()
                if i==0:
                    seed=torch.from_numpy(cv2.imread(s['seed'],0).astype(np.float32)).to(device)
                    processor.step(src,seed,objects=[1]);prob=processor.step(src,first_frame_pred=True)
                    for _ in range(10):prob=processor.step(src,first_frame_pred=True)
                else:prob=processor.step(src)
                alpha=processor.output_prob_to_mask(prob).cpu().numpy()
                hc.require(np.isfinite(alpha).all() and alpha.min()>=0 and alpha.max()<=1.00001,'Invalid model alpha')
                cv2.imwrite(str(dest/f'{i:04}.png'),np.rint(np.clip(alpha,0,1)*65535).astype(np.uint16));durations.append(time.perf_counter()-t)
                if i%60==0:print(f"{cut['id']} {i}/{n}",file=sys.stderr,flush=True)
        cap.release();del processor
        if device=='mps':torch.mps.empty_cache()
        records.append(dict(scene=cut['id'],seedSha256=hc.sha(s['seed']),seconds=sum(durations),frames=n))
        prepared.append({k:v for k,v in s.items() if k!='seed'})
    provenance=dict(method='MatAnyone2',weightsSha256=hc.sha(weights),planSha256=hc.sha(plan_path),
                    modelCodeSha256=hc.digest({str(p.relative_to(code)):hc.sha(p) for p in sorted((code/'matanyone2').rglob('*')) if p.suffix in ('.py','.yaml')}),
                    device=device,torch=torch.__version__,warmupRepeats=10,scenes=records,
                    seconds=time.perf_counter()-started,peakPythonRssBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    scriptSha256=hc.sha(__file__),foreground='original RGB only',approval='pending')
    finish.write(out/'inference.json',provenance)
    finish.write(out/'plan.json',dict(schemaVersion=1,binding=binding,scenes=prepared,provenance=provenance))
    result=finish.pack(out/'plan.json',project_path,out/'cache.json');finish.init_config(out/'cache.json',out/'controls.json')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args()
    try:print(json.dumps(analyze(args.plan,args.out),indent=2))
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as error:
        print(f'Error: {error}',file=sys.stderr);sys.exit(2)
