"""Job-owned hair settings and an independent, reversible finishing stage."""
import copy
import subprocess
import tempfile
from pathlib import Path

import hair_controls as hc
import hair_finish as hf

VERSION = 'editor-hair-v1'
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = ROOT/'.runtime/hair/venv/bin/python'
CODE = ('hair_controls.py', 'hair_finish.py', 'hair_base.py', 'hair_connector.py')


def code_hashes():
    return {n: hc.sha(ROOT/'scripts'/n) for n in CODE}


def invoke(args, log=None):
    args = list(map(str, args))
    if log:
        with Path(log).open('x') as f:
            import json
            f.write(json.dumps(args, ensure_ascii=False)+'\n'); f.flush()
            result = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
        hc.require(result.returncode == 0, f'Cabelo falhou; consulte {log}')
    else:
        result = subprocess.run(args, capture_output=True, text=True)
        hc.require(result.returncode == 0, 'Validação de cabelo falhou: '+result.stderr[-4000:])


def cache_for(s, d, hair):
    hc.require(hair.get('version') == VERSION, 'Versão de cabelo incompatível')
    asset = hair['cache']; hf.verify_asset(asset); cache = s.read(asset['path'])
    hc.require(cache.get('kind') == 'hair-alpha-cache' and cache.get('schemaVersion') == 1,
               'Cache de cabelo incompatível')
    hc.require(cache['cacheId'] == hc.digest({k: v for k, v in cache.items() if k != 'cacheId'})
               and cache['cacheId'] == asset['cacheId'], 'Manifesto do cache alterado')
    hc.require(cache['binding'] == hc.edit_binding(d['project.json']), 'Cabelo de outro corte; preparar/realinhar cache')
    hc.validate_config(hair['controls'], cache)
    return cache


def request(s, d, hair=None):
    hair = hair or d['finishing.json']['hair']; cache = cache_for(s, d, hair)
    p = d['project.json']; finish = d['finishing.json']
    hc.require(p['fps'] == 60 and all(x['fullSize'][0]*p['height'] == x['fullSize'][1]*p['width']
               for x in cache['scenes']), 'Cache de cabelo não corresponde ao formato do projeto')
    upstream = finish.get('videoMediaId')
    if upstream:
        hc.require(finish.get('videoEditHash') == s.edit_hash(d), 'Base tratada de outro corte')
        hc.require(upstream != hair.get('output', {}).get('mediaId'), 'Não usar cabelo como sua própria base')
    return dict(version=VERSION, binding=hc.edit_binding(p), format=[p['width'], p['height'], p['fps']],
                cache=hair['cache'], controls=hair['controls'], upstreamMediaId=upstream, scripts=code_hashes())


def validate_external(s, job, hair):
    d = s.load(job); request(s, d, hair)
    with tempfile.TemporaryDirectory(prefix='editor-hair-') as tmp:
        tmp = Path(tmp); s.write(tmp/'project.json', d['project.json']); s.write(tmp/'controls.json', hair['controls'])
        invoke([hair['python'], ROOT/'scripts/hair_finish.py', 'validate', '--cache', hair['cache']['path'],
                '--config', tmp/'controls.json', '--project', tmp/'project.json'])


def save(s, job, hair, action):
    d = s.load(job); old = d['finishing.json'].get('hair')
    d['finishing.json']['hair'] = hair
    s.write(s.jobdir(job)/'finishing.json', d['finishing.json'])
    s.log(job, action, previousHair=old, hair=hair)
    return summary(s, d)


def setup(s, job, cache_path, config_path=None, python=DEFAULT_PYTHON):
    cache_path = Path(cache_path).resolve(); cache = s.read(cache_path)
    if config_path:
        controls = s.read(config_path)
    else:
        controls = dict(schemaVersion=1, cacheId=cache['cacheId'],
            defaults=dict(alpha=copy.deepcopy(hc.ALPHA), intensity=1., background={}),
            scenes={sc['id']: dict(intervals=[], bypass=[]) for sc in cache['scenes']})
    # Keep the venv symlink path: resolving it would invoke the global interpreter.
    python = str(Path(python).absolute()); hc.require(Path(python).is_file(), 'Python de cabelo indisponível')
    hair = dict(version=VERSION, enabled=False, python=python,
                cache=dict(path=str(cache_path), sha256=s.sha(cache_path), cacheId=cache['cacheId']), controls=controls)
    before = s.digest(s.load(job))
    validate_external(s, job, hair)
    hc.require(s.digest(s.load(job)) == before, 'Job mudou durante configuração; repetir')
    return save(s, job, hair, 'hair-setup')


def configure(s, job, config_path=None, output=None):
    d = s.load(job); hair = copy.deepcopy(d['finishing.json']['hair'])
    hc.require(bool(config_path) != bool(output), 'Use --config para importar ou --out para exportar')
    if output:
        s.write(output, hair['controls'], True)
        return dict(config=str(Path(output).resolve()), modified=False)
    hair['controls'] = s.read(config_path)
    validate_external(s, job, hair)
    hc.require(s.load(job) == d, 'Job mudou durante configuração; repetir')
    return save(s, job, hair, 'hair-configure')


def disable(s, job):
    hair = copy.deepcopy(s.load(job)['finishing.json']['hair']); hair['enabled'] = False
    return save(s, job, hair, 'hair-disable')


def prepare(s, job, plan_path, work, python=DEFAULT_PYTHON):
    plan_path = Path(plan_path).resolve(); plan = s.read(plan_path); work = s.output_path(work)
    p = Path(plan['project']); p = p if p.is_absolute() else plan_path.parent/p
    hc.require(p.resolve() == (s.jobdir(job)/'project.json').resolve(), 'Plano deve apontar para o projeto deste job')
    d = s.load(job); binding = hc.edit_binding(d['project.json'])
    for scene in binding['scenes']: s.resolve(scene['mediaId'])
    hc.require(not work.exists(), 'Diretório já existe; escolher versão nova')
    work.mkdir(parents=True)
    s.write(work/'project.json', d['project.json'], True)
    # Freeze all input paths against the original plan, but use the project snapshot.
    frozen = copy.deepcopy(plan); frozen['project'] = str(work/'project.json')
    def absolute(value):
        path = Path(value); return str((path if path.is_absolute() else plan_path.parent/path).resolve())
    for key in ('code', 'weights'): frozen['model'][key] = absolute(plan['model'][key])
    for scene in frozen['scenes']:
        for key in ('source', 'seed', 'patchMask'): scene[key] = absolute(scene[key])
        scene['protection'] = [absolute(x) for x in scene.get('protection', [])]
    s.write(work/'plan.json', frozen, True)
    invoke([python, ROOT/'scripts/hair_analyze.py', '--plan', work/'plan.json', '--out', work/'analysis'], work/'analysis.log')
    hc.require(hc.edit_binding(s.load(job)['project.json']) == binding, 'Corte mudou durante análise')
    return setup(s, job, work/'analysis/cache.json', work/'analysis/controls.json', python)


def render(s, job, work, scene=None, frames=None, save_masks=False, quality='preview'):
    d = s.load(job); hair = d['finishing.json']['hair']; req = request(s, d)
    import face_connector
    face_connector.validate_attached(s, d)
    # Also verifies/reconnects originals, independent of cached preview inputs.
    for cut in req['binding']['scenes']: s.resolve(cut['mediaId'])
    base = s.resolve(req['upstreamMediaId']) if req['upstreamMediaId'] else None
    cache = cache_for(s, d, hair)
    hf.selection(cache, scene, frames)
    hc.require(quality in ('preview', 'production'), 'Qualidade inválida')
    if quality == 'production':
        hc.require(all(sc['fullSize'] == req['format'][:2] for sc in cache['scenes']), 'Cache de amostra não serve para produção; preparar resolução definitiva')
    work = s.output_path(work); hc.require(not work.exists(), 'Diretório já existe; escolher versão nova')
    work.mkdir(parents=True)
    s.write(work/'project.json', d['project.json'], True); s.write(work/'controls.json', hair['controls'], True)
    s.write(work/'request.json', req, True)
    args = [hair['python'], ROOT/'scripts/hair_finish.py', 'render', '--cache', hair['cache']['path'],
            '--config', work/'controls.json', '--project', work/'project.json', '--out', work/'render', '--quality', quality]
    if base: args += ['--base-video', base]
    if scene: args += ['--scene', scene]
    if frames: args += ['--frames', frames]
    if save_masks: args += ['--save-masks']
    invoke(args, work/'render.log')
    hc.require(request(s, s.load(job)) == req, 'Corte/base/controles mudaram durante render; não associar')
    stage = dict(version=VERSION, request=req, reportSha256=s.sha(work/'render/report.json'),
                 createdAt=s.now(), attached=False)
    s.write(work/'stage.json', stage, True)
    verify_run(s, d, work, require_full=False)
    s.log(job, 'hair-render', work=str(work), fullCut=scene is None, quality=quality)
    return dict(work=str(work), result=str(work/'render/result-pcm.mov'), report=str(work/'render/report.json'),
                attached=False, visualReview='pending')


def verify_run(s, d, work, require_full=True):
    work = s.output_path(work); stage = s.read(work/'stage.json'); report = s.read(work/'render/report.json')
    req = request(s, d)
    hc.require(stage.get('version') == VERSION and stage['request'] == req, 'Cabelo desatualizado: corte, formato, base, controles ou código mudou')
    hc.require(s.sha(work/'render/report.json') == stage['reportSha256'], 'Relatório de cabelo alterado')
    hc.require(report.get('technicalPass') is True and report.get('pcmBitExact') is True
               and report.get('ptsVerified') is True and report.get('sourceAlphaUnchanged') is True, 'Verificação técnica de cabelo incompleta')
    hc.require(report['binding'] == req['binding'] and report['cacheId'] == req['cache']['cacheId'], 'Relatório de outra análise/corte')
    hc.require(s.read(work/'render/config.json') == req['controls'] and
               s.sha(work/'render/config.json') == report['configSha256'], 'Controles renderizados divergentes')
    hc.require(all(report['scripts'].get(n) == h for n, h in req['scripts'].items() if n != 'hair_connector.py'), 'Código do render mudou')
    if req['upstreamMediaId']:
        hc.require(report.get('upstream', {}).get('sha256') == req['upstreamMediaId'][2:], 'Base tratada não foi composta no cabelo')
    else: hc.require(report.get('upstream') is None, 'Base não solicitada no resultado de cabelo')
    if require_full:
        expected = [dict(scene=c['id'], start=0, end=c['frames']) for c in req['binding']['scenes']]
        hc.require(report.get('fullCut') is True and report['selection'] == expected and
                   report['frames'] == sum(c['frames'] for c in req['binding']['scenes']), 'Resultado parcial não pode substituir a timeline')
    hc.require(report['fps'] == 60 and report['quality'] in ('preview', 'production'), 'Formato de saída incompatível')
    result = work/'render/result-pcm.mov'
    asset = next(x for x in report['outputs'] if x['file'] == result.name)
    hc.require(s.sha(result) == asset['sha256'] and asset['frames'] == report['frames']
               and asset['size'] == report['size'], 'Resultado de cabelo alterado')
    cache = cache_for(s, d, d['finishing.json']['hair'])
    hc.require(report['size'] == cache['scenes'][0]['fullSize'], 'Tamanho do resultado diverge do cache')
    if report['quality'] == 'production':
        hc.require(report.get('productionIntermediate') is True and report['size'] == req['format'][:2], 'Base definitiva exige resolução do projeto')
    return stage, report, result


def attach(s, job, work):
    work = s.persistent_path(work)
    d = s.load(job); stage, report, result = verify_run(s, d, work)
    import face_connector
    face_connector.validate_attached(s, d)
    if stage['request']['upstreamMediaId']: s.resolve(stage['request']['upstreamMediaId'])
    # Full decode and cache verification were done at render; hash binds those exact bytes.
    mid = s.register(result, 'video')
    hair = copy.deepcopy(d['finishing.json']['hair']); hair['enabled'] = True
    hair['output'] = dict(mediaId=mid, work=str(Path(work).resolve()), stageSha256=s.sha(Path(work)/'stage.json'),
                          quality=report['quality'])
    hc.require(s.load(job) == d, 'Job mudou durante associação; repetir')
    return save(s, job, hair, 'hair-attach')


def validate_attached(s, d, master=False):
    hair = d['finishing.json'].get('hair')
    if not hair or not hair.get('enabled'): return None
    hc.require(type(hair['enabled']) is bool, 'enabled de cabelo inválido')
    output = hair.get('output'); hc.require(output, 'Cabelo ativo sem resultado; renderizar/associar ou desativar')
    work = Path(output['work'])
    hc.require(s.sha(work/'stage.json') == output['stageSha256'], 'Registro de cabelo alterado')
    stage, report, path = verify_run(s, d, work)
    hc.require('m-'+s.sha(path) == output['mediaId'], 'ID do cabelo não corresponde à saída')
    s.resolve(output['mediaId'])
    if master:
        hc.require(report['quality'] == 'production' and report['size'] == stage['request']['format'][:2],
                   'Cabelo de amostra bloqueado no master; renderizar base definitiva')
    return output['mediaId']


def summary(s, d):
    hair = d['finishing.json'].get('hair')
    if not hair: return dict(state='not-configured', enabled=False)
    result = dict(enabled=bool(hair.get('enabled')), cacheId=hair['cache']['cacheId'],
                  controlsSha256=hc.digest(hair['controls']), output=hair.get('output'))
    try:
        request(s, d)
        if hair.get('output'):
            # Also inspect disabled outputs so stale state is visible before reattaching.
            probe = copy.deepcopy(d); probe['finishing.json']['hair']['enabled'] = True
            validate_attached(s, probe)
            result['state'] = 'active-'+hair['output']['quality'] if hair.get('enabled') else 'disabled'
        else: result['state'] = 'needs-render' if hair.get('enabled') else 'configured'
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        result.update(state='stale', reason=str(error))
    return result
