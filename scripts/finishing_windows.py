"""4K finishing recipes independent of the editable delivery timeline.

Recipes are frozen processing inputs, not alternative editable jobs. Existing face
and hair connectors retain all their checks against this exact processing recipe.
"""
import copy
from pathlib import Path
import face_connector as face
import hair_connector as hair

VERSION = 'finishing-windows-v1'
SIZE = (2160, 3840, 60)


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Host:
    def __init__(self, studio, job, work):
        self.studio, self.job = studio, job
        self.work = studio.persistent_path(work)
        self.manifest = studio.read(self.work/'windows.json')
        require(self.manifest['version'] == VERSION and self.manifest['job'] == job, 'Receita de outro vídeo')
        require(studio.sha(self.work/'recipe/project.json') == self.manifest['projectSha256'], 'Receita de janelas alterada')

    def __getattr__(self, name):
        return getattr(self.studio, name)

    def jobdir(self, job):
        require(job == self.job, 'Job divergente')
        return self.work/'recipe'

    def load(self, job):
        require(self.sha(self.work/'recipe/project.json') == self.manifest['projectSha256'], 'Receita alterada')
        return {n: self.read(self.jobdir(job)/n) for n in self.DOCS}

    def log(self, job, action, **details):
        self.studio.log(job, 'window-'+action, windowWork=str(self.work), **details)

    def attach_finish(self, job, kind, path, notes, automatic=False):
        d=self.load(job); mid=self.register(self.persistent_path(path),kind)
        f=d['finishing.json']; f[kind+'MediaId']=mid; f[kind+'EditHash']=self.edit_hash(d); f[kind+'Notes']=notes
        self.write(self.jobdir(job)/'finishing.json',f)
        return {'mediaId':mid,'review':'pending'}


def initialize(s, job, plan_path, work):
    d=s.load(job); p=d['project.json']; plan=s.read(plan_path); work=s.persistent_path(work)
    require(not work.exists(), 'Use uma nova execução')
    require(p['fps']==60 and plan.get('reviewed') is True and plan.get('notes'), 'Revisar limites reais das janelas')
    require(set(plan['scenes'])=={x['id'] for x in p['scenes']}, 'Plano deve cobrir todas as cenas')
    windows=[]; offset=0; frozen=copy.deepcopy(d)
    for sc in frozen['project.json']['scenes']:
        start,end=plan['scenes'][sc['id']]; original=sc['clip']['inFrame']; duration=sc['duration']
        require(type(start) is int and type(end) is int and 0<=start<=original and end>=original+duration, 'Janela não cobre o corte')
        info=s.vh.probe(s.resolve(sc['clip']['mediaId']));v=next(v for v in info['streams'] if v['codec_type']=='video')
        require(v['width']>=SIZE[0] and v['height']>=SIZE[1], 'Fonte menor que 4K; não ampliar silenciosamente')
        require(end/60 <= float(v.get('duration') or info['format']['duration']), 'Janela além do bruto')
        windows.append(dict(scene=sc['id'],sourceMediaId=sc['clip']['mediaId'],sourceIn=start,sourceOut=end,packFrom=offset,
                            approvedIn=original,approvedDuration=duration,headFrames=original-start,tailFrames=end-original-duration))
        offset+=end-start;sc.update(duration=end-start,layers=[],captions=[],events=[]);sc.pop('looks',None)
        sc['clip']={'mediaId':sc['clip']['mediaId'],'inFrame':start}
    frozen['project.json'].update(width=2160,height=3840,fps=60,requireLookReview=False)
    frozen['finishing.json']={'audioGainDb':0,'soundEffects':[]}
    s.checkpoint(job,'Antes de acabamento 4K com margens; corte atual preservado')
    for n,value in frozen.items():s.write(work/'recipe'/n,value,True)
    manifest=dict(version=VERSION,job=job,format=list(SIZE),windows=windows,plan=plan,frames=offset,
                  projectSha256=s.sha(work/'recipe/project.json'),createdAt=s.now())
    s.write(work/'windows.json',manifest,True);s.log(job,'window-init',work=str(work),windows=windows)
    return manifest


def select(windows, project):
    require(project['fps']==60, 'Janelas exigem 60 fps')
    result={}
    for scene in project['scenes']:
        matches=[w for w in windows if w['scene']==scene['id'] and w['sourceMediaId']==scene['clip']['mediaId']]
        require(len(matches)==1,'Cena/fonte sem janela tratada: '+scene['id'])
        w=matches[0];start=scene['clip']['inFrame'];end=start+scene['duration']
        require(w['sourceIn']<=start<end<=w['sourceOut'],'Corte fora da margem tratada: '+scene['id'])
        result[scene['id']]=w['packFrom']+start-w['sourceIn']
    return result


def publish(s, job, work):
    h=Host(s,job,work);d=h.load(job); face.validate_attached(h,d)
    require(d['finishing.json'].get('videoConnector'), 'Maquiagem com procedência obrigatória')
    hd=d['finishing.json'].get('hair',{}); require(hd.get('enabled'), 'Cabelo completo obrigatório')
    stage,report,path=hair.verify_run(h,d,hd['output']['work'])
    require(report['size']==[2160,3840] and report['quality']=='production','Acabamento precisa ser 4K ProRes')
    require(h.sha(h.resolve(hd['output']['mediaId']))==h.sha(path),'Mídia de cabelo diferente da execução verificada')
    select(h.manifest['windows'],s.load(job)['project.json'])
    evidence=[h.work/'windows.json',h.work/'recipe/project.json',h.work/'recipe/finishing.json',
              Path(hd['output']['work'])/'stage.json',Path(hd['output']['work'])/'render/report.json']
    fc=d['finishing.json']['videoConnector']
    evidence += [Path(fc['work'])/'treated.report.json',Path(fc['temporalReview'])]
    seal=dict(version=VERSION,work=str(h.work),windows=h.manifest['windows'],format=list(SIZE),
              videoMediaId=hd['output']['mediaId'],evidence={str(p):s.sha(p) for p in evidence},createdAt=s.now())
    s.write(h.work/'sealed.json',seal,True)
    current=s.load(job);finish=current['finishing.json'];previous=copy.deepcopy(finish)
    for key in ('videoMediaId','videoEditHash','videoNotes','videoConnector','hair'):finish.pop(key,None)
    finish['windows']={'work':str(h.work),'sealSha256':s.sha(h.work/'sealed.json'),'videoMediaId':seal['videoMediaId']}
    s.write(s.jobdir(job)/'finishing.json',finish);s.log(job,'window-publish',previousFinishing=previous,windows=finish['windows'])
    return finish['windows']


def compiled(s,d):
    config=d['finishing.json'].get('windows')
    if not config:return None
    require(not d['finishing.json'].get('videoMediaId') and not d['finishing.json'].get('hair',{}).get('enabled'), 'Bases de acabamento concorrentes')
    path=Path(config['work'])/'sealed.json'
    require(s.sha(path)==config['sealSha256'],'Selo das janelas alterado')
    seal=s.read(path);require(seal['version']==VERSION and seal['format']==list(SIZE),'Formato das janelas inválido')
    require(config['videoMediaId']==seal['videoMediaId'],'Mídia diferente do selo')
    for name,digest in seal['evidence'].items():require(s.sha(name)==digest,'Evidência alterada: '+name)
    s.resolve(seal['videoMediaId'])
    for w in seal['windows']:s.resolve(w['sourceMediaId'])
    return {'mediaId':seal['videoMediaId'],'starts':select(seal['windows'],d['project.json'])}
