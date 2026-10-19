"""Process real source handles per scene; conform without discarding extended WAVs.

Separate from the legacy automatic voice connector. Requires a cut-only user
approval, a frozen window recipe, and the unchanged approved processor bundle.
"""
import argparse
import copy
import os
from pathlib import Path
import wave
import studio as s
import voice_connector as voice
import finishing_windows as windows


def sample_range(window, scene, fps=60):
    if fps != 60 or window['sourceMediaId'] != scene['clip']['mediaId']:
        raise ValueError('Fonte/fps divergente')
    a = scene['clip']['inFrame']; b = a+scene['duration']
    if not window['sourceIn'] <= a < b <= window['sourceOut']:
        raise ValueError('Corte fora da janela de voz')
    return (a-window['sourceIn'])*800, (b-window['sourceIn'])*800


def require_cut(job, evidence):
    d=s.load(job); e=s.read(evidence)
    if (e.get('scope')!='cut-only' or e.get('job')!=job or not e.get('userApproval')
            or e.get('editHash')!=s.edit_hash(d) or s.sha(e['output'])!=e['outputSha256']):
        raise ValueError('Aprovação real do corte atual pendente')
    return d


def process(job, window_work, evidence, out):
    d=require_cut(job,evidence); h=windows.Host(s,job,window_work)
    windows.select(h.manifest['windows'],d['project.json'])
    profile=d['finishing.json']['voiceNeural']; frozen=voice.bundle(s,profile)
    out=s.persistent_path(out);out.mkdir(parents=True,exist_ok=False)
    entries=[];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
    recipe=h.load(job)
    for window,sc in zip(h.manifest['windows'],recipe['project.json']['scenes']):
        work=out/s.safe_id(sc['id']);work.mkdir()
        one=copy.deepcopy(recipe);one['project.json']['scenes']=[sc]
        source, originals, segments=voice.extract(s,one,work)
        output=work/'voice-with-handles.wav'
        cmd=[frozen/'python/bin/python3.12',frozen/'processor/independent_voice_runner.py',source,output]
        voice.run(cmd,work,'runner',env)
        voice.verify_wav(output,voice.sample_count(one))
        diagnostics=s.read(output.with_suffix('.json'))
        if diagnostics['settings']!=s.read(frozen/'preset.json'):
            raise ValueError('Preset de voz divergente')
        for info in originals.values():
            if s.sha(info['path'])!=info['sha256']:raise ValueError('Fonte alterada')
        entries.append(dict(window=window,output=str(output),outputSha256=s.sha(output),
                            inputSha256=s.sha(source),samples=voice.sample_count(one),
                            diagnosticsSha256=s.sha(output.with_suffix('.json')),segments=segments,
                            gainAppliedDb=0,perceptualReview='pending'))
        print(sc['id'],output,flush=True)
    voice.bundle(s,profile)
    report=dict(version='voice-windows-v1',job=job,windowWork=str(h.work),
                windowManifestSha256=s.sha(h.work/'windows.json'),recipeSha256=h.manifest['projectSha256'],
                profile=profile,adapterSha256=s.sha(__file__),cutApprovalSha256=s.sha(evidence),
                sampleRate=48000,bits=24,channels=2,entries=entries,createdAt=s.now())
    s.write(out/'report.json',report,True)
    s.log(job,'voice-windows-processed',report=str(out/'report.json'))
    return out/'report.json'


def conform(job, report_path, out):
    report=s.read(report_path);d=s.load(job)
    if report['job']!=job or report['version']!='voice-windows-v1':raise ValueError('Pacote de outro vídeo')
    voice.bundle(s,report['profile'])
    h=windows.Host(s,job,report['windowWork'])
    if s.sha(h.work/'windows.json')!=report['windowManifestSha256']:raise ValueError('Janelas alteradas')
    out=s.persistent_path(out)
    if out.exists():raise ValueError('Use saída nova')
    out.parent.mkdir(parents=True,exist_ok=True)
    parts=[]
    for scene in d['project.json']['scenes']:
        matches=[e for e in report['entries'] if e['window']['scene']==scene['id']]
        if len(matches)!=1:raise ValueError('Cena sem voz única')
        entry=matches[0];a,b=sample_range(entry['window'],scene,d['project.json']['fps'])
        if s.sha(entry['output'])!=entry['outputSha256']:raise ValueError('Voz alterada')
        voice.verify_wav(entry['output'],entry['samples'])
        parts.append((entry,a,b))
    with wave.open(str(out),'wb') as dest:
        dest.setparams((2,3,48000,0,'NONE','not compressed'))
        for entry,a,b in parts:
            with wave.open(entry['output'],'rb') as src:
                src.setpos(a);dest.writeframes(src.readframes(b-a))
    voice.verify_wav(out,voice.sample_count(d))
    conform_report={'editHash':s.edit_hash(d),'sourceReport':str(Path(report_path).resolve()),
                    'sourceReportSha256':s.sha(report_path),'outputSha256':s.sha(out),
                    'segments':[{'scene':e['window']['scene'],'source':e['output'],'inSample':a,'outSample':b} for e,a,b in parts],
                    'note':'Montagem de escuta derivada; WAVs por cena com margens preservados como fontes para Premiere. Sem novo ganho, sem preenchimento artificial.'}
    s.write(out.with_suffix('.conform.json'),conform_report,True)
    if s.edit_hash(s.load(job))!=conform_report['editHash']:raise ValueError('Corte mudou; não associar')
    s.attach_finish(job,'audio',out,'Voz por janelas; '+str(report_path)+'; reconformação explícita; ganho zero')
    f=s.read(s.jobdir(job)/'finishing.json');f['audioGainDb']=0
    f['voiceWindows']={'report':str(Path(report_path).resolve()),'reportSha256':s.sha(report_path),
                       'conformReport':str(out.with_suffix('.conform.json')),'conformReportSha256':s.sha(out.with_suffix('.conform.json'))}
    s.write(s.jobdir(job)/'finishing.json',f)
    s.log(job,'voice-windows-conformed',report=str(out.with_suffix('.conform.json')))


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('process');a.add_argument('job');a.add_argument('--window-work',required=True);a.add_argument('--approval',required=True);a.add_argument('--out',required=True)
    a=sub.add_parser('conform');a.add_argument('job');a.add_argument('--report',required=True);a.add_argument('--out',required=True)
    a=p.parse_args()
    if a.command=='process':print(process(a.job,a.window_work,a.approval,a.out))
    else:conform(a.job,a.report,a.out)
