"""Small synthetic, isolated host test. Never reads or edits a production job."""
import argparse
import json
import subprocess
from pathlib import Path
import studio as s
from premiere_package import write_xml
from pipeline_cache import sha, Metrics, ProbeCache


def build(out):
    out=Path(out).resolve()
    if out.exists():raise ValueError('Use a new fixture directory')
    out.mkdir(parents=True)
    ff=s.ROOT/'.local-bin/ffmpeg'
    video=out/'fixture-4k.mov';audio=out/'fixture-voice.wav'
    subprocess.run([str(ff),'-v','error','-f','lavfi','-i','color=c=0x183f68:s=2160x3840:r=60:d=3','-an','-c:v','prores_ks','-profile:v','2','-pix_fmt','yuv422p10le','-threads','4',str(video)],check=True)
    subprocess.run([str(ff),'-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=3','-ac','2','-c:a','pcm_s24le',str(audio)],check=True)
    import psd_cutouts as psd
    from psd_tools.api.layers import PixelLayer
    image=psd.Image.new('RGB',(300,500),'red')
    original=psd.PSDImage.new('RGB',image.size);original.append(PixelLayer.frompil(image,original,'pixels originais'));original.save(out/'original.psd')
    mask=psd.Image.new('L',image.size,255)
    from PIL import ImageDraw
    ImageDraw.Draw(mask).rectangle((0,0,99,499),fill=0);mask.save(out/'mask.png')
    psd.mask_layer(out/'original.psd',[0],out/'mask.png',out/'masked.psd')
    psd.export_png(out/'masked.psd',out/'masked.png')
    from premiere_package import build as build_package
    ident=lambda path:dict(path=str(path),sha256=sha(path))
    layers=[]
    for index,ext in enumerate(('png','psd')):
        source=out/('masked.'+ext)
        provenance={'assetSha256':sha(source),'original':{**ident(out/'original.psd'),'pixelSize':[300,500]},'resampled':False,
                    'recovery':{'kind':'layered-psd','document':ident(out/'masked.psd'),'inspection':ident(out/'masked.inspection.json')}}
        layers.append(dict(id='masked-'+ext,src=str(source),from_=0,duration=60,transition='cut',rect=dict(x=200+650*index,y=350,width=300,height=500),cutoutProvenance=provenance))
        layers[-1]['from']=layers[-1].pop('from_')
    snapshot=dict(videoId='editor-transfer-fixture',fps=60,width=1440,height=2560,durationInFrames=60,premiereCaptionPosition=[720,1030],layout={'base':{'scale':1,'x':0,'y':0},'labels':[]},captions=[{'text':'rico','from':1,'duration':59,'highlight':True}],scenes=[{'id':'s1','from':0,'duration':60,'layers':layers}])
    manifest={'entries':[{'scene':'s1','file':str(video),'sha256':sha(video),'audio':str(audio),'audioSha256':sha(audio),'frames':180,'cutIn':60,'cutOut':120,'sourceWindow':{'sourceMediaId':'fixture','sourceIn':0,'sourceOut':180,'approvedIn':60,'approvedDuration':60}}]}
    p=build_package('editor-transfer-fixture',snapshot,manifest,out/'package',s.ROOT/'studio/templates/premiere/palavra-101-v1.mogrt',s.ROOT/'studio/templates/premiere/palavra-101-v1.approval.json',lambda path:Path(path))
    # Lead gap exists only in the diagnostic timeline, permitting safe head extension.
    for clip in p['clips']:clip['start']+=60
    for caption in p['captions']:caption['from']+=60
    p['durationInFrames']=180
    write_xml(p,out/'fixture.xml');s.write(out/'expected.json',p)
    metrics=Metrics();probe=ProbeCache(s.vh.probe,metrics)
    with metrics.measure('uncached-three-probes'):
        for _ in range(3):s.vh.probe(video)
    with metrics.measure('memoized-three-probes'):
        for _ in range(3):probe(video)
    s.write(out/'metrics.json',metrics.report())
    print(out,flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);build(ap.parse_args().out)
