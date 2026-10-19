"""Resumable provenance across preparation, Premiere handoff and exact-file release."""
from pathlib import Path
import shutil
import uuid
import studio as s

TRANSFER_CHECKS = ('geometry', 'captions', 'avLinks', 'headHandles', 'tailHandles', 'saveReopen', 'mixLimiter')
FINAL_CHECKS = ('visual', 'audio', 'completePlayback', 'noGuides', 'mixLimiter')


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': s.sha(path)}


def verify_identity(record):
    if s.sha(record['path']) != record['sha256']:
        raise ValueError('Arquivo alterado: ' + record['path'])


def require_review(evidence, checks):
    if not evidence.get('userApproval') or not evidence.get('reviewer') or not evidence.get('notes'):
        raise ValueError('Decisão real, responsável e notas são obrigatórios')
    if any(evidence.get('checks', {}).get(k) != 'passed' for k in checks):
        raise ValueError('Conferência incompleta: ' + ', '.join(checks))


def record_handoff(job, project, sequence_id, package, evidence):
    e = s.read(evidence)
    require_review(e, TRANSFER_CHECKS)
    package_id = identity(package)
    project_id = identity(project)
    if e.get('packageSha256') != package_id['sha256'] or e.get('projectSha256') != project_id['sha256'] or e.get('sequenceId') != sequence_id:
        raise ValueError('Evidência não corresponde à transferência exata')
    r = {'schemaVersion': 1, 'at': s.now(), 'job': job, 'authority': 'premiere',
         'project': project_id, 'sequenceId': sequence_id, 'package': package_id,
         'evidence': identity(evidence), 'preparationFingerprint': s.digest(s.load(job))}
    dest = s.jobdir(job) / 'handoffs' / (uuid.uuid4().hex + '.json')
    s.write(dest, r, True)
    s.log(job, 'premiere-handoff', record=str(dest))
    return {'record': str(dest), **r}


def resume(job):
    """Read-only, no media probing/copying and no inferred approvals for legacy jobs."""
    home = s.jobhome(job)
    records = []
    for path in (s.jobdir(job) / 'handoffs').glob('*.json'):
        r = s.read(path)
        problems = []
        for k in ('package', 'evidence'):
            try:
                verify_identity(r[k])
            except (OSError, ValueError) as exc:
                problems.append(str(exc))
        project = Path(r['project']['path'])
        # Changes in Premiere are normal after handoff; they do not resurrect a JSON timeline.
        state = 'offline' if not project.is_file() else ('unchanged' if s.sha(project) == r['project']['sha256'] else 'edited-since-handoff')
        records.append({**r, 'record': str(path), 'integrityErrors': problems, 'projectState': state})
    records.sort(key=lambda r: r['at'])
    recent = [s.read(p) for p in sorted((s.jobdir(job)/'history').glob('*.json'))[-12:]]
    legacy = [str(p) for p in sorted((home/'interchange').glob('*/report.json'))]
    candidates = [str(p) for p in sorted((s.jobdir(job)/'premiere-candidates').glob('*.json'))]
    return {'schemaVersion': 1, 'job': job,
            'authority': 'premiere' if records else 'preparation-or-unregistered-handoff',
            'activeHandoff': records[-1] if records else None,
            'preparationFingerprint': s.digest(s.load(job)), 'recentHistory': recent,
            'legacyTransferReports': legacy, 'masterCandidates': candidates,
            'next': 'review-current-Premiere-and-exact-export' if records else 'inspect-existing-evidence-before-editing',
            'warning': 'Legacy reports are evidence to inspect; their presence never grants approval.'}


def register_candidate(job, master, project, sequence_id, dependencies, evidence):
    """Separate external provenance; never uses renderer fingerprints or its release gate."""
    e = s.read(evidence)
    if not e.get('exportedByPremiere') or not e.get('exportReceipt'):
        raise ValueError('Identificar evidência da exportação real pelo Premiere')
    master_id, project_id = identity(master), identity(project)
    if e.get('outputSha256') != master_id['sha256'] or e.get('projectSha256') != project_id['sha256'] or e.get('sequenceId') != sequence_id:
        raise ValueError('Procedência não corresponde ao arquivo/projeto/sequência')
    if not isinstance(e.get('durationFrames'), int) or e['durationFrames'] <= 0:
        raise ValueError('Duração da sequência em frames obrigatória')
    state = resume(job)
    handoff = state['activeHandoff']
    if not handoff or handoff['integrityErrors'] or handoff['sequenceId'] != sequence_id or handoff['project']['path'] != project_id['path']:
        raise ValueError('Transferência verificada correspondente é obrigatória')
    dep = s.read(dependencies)
    if not dep.get('files'):
        raise ValueError('Inventário de dependências vazio')
    for item in dep['files']:
        verify_identity(item)
    verification = s.vh.verify(master, {'durationInFrames': e['durationFrames'], 'fps': 60}, True)
    # Refuse races while probing/decoding.
    verify_identity(master_id)
    verify_identity(project_id)
    if not sequence_id.strip():raise ValueError('Sequence identity required')
    r = {'schemaVersion': 1, 'producer': 'premiere', 'job': job, 'at': s.now(),
         'output': master_id, 'project': project_id, 'sequenceId': sequence_id,
         'durationFrames': e['durationFrames'], 'dependencies': identity(dependencies),
         'exportEvidence': identity(evidence), 'handoff': identity(handoff['record']),
         'verification': verification, 'released': False}
    if not verification['technical_pass']:
        raise ValueError('Master reprovado: ' + '; '.join(verification['errors']))
    dest = s.jobdir(job)/'premiere-candidates'/(master_id['sha256']+'.json')
    s.write(dest, r, True)
    s.log(job, 'premiere-candidate', record=str(dest))
    return {'record': str(dest), **r}


def release_candidate(job, candidate, evidence):
    r, e = s.read(candidate), s.read(evidence)
    if r.get('producer') != 'premiere' or r.get('job') != job or not r['verification']['technical_pass']:
        raise ValueError('Candidato inválido')
    require_review(e, FINAL_CHECKS)
    if e.get('outputSha256') != r['output']['sha256'] or e.get('candidateSha256') != s.sha(candidate):
        raise ValueError('Aprovação é de outro arquivo/candidato')
    for key in ('output', 'project', 'dependencies', 'exportEvidence', 'handoff'):
        verify_identity(r[key])
    handoff = s.read(r['handoff']['path'])
    for key in ('package', 'evidence'):
        verify_identity(handoff[key])
    for item in s.read(r['dependencies']['path'])['files']:
        verify_identity(item)
    if not s.vh.verify(r['output']['path'], {'durationInFrames': r['durationFrames'], 'fps': 60}, True)['technical_pass']:
        raise ValueError('Falha técnica ao liberar')
    source = Path(r['output']['path'])
    dest = s.paths()['ready']/s.safe_id(job)/('premiere-'+r['output']['sha256'])/source.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        verify_identity({'path': str(dest), 'sha256': r['output']['sha256']})
    else:
        temp = dest.with_name('.'+dest.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            shutil.copy2(source, temp)
            verify_identity({'path': str(temp), 'sha256': r['output']['sha256']})
            # Publish without overwriting an existing file.
            import os
            os.link(temp, dest)
        finally:
            temp.unlink(missing_ok=True)
    result = {'at': s.now(), 'producer': 'premiere', 'output': identity(dest),
              'candidate': identity(candidate), 'evidence': identity(evidence), 'reviewer': e['reviewer']}
    s.write(s.jobdir(job)/'releases'/('premiere-'+r['output']['sha256']+'.json'), result, True)
    s.log(job, 'premiere-release', **result)
    return result


def final_gate(job):
    """Validate an already approved external release; never create approval here."""
    releases=[]
    for p in (s.jobdir(job)/'releases').glob('premiere-*.json'):
        r=s.read(p);releases.append((r['at'],p,r))
    if not releases:raise ValueError('Master do Premiere ainda sem liberação do arquivo exato')
    _,path,r=max(releases,key=lambda item:item[0])
    for key in ('output','candidate','evidence'):verify_identity(r[key])
    candidate=s.read(r['candidate']['path']);e=s.read(r['evidence']['path'])
    require_review(e,FINAL_CHECKS)
    if candidate.get('job')!=job or candidate.get('producer')!='premiere' or e.get('outputSha256')!=r['output']['sha256'] or e.get('candidateSha256')!=r['candidate']['sha256']:
        raise ValueError('Liberação não corresponde ao candidato/arquivo')
    for key in ('output','project','dependencies','exportEvidence','handoff'):verify_identity(candidate[key])
    for item in s.read(candidate['dependencies']['path'])['files']:verify_identity(item)
    for key in ('package','evidence'):verify_identity(s.read(candidate['handoff']['path'])[key])
    return {'job':job,'authority':'premiere','ready':True,'release':str(path),'output':r['output']}
