"""Local Rosto Natural Metal connector. No creative approvals; no CPU fallback.

The host studio object is injected so integration fixtures never touch real jobs.
"""
import json
import subprocess
import uuid
from fractions import Fraction
from pathlib import Path

DEFAULT_ENGINE = Path('/Users/lucas/Documents/Codex/rosto-natural')
VERSION = 'editor-face-metal-v1'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def invoke(args, log):
    """Argument vector only; persist both success and failure diagnostics."""
    with Path(log).open('x') as out:
        out.write(json.dumps([str(a) for a in args], ensure_ascii=False) + '\n')
        out.flush()
        result = subprocess.run([str(a) for a in args], stdout=out, stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'Processador falhou ({result.returncode}); consulte {log}')


def engine_paths(root):
    root = Path(root).resolve()
    home = root / 'integrations/editor-metal-v1'
    paths = {'python': root / '.venv/bin/python', 'runner': home / 'runner.py',
             'ffmpeg': root / '.local/bin/ffmpeg', 'backend': home / 'backend.py',
             'shader': home / 'F5.metal', 'library': home / 'build/libRostoMetalF5.dylib',
             'preset': home / 'preset-F5-v004.json'}
    require(all(p.is_file() for p in paths.values()), 'Instalação Metal incompleta: ' + str(root))
    return paths


def binding(s, job):
    d = s.load(job)
    errors = s.validate_job(d)
    require(not errors, '; '.join(errors))
    p = d['project.json']
    require(p['fps'] == 60, 'Conector exige projeto a 60 fps')
    require(all(16 <= p[k] <= 4096 and p[k] % 2 == 0 for k in ('width', 'height')), 'Dimensões não suportadas')
    cursor = 0
    segments = []
    for scene in p['scenes']:
        clip = scene['clip']
        source = s.resolve(clip['mediaId'])  # Always original, never proxy/previous finish.
        segments.append({'scene': scene['id'], 'mediaId': clip['mediaId'],
                         'sourceSha256': s.sha(source), 'inFrame': clip['inFrame'],
                         'duration': scene['duration'], 'from': cursor})
        cursor += scene['duration']
    return {'editorRoot': str(s.ROOT.resolve()), 'job': job, 'editHash': s.edit_hash(d),
            'width': p['width'], 'height': p['height'], 'fps': 60,
            'frames': cursor, 'segments': segments}


def current(s, job, work):
    work = s.output_path(work)
    m = s.read(work / 'base.json')
    require(m['version'] == VERSION, 'Versão de conector incompatível')
    require(m['binding'] == binding(s, job), 'Fonte/corte/formato mudou; prepare nova base e revisão')
    require(m['connectorSha256'] == s.sha(__file__), 'Conector mudou; prepare nova base')
    require(s.sha(work / 'base.mov') == m['baseSha256'], 'Base alterada')
    ep = engine_paths(m['engineRoot'])
    require(m['engineHashes'] == {k: s.sha(v) for k, v in ep.items()}, 'Motor mudou; prepare nova análise/base')
    return m, ep


def inspect(s, path, b, ffmpeg, pcm_format=None):
    """Independent verification, including exact CFR PTS and decoded PCM size/hash."""
    info = s.vh.probe(path)
    videos = [v for v in info['streams'] if v['codec_type'] == 'video']
    audios = [v for v in info['streams'] if v['codec_type'] == 'audio']
    require(len(videos) == len(audios) == 1, 'Exige exatamente um vídeo e um áudio')
    v, a = videos[0], audios[0]
    require(v['codec_name'] == 'prores' and str(v['profile']) in ('Standard', '2'), 'Exige ProRes 422 Standard')
    for k, val in {'width': b['width'], 'height': b['height'], 'pix_fmt': 'yuv422p10le',
                   'color_space': 'bt709', 'color_transfer': 'bt709', 'color_primaries': 'bt709'}.items():
        require(v.get(k) == val, 'Vídeo incompatível: ' + k)
    require(all(Fraction(v[k]) == 60 for k in ('r_frame_rate', 'avg_frame_rate')), 'FPS incompatível')
    require(a['codec_name'] in ('pcm_f32le', 'pcm_s16le', 'pcm_s24le') and
            a['sample_rate'] == '48000' and a['channels'] == 2, 'PCM estéreo 48kHz obrigatório')
    if pcm_format:
        require(a['codec_name'] == pcm_format, 'Formato PCM alterado')
    # Decode every frame. No -r/fps filter: timestamp defects must remain visible.
    result = subprocess.run([str(ffmpeg), '-v', 'error', '-xerror', '-i', str(path),
                             '-map', '0:v:0', '-fps_mode', 'passthrough', '-f', 'framemd5', '-'],
                            capture_output=True, text=True, check=True)
    lines = result.stdout.splitlines()
    tb = Fraction(next(x.split(':', 1)[1].strip() for x in lines if x.startswith('#tb 0:')))
    frames = [x.split(',') for x in lines if x and not x.startswith('#')]
    require(len(frames) == b['frames'], 'Contagem de frames divergente')
    require(all(Fraction(int(x[2])) * tb == Fraction(i, 60) and
                Fraction(int(x[3])) * tb == Fraction(1, 60) for i, x in enumerate(frames)), 'PTS/duração divergente')
    import hashlib
    h = hashlib.sha256()
    process = subprocess.Popen([str(ffmpeg), '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                '-c:a', 'pcm_f32le', '-f', 'f32le', '-'], stdout=subprocess.PIPE)
    size = 0
    for chunk in iter(lambda: process.stdout.read(8 * 1024 * 1024), b''):
        h.update(chunk); size += len(chunk)
    process.stdout.close()
    require(process.wait() == 0, 'Falha ao decodificar áudio')
    require(size == b['frames'] * 800 * 8, 'Contagem PCM divergente')
    return {'metadata': info, 'frames': len(frames), 'pcm': {'sha256': h.hexdigest(), 'bytes': size,
            'samplesPerChannel': size // 8}, 'audioCodec': a['codec_name'], 'allFramesDecoded': True}


def base(s, job, work, engine=DEFAULT_ENGINE):
    b = binding(s, job)
    work = s.output_path(work)
    require(not work.exists(), 'Diretório de trabalho já existe; escolha uma versão nova')
    ep = engine_paths(engine)
    # Reject unsupported implicit color conversions instead of relabeling HDR.
    for seg in b['segments']:
        info = s.vh.probe(s.resolve(seg['mediaId']))
        v = next(v for v in info['streams'] if v['codec_type'] == 'video')
        require(all(v.get(k) == 'bt709' for k in ('color_space', 'color_transfer', 'color_primaries')), 'Fonte precisa ser Rec.709 explícita')
        require(any(a['codec_type'] == 'audio' for a in info['streams']), 'Fonte sem áudio')
        require((seg['inFrame'] + seg['duration']) / 60 <= float(info['format']['duration']) + 1e-6, 'Corte ultrapassa fonte')
    work.mkdir(parents=True)
    cmd = [ep['ffmpeg'], '-n', '-v', 'error']
    filters = []
    for i, seg in enumerate(b['segments']):
        cmd += ['-ss', format(seg['inFrame'] / 60, '.12f'), '-i', s.resolve(seg['mediaId'])]
        filters += [f"[{i}:v:0]fps=60,trim=end_frame={seg['duration']},setpts=N/(60*TB),"
                    f"scale={b['width']}:{b['height']}:force_original_aspect_ratio=decrease:flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv,"
                    f"pad={b['width']}:{b['height']}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv422p10le,setfield=prog,"
                    f"setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v{i}]",
                    f"[{i}:a:0]asetpts=PTS-STARTPTS,aformat=sample_fmts=flt:sample_rates=48000:channel_layouts=stereo,"
                    f"atrim=end_sample={seg['duration'] * 800},asetpts=N/SR/TB[a{i}]"]
    filters += [''.join(f'[v{i}][a{i}]' for i in range(len(b['segments']))) +
                f"concat=n={len(b['segments'])}:v=1:a=1[vc][a];[vc]settb=1/60000,setpts=N*1000[v]"]
    cmd += ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
            '-r', '60', '-fps_mode', 'cfr', '-video_track_timescale', '60000',
            '-c:v', 'prores_ks', '-profile:v', '2', '-pix_fmt', 'yuv422p10le',
            '-color_range', 'tv', '-colorspace', 'bt709', '-color_trc', 'bt709',
            '-color_primaries', 'bt709', '-movflags', '+write_colr', '-c:a', 'pcm_f32le',
            '-ar', '48000', '-ac', '2', '-threads', '2', work / 'base.mov']
    invoke(cmd, work / 'base.log')
    require(binding(s, job) == b, 'Fonte/corte mudou durante preparação')
    verification = inspect(s, work / 'base.mov', b, ep['ffmpeg'], 'pcm_f32le')
    m = {'version': VERSION, 'binding': b, 'baseSha256': s.sha(work / 'base.mov'),
         'engineRoot': str(Path(engine).resolve()), 'engineHashes': {k: s.sha(v) for k, v in ep.items()},
         'connectorSha256': s.sha(__file__), 'verification': verification,
         'command': list(map(str, cmd)), 'audioPolicy': 'Original cut audio, PCM float32; no gain or treated voice; overlays excluded'}
    s.write(work / 'base.json', m, True)
    template = {'sourceSha256': m['baseSha256'], **{k: b[k] for k in ('width', 'height', 'frames', 'fps')},
                'cuts': [seg['from'] for seg in b['segments']], 'reviewed': False,
                'reviewNotes': '', 'fadeFrames': 12, 'spatialFeatherPx': 50,
                'rectangles': [], 'fullBypassIntervals': [], 'reviewedHandOverrides': []}
    s.write(work / 'review-template.json', template, True)
    return {'base': str(work / 'base.mov'), 'reviewTemplate': str(work / 'review-template.json'), 'attached': False}


def prepare(s, job, work, review):
    work = s.output_path(work); m, ep = current(s, job, work)
    require(not (work / 'analysis').exists() and not (work / 'prepared.json').exists(), 'Análise já existe')
    c = s.read(review); b = m['binding']
    require(c.get('sourceSha256') == m['baseSha256'] and all(c.get(k) == b[k] for k in ('width', 'height', 'frames', 'fps')), 'Revisão de outra base')
    require(c.get('reviewed') is True and bool(c.get('reviewNotes', '').strip()), 'Revisão real de oclusões pendente; Hands não detecta pompom')
    require(set(seg['from'] for seg in b['segments']).issubset(c.get('cuts', [])), 'Revisão omite corte da montagem')
    s.write(work / 'review-input.json', c, True)
    invoke([ep['python'], ep['runner'], 'prepare', '--input', work / 'base.mov',
            '--review', work / 'review-input.json', '--work', work / 'analysis'], work / 'prepare.log')
    current(s, job, work)
    a = s.read(work / 'analysis/analysis.json')
    require(a['sourceSha256'] == m['baseSha256'] and a['analysisMode'] == 'mediapipe-0.10.21-cut-reset', 'Análise inesperada ou cache reutilizado')
    require(s.read(work / 'analysis/review.json') == c, 'Revisão mudou durante análise')
    s.write(work / 'prepared.json', {'baseManifestSha256': s.sha(work / 'base.json'),
            'analysisSha256': s.sha(work / 'analysis/analysis.json')}, True)
    return {'analysis': str(work / 'analysis'), 'attached': False}


def analysis_current(s, job, work):
    m, ep = current(s, job, work); prepared = s.read(work / 'prepared.json')
    require(prepared['baseManifestSha256'] == s.sha(work / 'base.json'), 'Manifesto da base alterado')
    require(prepared['analysisSha256'] == s.sha(work / 'analysis/analysis.json'), 'Manifesto de análise alterado')
    a = s.read(work / 'analysis/analysis.json')
    for name, h in a['files'].items():
        require(Path(name).name == name and s.sha(work / 'analysis' / name) == h, 'Cache adulterado: ' + name)
    return m, ep, a


def verified_report(s, job, work, compare_cpu=False):
    work = s.output_path(work); m, ep, a = analysis_current(s, job, work)
    out = work / 'treated.mov'; r = s.read(work / 'treated.report.json'); b = m['binding']
    require(r['version'] == 'editor-metal-F5-v1' and r['backend'] == 'metal' and r['device'] not in ('', 'CPU'), 'Backend Metal real não comprovado')
    for field, path in [('sourceSha256', work / 'base.mov'), ('outputSha256', out),
                        ('analysisSha256', work / 'analysis/analysis.json'), ('reviewSha256', work / 'analysis/review.json'),
                        ('presetSha256', work / 'analysis/preset.json'), ('librarySha256', ep['library']), ('shaderSha256', ep['shader'])]:
        require(r[field] == s.sha(path), 'Relatório/hash divergente: ' + field)
    require(Path(r['input']).resolve() == work / 'base.mov' and Path(r['output']).resolve() == out, 'Paths divergentes no relatório')
    require(all(r[k] == b[k] for k in ('width', 'height', 'frames', 'fps')), 'Formato de saída divergente')
    require(r['pcmExact'] is True and r['allOutputFramesDecoded'] is True and r['approved'] is False, 'Verificação incompleta')
    require(r['pcm'] == m['verification']['pcm'] and r['audioCodec'] == 'pcm_f32le', 'PCM não preservado')
    rows = r['framesChecks']; require(len(rows) == b['frames'], 'Verificação de frames incompleta')
    require(all(row['frame'] == i and row['unsafeChanged'] == 0 for i, row in enumerate(rows)), 'Proteção espacial falhou')
    if compare_cpu:
        require(r['compareCPU'] is True and any('maxDelta' in row for row in rows), 'Fixture não exercitou paridade CPU/Metal')
    require(all(row.get('maxDelta', 0) <= 1 and row.get('protectedChanged', 0) == 0 and row.get('highlightsChanged', 0) == 0 for row in rows), 'Paridade/proteção reprovada')
    verification = inspect(s, out, b, ep['ffmpeg'], 'pcm_f32le')
    require(verification['pcm'] == m['verification']['pcm'], 'Áudio da saída diverge da base')
    return m, r, verification


def render(s, job, work, compare_cpu=False):
    work = s.output_path(work); m, ep, a = analysis_current(s, job, work)
    require(not any((work / f).exists() for f in ('treated.mov', 'treated.report.json', 'verified.json', 'render.log')), 'Saída já existe')
    # Doctor is a real GPU check, not an environment-variable simulation.
    invoke([ep['python'], ep['runner'], 'doctor'], work / ('doctor-' + uuid.uuid4().hex + '.log'))
    cmd = [ep['python'], ep['runner'], 'render', '--work', work / 'analysis',
           '--output', work / 'treated.mov', '--size', f"{m['binding']['width']}x{m['binding']['height']}", '--backend', 'metal']
    if compare_cpu: cmd += ['--compare-cpu']
    invoke(cmd, work / 'render.log')
    _, r, verified = verified_report(s, job, work, compare_cpu)
    s.write(work / 'verified.json', {'outputSha256': r['outputSha256'], 'reportSha256': s.sha(work / 'treated.report.json'),
            'binding': m['binding'], 'verification': verified, 'compareCPU': compare_cpu, 'attached': False}, True)
    return {'output': str(work / 'treated.mov'), 'report': str(work / 'treated.report.json'), 'backend': r['backend'], 'device': r['device'], 'attached': False}


def attach(s, job, path, notes, work, temporal_review):
    work = s.output_path(work)
    require(Path(path).resolve() == work / 'treated.mov', 'Arquivo não pertence à execução')
    seal = s.read(work / 'verified.json')
    require(seal['reportSha256'] == s.sha(work / 'treated.report.json') and seal['outputSha256'] == s.sha(path), 'Saída/relatório mudou após verificação')
    m, r, verified = verified_report(s, job, work, seal['compareCPU'])
    e = s.read(temporal_review)
    require(e.get('outputSha256') == r['outputSha256'] and e.get('baseSha256') == m['baseSha256'] and
            e.get('editHash') == m['binding']['editHash'], 'Revisão temporal de outra fonte/corte/saída')
    require(e.get('reviewed') is True and bool(e.get('reviewer', '').strip()) and bool(e.get('notes', '').strip()) and
            e.get('checks', {}).get('temporalAlignment') == 'passed' and
            e.get('checks', {}).get('occlusions') == 'passed', 'Revisão temporal/oclusões pendente')
    result = s.attach_finish(job, 'video', path, notes + '\n' + json.dumps({
        'connector': VERSION, 'work': str(work), 'reportSha256': seal['reportSha256'],
        'temporalReview': str(Path(temporal_review).resolve()), 'temporalReviewSha256': s.sha(temporal_review),
        'baseSha256': m['baseSha256'], 'backend': 'metal', 'device': r['device']}))
    # Association records provenance, not aesthetic approval. Separate audio fields stay untouched.
    finish = s.read(s.jobdir(job) / 'finishing.json')
    finish['videoConnector'] = {'kind': VERSION, 'work': str(work), 'binding': m['binding'],
                              'reportSha256': seal['reportSha256'], 'temporalReview': str(Path(temporal_review).resolve()),
                              'temporalReviewSha256': s.sha(temporal_review)}
    s.write(s.jobdir(job) / 'finishing.json', finish)
    return result


def validate_attached(s, d):
    """Cheap semantic check + content hashes during compile, before any renderer uses a finish."""
    c = d['finishing.json'].get('videoConnector')
    if not c: return
    p = d['project.json']; b = c['binding']
    require((p['width'], p['height'], p['fps'], s.edit_hash(d)) == (b['width'], b['height'], b['fps'], b['editHash']), 'Vídeo Metal de outro corte/formato')
    for seg in b['segments']: s.resolve(seg['mediaId'])
    work = Path(c['work'])
    require(s.sha(work / 'treated.report.json') == c['reportSha256'] and
            s.sha(c['temporalReview']) == c['temporalReviewSha256'], 'Evidência Metal alterada')
    require(s.sha(s.resolve(d['finishing.json']['videoMediaId'])) == s.read(work / 'treated.report.json')['outputSha256'], 'Vídeo Metal alterado')
