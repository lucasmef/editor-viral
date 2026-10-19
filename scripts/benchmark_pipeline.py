"""Repeatable local benchmark on a caller-selected short fixture, never production in place."""
import argparse
import subprocess
from pathlib import Path
import studio as s
from pipeline_cache import Metrics, ProbeCache, cached_build, sha
from render_cache import stage_copy
import shutil


def benchmark(source,out):
    source=Path(source).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('New benchmark directory required')
    if float(s.vh.probe(source)['format']['duration'])>10:raise ValueError('Use a short fixture of at most 10 seconds')
    out.mkdir(parents=True)
    metrics=Metrics();probe=ProbeCache(s.vh.probe,metrics)
    with metrics.measure('three-uncached-probes'):
        for _ in range(3):s.vh.probe(source)
    with metrics.measure('three-memoized-probes'):
        for _ in range(3):probe(source)
    with metrics.measure('copy2'):shutil.copy2(source,out/'copy.mov')
    with metrics.measure('independent-clone') as event:event.update(stage_copy(source,out/'clone.mov'))
    ff=s.ROOT/'.local-bin/ffmpeg'
    recipe={'adapter':sha(__file__),'ffmpeg':sha(ff),'filter':'eq=brightness=0.01','profile':2}
    def render(target):
        subprocess.run([str(ff),'-nostdin','-v','error','-i',str(source),'-an','-vf',recipe['filter'],'-c:v','prores_ks','-profile:v','2','-pix_fmt','yuv422p10le','-threads','4',str(target)],check=True)
    for name in ('cold-cache','warm-cache'):
        with metrics.measure(name):cached_build(out/'cache',recipe,[source],'.mov',render,metrics)
    report={'sourceSha256':sha(source),'sourceBytes':source.stat().st_size,'scope':'one short fixture; not a whole-video speed forecast',**metrics.report()}
    s.write(out/'performance.json',report,True)
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('--out',required=True);a=ap.parse_args()
    print(__import__('json').dumps(benchmark(a.source,s.output_path(a.out)),indent=2))
