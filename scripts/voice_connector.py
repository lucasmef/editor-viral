"""Offline approved voice finishing. Processing is not perceptual approval."""
import copy
import json
import os
import subprocess
import time
import uuid
import wave
from pathlib import Path

KIND = 'editor-voice-neural-v1'
RATE = 48000


def defaults(host):
    path = host.ROOT / 'studio/default-voice.json'
    return copy.deepcopy(host.read(path)) if path.exists() else None


def enabled(d):
    return d['finishing.json'].get('voiceNeural', {}).get('enabled') is True


def bundle(host, profile):
    root = (host.ROOT / profile['bundle']).resolve()
    if host.sha(root / 'FILES.sha256.json') != profile['manifestSha256']:
        raise ValueError('Manifesto do Voz Neural alterado')
    if host.sha(root / 'approval.json') != profile['approvalSha256']:
        raise ValueError('Aprovação do Voz Neural alterada')
    approval = host.read(root / 'approval.json')
    if (approval['status'] != 'approved' or approval['version'] != profile['version']
            or approval['fingerprint'] != profile['approvalFingerprint']):
        raise ValueError('Versão de voz sem aprovação correspondente')
    manifest = host.read(root / 'FILES.sha256.json')
    for rel, expected in manifest['files'].items():
        path = root / rel
        if not path.resolve().is_relative_to(root) or host.sha(path) != expected:
            raise ValueError('Pacote Voz Neural alterado: ' + rel)
    for rel, target in manifest['symlinks'].items():
        path = root / rel
        if not path.is_symlink() or str(path.readlink()) != target or not path.resolve().is_relative_to(root):
            raise ValueError('Link do Voz Neural alterado: ' + rel)
    return root


def binding(host, d):
    return {'editHash': host.edit_hash(d), 'profile': d['finishing.json']['voiceNeural'],
            'adapterSha256': host.sha(Path(__file__))}


def summary(host, d, stages=None):
    if not enabled(d):
        return {'state': 'disabled'}
    c = d['finishing.json'].get('audioConnector')
    state = 'needs-processing'
    if c:
        state = 'ready' if c.get('binding') == binding(host, d) else 'stale'
    if stages and stages.get('preproduction') != 'approved':
        state = 'waiting-for-cut-approval'
    return {'state': state, 'version': d['finishing.json']['voiceNeural']['version'],
            'perceptualReview': 'separate-postproduction-checkpoint'}


def validate_attached(host, d, required=False):
    finish = d['finishing.json']
    c = finish.get('audioConnector')
    if not c:
        if required and enabled(d):
            raise ValueError('Voz Neural pendente: gere uma prévia ou use voice-process antes de revisar o áudio')
        return
    if c.get('kind') != KIND or not enabled(d) or c.get('binding') != binding(host, d):
        raise ValueError('Voz Neural pertence a outro corte, preset ou adaptador; reprocesse')
    if finish.get('audioGainDb') != 0:
        raise ValueError('Voz Neural exige ganho adicional zero para evitar ganho duplicado')
    if finish.get('audioEditHash') != host.edit_hash(d):
        raise ValueError('Voz Neural pertence a outro corte; reprocesse')
    report_path = host.ROOT / c['report']
    if host.sha(report_path) != c['reportSha256']:
        raise ValueError('Relatório de voz alterado')
    report = host.read(report_path)
    if report['binding'] != c['binding'] or report['outputSha256'] != finish.get('audioMediaId', '')[2:]:
        raise ValueError('Vínculo do áudio tratado inválido')
    path = host.resolve(finish['audioMediaId'])
    verify_wav(path, sample_count(d))
    bundle(host, finish['voiceNeural'])


def sample_count(d):
    fps = d['project.json']['fps']
    if type(fps) is not int or fps <= 0:
        raise ValueError('FPS inválido')
    total = 0
    for scene in d['project.json']['scenes']:
        for frames in (scene['clip']['inFrame'], scene['duration']):
            if frames * RATE % fps:
                raise ValueError('Limite de corte não representável em amostras de 48 kHz')
        total += scene['duration'] * RATE // fps
    if total <= 0:
        raise ValueError('Corte vazio')
    return total


def verify_wav(path, expected):
    with wave.open(str(path), 'rb') as f:
        if (f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()) != (RATE, 2, 3, expected):
            raise ValueError('Voz Neural: duração/taxa/canais/bits incompatíveis')
        data = f.readframes(expected)
        if any(data[k::6] != data[k+3::6] for k in range(3)):
            raise ValueError('Voz Neural não é dual-mono')


def run(command, work, name, env=None):
    p = subprocess.run(list(map(str, command)), capture_output=True, env=env)
    (work / (name + '.stdout.log')).write_bytes(p.stdout)
    (work / (name + '.stderr.log')).write_bytes(p.stderr)
    if p.returncode:
        raise ValueError(f'Falha no processamento de voz ({name}); consulte {work}')
    return p


def probe(host, path):
    exe = Path(host.vh.binary('ffprobe'))
    env = dict(os.environ)
    if (exe.parent / 'libavdevice.dylib').exists():
        env['DYLD_LIBRARY_PATH'] = str(exe.parent)
    p = subprocess.run([str(exe), '-v', 'error', '-show_streams', '-of', 'json', str(path)],
                       env=env, capture_output=True, check=True)
    return json.loads(p.stdout)


def extract(host, d, work):
    """Sample-exact full cut from verified originals, arithmetic channel mean, no gain."""
    expected = sample_count(d)
    fps = d['project.json']['fps']
    sources = {}
    segments = []
    output = work / 'input.wav'
    with wave.open(str(output), 'wb') as dest:
        dest.setnchannels(2); dest.setsampwidth(3); dest.setframerate(RATE)
        cursor = 0
        for i, scene in enumerate(d['project.json']['scenes']):
            mid = scene['clip']['mediaId']
            if mid not in sources:
                p = host.resolve(mid)  # Never fall back to a proxy or processed base.
                meta = probe(host, p)
                audios = [s for s in meta['streams'] if s['codec_type'] == 'audio']
                videos = [s for s in meta['streams'] if s['codec_type'] == 'video']
                if not audios:
                    raise ValueError('Original sem áudio: ' + str(p))
                a = audios[0]
                at = float(a.get('start_time', 0))
                vt = float(videos[0].get('start_time', 0)) if videos else 0
                if abs(at-vt) > 1/RATE or abs(vt) > 1/RATE:
                    raise ValueError('Timestamps não zero/desalinhados; reconformação explícita necessária')
                channels = a['channels']
                if not 1 <= channels <= 8:
                    raise ValueError('Layout de canais não suportado')
                sources[mid] = {'path': str(p), 'sha256': host.registry()['media'][mid]['sha256'],
                                'audioStream': a, 'channels': channels}
            src = sources[mid]
            start = scene['clip']['inFrame'] * RATE // fps
            count = scene['duration'] * RATE // fps
            mean = '+'.join(f'{1/src["channels"]:.17g}*c{k}' for k in range(src['channels']))
            filters = f'aresample={RATE},atrim=start_sample={start}:end_sample={start+count},asetpts=PTS-STARTPTS,pan=stereo|c0={mean}|c1={mean}'
            part = work / f'scene-{i:04d}.wav'
            command = [host.vh.binary('ffmpeg'), '-v', 'error', '-n', '-i', src['path'], '-map', '0:a:0',
                       '-af', filters, '-c:a', 'pcm_s24le', str(part)]
            run(command, work, f'extract-{i:04d}')
            verify_wav(part, count)
            with wave.open(str(part), 'rb') as f:
                dest.writeframes(f.readframes(count))
            segments.append({'scene': scene['id'], 'mediaId': mid, 'sourceStartSample': start,
                             'outputStartSample': cursor, 'sampleCount': count, 'command': list(map(str, command))})
            cursor += count
    verify_wav(output, expected)
    return output, sources, segments


def process(host, job):
    d = host.load(job)
    if not enabled(d):
        raise ValueError('Voz Neural não habilitada neste job; use voice-process --enable para adoção explícita')
    if host.status(job)['checkpoints']['preproduction'] != 'approved':
        raise ValueError('Aprovação do corte inicial pendente; voz automática aguarda preproduction')
    errors = host.validate_job(d)
    if errors:
        raise ValueError('; '.join(errors))
    finish = d['finishing.json']
    if finish.get('audioMediaId') and not finish.get('audioConnector'):
        raise ValueError('Há áudio manual; não será substituído automaticamente')
    frozen = bundle(host, finish['voiceNeural'])
    key = binding(host, d)
    connector = finish.get('audioConnector')
    if connector and connector.get('binding') == key:
        validate_attached(host, d, required=True)
        return {'state': 'reused', 'mediaId': finish['audioMediaId'], 'report': connector['report']}
    work = host.jobhome(job) / 'audio' / (host.now().replace(':', '-') + '-' + uuid.uuid4().hex[:8])
    work.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    source, originals, segments = extract(host, d, work)
    output = work / 'voice.wav'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONHOME', None); env.pop('PYTHONPATH', None)
    command = [frozen / 'python/bin/python3.12', frozen / 'processor/independent_voice_runner.py', source, output]
    neural_started = time.perf_counter()
    run(command, work, 'runner', env)
    neural_seconds = time.perf_counter() - neural_started
    verify_wav(output, sample_count(d))
    diagnostics = host.read(output.with_suffix('.json'))
    if diagnostics['settings'] != host.read(frozen / 'preset.json'):
        raise ValueError('Runner divergiu do preset aprovado')
    measurement = run([host.vh.binary('ffmpeg'), '-hide_banner', '-i', output, '-af',
                       'loudnorm=I=-23:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'], work, 'measurement')
    text = measurement.stderr.decode()
    measured = json.loads(text[text.rfind('{'):text.rfind('}')+1])
    levels = {k: measured[k] for k in ('input_i', 'input_tp', 'input_lra', 'input_thresh')}
    # Validate dependencies/input identity again before changing any editable job document.
    bundle(host, finish['voiceNeural'])
    for mid, info in originals.items():
        if host.sha(Path(info['path'])) != info['sha256']:
            raise ValueError('Original mudou durante processamento de voz: ' + mid)
    current = host.load(job)
    if binding(host, current) != key or current['finishing.json'] != finish:
        raise ValueError('Job mudou durante processamento; saída preservada, associação recusada')
    report = {'kind': KIND, 'binding': key, 'originals': originals, 'segments': segments,
              'inputSha256': host.sha(source), 'outputSha256': host.sha(output),
              'output': str(output), 'sampleRate': RATE, 'channels': 2, 'bits': 24,
              'sampleCount': sample_count(d), 'neuralSeconds': neural_seconds,
              'totalSeconds': time.perf_counter()-started, 'command': list(map(str, command)),
              'metrics': levels, 'diagnosticsSha256': host.sha(output.with_suffix('.json')),
              'gainAppliedBeforeRunnerDb': 0, 'perceptualReview': 'pending'}
    report_path = work / 'report.json'
    host.write(report_path, report, True)
    host.attach_finish(job, 'audio', output, 'Voz Neural '+finish['voiceNeural']['version']+'; '+str(report_path), automatic=True)
    updated = host.load(job)['finishing.json']
    updated['audioConnector'] = {'kind': KIND, 'binding': key, 'report': str(report_path),
                                 'reportSha256': host.sha(report_path)}
    host.write(host.jobdir(job)/'finishing.json', updated)
    host.log(job, 'voice-processed', version=finish['voiceNeural']['version'], report=str(report_path), editHash=key['editHash'])
    return {'state': 'processed', 'output': str(output), 'report': str(report_path), 'review': 'pending'}


def prepare(host, job, master=False):
    d = host.load(job)
    if not enabled(d):
        return d
    if master:
        validate_attached(host, d, required=True)
        return d
    if host.status(job)['checkpoints']['preproduction'] != 'approved':
        # A recut awaiting review must not play audio from the old montage.
        c = d['finishing.json'].get('audioConnector')
        if c and c.get('binding') != binding(host, d):
            d = copy.deepcopy(d)
            for k in ('audioMediaId', 'audioEditHash', 'audioNotes', 'audioConnector'):
                d['finishing.json'].pop(k, None)
            d['finishing.json']['audioGainDb'] = 0
        return d
    process(host, job)
    return host.load(job)


def enable(host, job):
    d = host.load(job)
    if d['finishing.json'].get('audioMediaId'):
        raise ValueError('Job já possui áudio; preserve/revise essa ligação antes de habilitar voz automática')
    profile = defaults(host)
    if not profile:
        raise ValueError('Preset padrão não configurado')
    bundle(host, profile)
    d['finishing.json']['voiceNeural'] = profile
    host.write(host.jobdir(job)/'finishing.json', d['finishing.json'])
    host.log(job, 'voice-enabled', version=profile['version'])
