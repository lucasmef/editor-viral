"""Reusable local take-selection gallery. Does not edit or approve the timeline."""
import argparse, functools, http.server, json, secrets, subprocess, threading, re
from pathlib import Path
import studio as s

TEMPLATE = s.ROOT / 'studio/templates/takes-review.html'

def validate_selection(data, manifest):
    if data.get('manifestHash') != s.digest(manifest):
        raise ValueError('Lista de tomadas mudou; recarregue a página')
    selected = data.get('selected', {})
    allowed = {scene['id']: {t['id'] for t in scene['takes']} for scene in manifest['scenes']}
    if not isinstance(selected, dict) or any(k not in allowed or v not in allowed[k] for k, v in selected.items()):
        raise ValueError('Cena ou tomada inválida')
    notes = data.get('notes', '')
    if not isinstance(notes, str) or len(notes) > 10000:
        raise ValueError('Observação inválida')
    return {'schemaVersion': 1, 'job': manifest['job'], 'manifestHash': s.digest(manifest),
            'selected': selected, 'notes': notes, 'complete': len(selected) == len(allowed),
            'scope': 'take-choice-only; fine-cut-review-pending', 'savedAt': s.now()}

def build(job, input_path, out):
    manifest = s.read(input_path)
    if manifest['job'] != job: raise ValueError('Job divergente')
    out = s.output_path(out)
    if out.exists(): raise ValueError('Use um diretório novo')
    # Validate every source/range before creating media.
    sources = {}
    for scene in manifest['scenes']:
        for take in scene['takes']:
            mid = take['mediaId']
            if mid not in sources:
                path = s.resolve(mid); duration = float(s.vh.probe(path)['format']['duration'])
                sources[mid] = (path, duration)
            if not 0 <= take['start'] < take['end'] <= sources[mid][1]:
                raise ValueError('Intervalo fora do bruto')
    out.mkdir(parents=True); (out/'clips').mkdir()
    for scene in manifest['scenes']:
        for take in scene['takes']:
            name = s.safe_id(scene['id']) + '-' + s.safe_id(take['id'])
            dest = out/'clips'/f'{name}.mp4'
            subprocess.run([s.vh.binary('ffmpeg'), '-v', 'error', '-ss', str(take['start']),
                '-i', str(sources[take['mediaId']][0]), '-t', str(take['end']-take['start']),
                '-map','0:v:0','-map','0:a:0','-vf','fps=30,scale=480:854,drawbox=x=iw*0.06:y=ih*0.06:w=iw*0.88:h=ih*0.88:color=cyan@0.7:t=1',
                '-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',
                '-c:a','aac','-b:a','128k','-movflags','+faststart',str(dest)], check=True)
            poster = dest.with_suffix('.jpg')
            subprocess.run([s.vh.binary('ffmpeg'),'-v','error','-ss','0.35','-i',str(dest),
                '-frames:v','1',str(poster)],check=True)
            take.update(src=str(dest.relative_to(out)), poster=str(poster.relative_to(out)), sha256=s.sha(dest))
            print(scene['id'],take['id'],flush=True)
    s.write(out/'manifest.json',manifest,True)
    data=json.dumps({'manifest':manifest,'manifestHash':s.digest(manifest)},ensure_ascii=False).replace('<','\\u003c')
    (out/'index.html').write_text(TEMPLATE.read_text().replace('__REVIEW_DATA__',data))
    s.log(job,'take-gallery-created',manifest=str(out/'manifest.json'),manifestHash=s.digest(manifest))
    continuous(job, out)
    print(out/'index.html')

def continuous(job, directory):
    """Add continuous scene playback without changing candidate/selection identity."""
    directory = s.output_path(directory)
    manifest = s.read(directory/'manifest.json')
    if manifest['job'] != job: raise ValueError('Job divergente')
    playback = {}
    destdir = directory/'continuous'
    destdir.mkdir(exist_ok=True)
    for scene in manifest['scenes']:
        dest = destdir/(s.safe_id(scene['id'])+'.mp4')
        listing = dest.with_suffix('.txt')
        offset = 0
        entries = []
        lines = []
        for take in scene['takes']:
            clip = (directory/take['src']).resolve()
            if not clip.is_relative_to(directory.resolve()): raise ValueError('Clip fora da galeria')
            duration = float(s.vh.probe(clip)['format']['duration'])
            entries.append({'id': take['id'], 'start': offset, 'end': offset+duration})
            offset += duration
            lines.append("file '"+str(clip).replace("'", "'\\''")+"'")
        if not dest.exists():
            listing.write_text('\n'.join(lines)+'\n')
            subprocess.run([s.vh.binary('ffmpeg'),'-v','error','-f','concat','-safe','0','-i',str(listing),
                '-c','copy','-movflags','+faststart',str(dest)],check=True)
        playback[scene['id']] = {'src': str(dest.relative_to(directory)), 'takes': entries, 'sha256': s.sha(dest)}
    s.write(directory/'playback.json',playback)
    data = json.dumps({'manifest':manifest,'manifestHash':s.digest(manifest),'playback':playback},ensure_ascii=False).replace('<','\\u003c')
    index = directory/'index.html'
    backup = directory/'index-before-continuous.html'
    if index.exists() and not backup.exists(): backup.write_bytes(index.read_bytes())
    index.write_text(TEMPLATE.read_text().replace('__REVIEW_DATA__',data))
    s.log(job,'take-gallery-continuous',manifestHash=s.digest(manifest),playback=str(directory/'playback.json'))


def serve(job, directory, port):
    directory=Path(directory).resolve(); manifest=s.read(directory/'manifest.json')
    if manifest['job'] != job: raise ValueError('Job divergente')
    token=secrets.token_urlsafe(24)
    selection_path=s.jobdir(job)/'take-selection.json'
    class Handler(http.server.SimpleHTTPRequestHandler):
        def send_head(self):
            self.byte_range = None
            path = Path(self.translate_path(self.path))
            header = self.headers.get('Range')
            if header and path.is_file():
                size = path.stat().st_size
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
                if not match or not any(match.groups()):
                    self.send_error(416); return None
                first, last = match.groups()
                start = int(first) if first else max(0, size-int(last))
                end = min(int(last), size-1) if first and last else size-1
                if start > end or start >= size:
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
                stream = path.open('rb');stream.seek(start)
                self.byte_range = end-start+1
                self.send_response(206)
                self.send_header('Content-Type', self.guess_type(str(path)))
                self.send_header('Content-Length', str(self.byte_range))
                self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                self.send_header('Accept-Ranges','bytes');self.end_headers()
                return stream
            return super().send_head()
        def copyfile(self, source, outputfile):
            if self.byte_range is None: return super().copyfile(source,outputfile)
            remaining = self.byte_range
            while remaining:
                chunk = source.read(min(65536,remaining))
                if not chunk: break
                outputfile.write(chunk);remaining -= len(chunk)
        def do_GET(self):
            if self.path == '/api/selection':
                data=s.read(selection_path) if selection_path.exists() else {}
                if data.get('manifestHash') != s.digest(manifest): data={}
                self.reply(200,data);return
            super().do_GET()
        def reply(self, status, data):
            body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.end_headers();self.wfile.write(body)
        def do_POST(self):
            if self.path != '/api/selection' or self.headers.get('X-Review-Token') != token:
                self.reply(403,{'error':'Reabra o link local de revisão'});return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0 < size <= 20000: raise ValueError('Pedido inválido')
                data=validate_selection(json.loads(self.rfile.read(size)),manifest)
                s.write(selection_path,data)
                s.log(job,'user-take-selection',**{k:v for k,v in data.items() if k!='job'})
                self.reply(200,data)
            except (ValueError,KeyError,TypeError) as e:self.reply(400,{'error':str(e)})
        def log_message(self,*args):pass
    # Single-threaded: one mutation at a time, in accordance with harness contract.
    server=http.server.HTTPServer(('127.0.0.1',port),functools.partial(Handler,directory=str(directory)))
    print(f'http://127.0.0.1:{server.server_port}/index.html#token={token}',flush=True)
    server.serve_forever()

if __name__ == '__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('build');a.add_argument('job');a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('continuous');a.add_argument('job');a.add_argument('--directory',type=Path,required=True)
    a=sub.add_parser('serve');a.add_argument('job');a.add_argument('--directory',type=Path,required=True);a.add_argument('--port',type=int,default=0)
    a=p.parse_args()
    if a.command=='build':build(a.job,a.input,a.out)
    elif a.command=='continuous':continuous(a.job,a.directory)
    else:serve(a.job,a.directory,a.port)
