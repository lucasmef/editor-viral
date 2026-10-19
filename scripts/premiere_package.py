"""Native-size assets, editable titles and per-scene A/V interchange.
XML is preparation, never proof of a correct host import. The host plan must be read back.
"""
import copy
import math
import subprocess
import xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image
import studio as s
from pipeline_cache import Metrics, ProbeCache, copy_asset, cached_build, sha
from premiere_titles import make_title


def node(parent, tag, value=None, **attrs):
    n = E.SubElement(parent, tag, attrs)
    if value is not None:
        n.text = str(value)
    return n


def rate(parent, fps):
    r = node(parent, 'rate')
    node(r, 'timebase', fps)
    node(r, 'ntsc', 'FALSE')


def verify_file(path, expected):
    path = Path(path).resolve()
    if sha(path) != expected:
        raise ValueError('Changed source: ' + str(path))
    return path


def av_windows(project, manifest, probe):
    entries = manifest['entries']
    by_scene = {e['scene']: e for e in entries}
    if len(by_scene) != len(entries) or set(by_scene) != {sc['id'] for sc in project['scenes']}:
        raise ValueError('A/V scene inventory does not match snapshot')
    result = []
    cursor = 0
    fps = project['fps']
    if fps != 60:
        raise ValueError('Current handoff contract requires 60 fps')
    for sc in project['scenes']:
        e = copy.deepcopy(by_scene[sc['id']])
        if sc['from'] != cursor or e['cutOut'] - e['cutIn'] != sc['duration']:
            raise ValueError('Timeline/cut mismatch: ' + sc['id'])
        if not all(isinstance(e[k], int) for k in ('frames', 'cutIn', 'cutOut')) or not 0 <= e['cutIn'] < e['cutOut'] <= e['frames']:
            raise ValueError('Invalid source range')
        for field, hash_field, kind in [('file', 'sha256', 'video'), ('audio', 'audioSha256', 'audio')]:
            path = verify_file(e[field], e[hash_field])
            info = probe(path)
            stream = next(x for x in info['streams'] if x['codec_type'] == kind)
            if kind == 'video':
                if (stream.get('width'), stream.get('height')) != (2160, 3840) or stream.get('codec_name') != 'prores' or str(stream.get('profile')) not in ('Standard', '2'):
                    raise ValueError('Visual source must be real 4K ProRes 422 Standard')
                n, d = map(int, stream['avg_frame_rate'].split('/'))
                if n/d != fps or int(stream.get('nb_frames', -1)) != e['frames']:
                    raise ValueError('Video window frames mismatch')
            else:
                if stream.get('sample_rate') != '48000' or stream.get('channels') != 2 or not stream.get('codec_name', '').startswith('pcm_'):
                    raise ValueError('Voice must be stereo PCM 48 kHz')
                # PCM duration_ts/time_base is exact, unlike rounded format.duration.
                num, den = map(int, stream['time_base'].split('/'))
                samples = round(int(stream['duration_ts']) * num * 48000 / den)
                if samples != e['frames'] * 800:
                    raise ValueError('Voice window does not match video samples')
        e.update(start=sc['from'], duration=sc['duration'], headFrames=e['cutIn'], tailFrames=e['frames']-e['cutOut'])
        if min(e['headFrames'], e['tailFrames']) < 30 and not e.get('handleException'):
            raise ValueError('Less than 0.5 s available: record actual handle exception')
        window=e.get('sourceWindow')
        if not window or window.get('sourceOut',0)-window.get('sourceIn',0)!=e['frames'] or window.get('approvedIn',-1)-window.get('sourceIn',0)!=e['cutIn'] or window.get('approvedDuration')!=e['duration']:
            raise ValueError('Real origin window provenance does not match cut/handles')
        result.append(e)
        cursor += sc['duration']
    if cursor != project['durationInFrames']:
        raise ValueError('Timeline duration mismatch')
    return result


def write_xml(package, path):
    p = package
    fps, w, h, duration = p['fps'], p['width'], p['height'], p['durationInFrames']
    root = E.Element('xmeml', version='5')
    seq = node(root, 'sequence', id='sequence-'+s.safe_id(p['job']))
    node(seq, 'name', p['job']+' — EDITAVEL')
    node(seq, 'duration', duration)
    rate(seq, fps)
    media = node(seq, 'media')
    video = node(media, 'video')
    fmt = node(node(video, 'format'), 'samplecharacteristics')
    rate(fmt, fps)
    for k, v in dict(width=w, height=h, anamorphic='FALSE', pixelaspectratio='square', fielddominance='none').items():
        node(fmt, k, v)
    audio = node(media, 'audio')
    node(audio, 'numOutputChannels', 2)
    af = node(node(audio, 'format'), 'samplecharacteristics')
    node(af, 'depth', 24)
    node(af, 'samplerate', 48000)
    outputs = node(audio, 'outputs')
    for channel in (1, 2):
        group=node(outputs,'group');node(group,'index',channel);node(group,'numchannels',1);node(group,'downmix',0);node(node(group,'channel'),'index',channel)
    tracks = {}
    # FCP7 represents Premiere stereo tracks as two exploded channel tracks.
    all_clips = []
    for original in p['clips']:
        if original['kind'] == 'video':
            all_clips.append(copy.deepcopy(original))
        else:
            for channel in (0,1):
                c=copy.deepcopy(original);c['id']=original['id']+'-ch'+str(channel+1)
                c['track']=original['track']*2+channel;c['channel']=channel+1
                c['pair']=original.get('pair','sfx-'+original['id']);all_clips.append(c)
    for kind, parent in [('video', video), ('audio', audio)]:
        count = max((c['track'] for c in all_clips if c['kind'] == kind), default=-1)+1
        for index in range(count):
            tr = node(parent, 'track')
            if kind == 'audio':
                tr.set('premiereTrackType', 'Stereo')
                tr.set('currentExplodedTrackIndex',str(index%2));tr.set('totalExplodedTrackCount','2')
            tracks[kind, index] = tr
    declared_files=set()
    for c in all_clips:
        tr = tracks[c['kind'], c['track']]
        ci = node(tr, 'clipitem', id=c['id'])
        for k, v in dict(name=c['name'], enabled='TRUE', duration=c['sourceFrames'], start=c['start'], end=c['start']+c['duration'], **{'in': c['sourceIn'], 'out': c['sourceIn']+c['duration']}).items():
            node(ci, k, v)
        rate(ci, fps)
        if c['kind'] == 'audio':
            ci.set('premiereChannelType', 'stereo')
        file_id='file-'+s.digest(c['path'])[:20]
        file = node(ci, 'file', id=file_id)
        node(file, 'name', Path(c['path']).name)
        node(file, 'pathurl', Path(c['path']).as_uri())
        rate(file, fps)
        node(file, 'duration', c['sourceFrames'])
        fm = node(file, 'media')
        if c['kind'] == 'audio':
            am = node(fm, 'audio')
            sample = node(am, 'samplecharacteristics')
            node(sample, 'depth', c.get('depth', 24))
            node(sample, 'samplerate', c.get('sampleRate',48000))
            node(am, 'channelcount', 2)
            st = node(ci, 'sourcetrack')
            node(st, 'mediatype', 'audio')
            node(st, 'trackindex', c.get('channel',1))
        else:
            sc = node(node(fm, 'video'), 'samplecharacteristics')
            rate(sc, fps)
            for k, v in dict(width=c['size'][0], height=c['size'][1], anamorphic='FALSE', pixelaspectratio='square', fielddominance='none').items():
                node(sc, k, v)
            if Path(c['path']).suffix.lower() in ('.png','.psd'):
                node(file, 'stillframe', 'TRUE')
                node(ci, 'alphatype', 'straight')
            motion = c['motion']
            ef = node(node(ci, 'filter'), 'effect')
            for k, v in dict(name='Basic Motion', effectid='basic', effectcategory='motion', effecttype='motion', mediatype='video').items():
                node(ef, k, v)
            par = node(ef, 'parameter')
            node(par, 'parameterid', 'scale'); node(par, 'name', 'Scale'); node(par, 'value', motion['scale'])
            # Host plan carries authoritative pixel positions; XML normalization is verified in host tests.
            par = node(ef, 'parameter'); node(par, 'parameterid', 'center'); node(par, 'name', 'Center')
            val = node(par, 'value')
            node(val, 'horiz', (motion['position'][0]-w/2)/c['size'][0])
            node(val, 'vert', (motion['position'][1]-h/2)/c['size'][1])
        if c.get('pair'):
            for linked in [x for x in all_clips if x.get('pair') == c['pair']]:
                link = node(ci, 'link')
                node(link, 'linkclipref', linked['id']); node(link, 'mediatype', linked['kind'])
                node(link, 'trackindex', linked['track']+1)
                siblings = [x for x in all_clips if x['kind'] == linked['kind'] and x['track'] == linked['track']]
                node(link, 'clipindex', siblings.index(linked)+1); node(link, 'groupindex', 1)
        if file_id in declared_files:
            file.clear();file.set('id',file_id)
        else:declared_files.add(file_id)
    for (kind,index),tr in tracks.items():
        node(tr, 'enabled', 'TRUE'); node(tr, 'locked', 'FALSE')
        if kind=='audio':node(tr,'outputchannelindex',index%2+1)
    E.indent(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def build(job, project, av_manifest, output, template, approval, resolve, lut=None, cache=None):
    """Frozen compiled input. Does not load or write jobs; output is a new version only."""
    if project.get('videoId')!=job:raise ValueError('Snapshot belongs to another video')
    previous=1
    for caption in project['captions']:
        if caption['from']!=previous or type(caption['duration']) is not int or caption['duration']<=0:
            raise ValueError('Caption continuity/timing mismatch')
        previous=caption['from']+caption['duration']
    if project['captions'] and previous!=project['durationInFrames']:raise ValueError('Caption must reach final frame')
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new package directory; existing Premiere packages are immutable')
    if '"$expr"' in __import__('json').dumps(project):
        raise ValueError('Animated expressions require a dedicated adapter')
    approved = s.read(approval)
    if approved.get('templateSha256') != sha(template) or not approved.get('userApproval'):
        raise ValueError('Caption template requires matching approval evidence')
    if (project['width'],project['height']) != (1440,2560):
        raise ValueError('Caption adapter currently calibrated for 1440x2560')
    caption_position = project.get('premiereCaptionPosition')
    if not caption_position or len(caption_position)!=2:
        raise ValueError('Explicit approved Premiere caption position is required')
    metrics = Metrics()
    probe = ProbeCache(s.vh.probe, metrics)
    windows = av_windows(project, av_manifest, probe)
    output.mkdir(parents=True)
    media = output/'media'
    media.mkdir()
    clips = []
    p = project
    def add(path, name, kind, track, start, duration, source_frames, source_in=0, size=None, rect=None, pair=None):
        c = dict(id='clip-'+str(len(clips)+1), name=name, path=str(path), sha256=sha(path), kind=kind, track=track, start=start, duration=duration, sourceFrames=source_frames, sourceIn=source_in)
        if pair: c['pair'] = pair
        if kind=='audio':
            stream=next(x for x in probe(path)['streams'] if x['codec_type']=='audio')
            if stream.get('channels')!=2:raise ValueError('Stereo source required')
            c.update(sampleRate=int(stream['sample_rate']),depth=int(stream.get('bits_per_sample') or 24))
        if size:
            if abs(rect['width']/size[0]-rect['height']/size[1]) > .002:
                raise ValueError('Nonuniform scaling not supported: '+name)
            c.update(size=list(size), rect=rect, motion={'position': [rect['x']+rect['width']/2, rect['y']+rect['height']/2], 'scale': 100*rect['width']/size[0]})
        clips.append(c)
    for e in windows:
        source = Path(e['file'])
        base = p['layout']['base']
        if lut or base != {'scale': 1, 'x': 0, 'y': 0}:
            if not lut:
                raise ValueError('Provide grading LUT explicitly for framed/graded sources')
            sw, sh = 2160, 3840
            nw, nh = round(sw*base['scale']/2)*2, round(sh*base['scale']/2)*2
            cx, cy = (nw-sw)/2-base['x']*sw/p['width'], (nh-sh)/2-base['y']*sh/p['height']
            # Copy LUT to a simple local cache name; reject filter syntax in paths.
            lutfile = copy_asset(lut, Path(cache)/'luts')
            if any(x in str(lutfile) for x in ("'", ':', '\\')):
                raise ValueError('Unsupported LUT path characters')
            recipe = {'adapter': sha(__file__), 'lut': sha(lut), 'base': base, 'profile': 2, 'ffmpeg': sha(s.ROOT/'.local-bin/ffmpeg')}
            def render(dest):
                filt = f"lut3d=file='{lutfile}':interp=tetrahedral,scale={nw}:{nh},crop=2160:3840:{cx}:{cy},setsar=1"
                subprocess.run([str(s.ROOT/'.local-bin/ffmpeg'), '-nostdin', '-v', 'error', '-i', str(source), '-map', '0:v:0', '-an', '-vf', filt, '-c:v', 'prores_ks', '-profile:v', '2', '-pix_fmt', 'yuv422p10le', '-threads', '4', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(dest)], check=True)
            source = cached_build(Path(cache)/'premiere-grade', recipe, [source, lutfile], '.mov', render, metrics)
        elif p.get('colorGrade') and any(p['colorGrade'].get(k, default) != default for k, default in [('brightness',1),('contrast',1),('saturation',1),('warmth',0)]):
            raise ValueError('Non-neutral grade requires explicit LUT')
        video, audio = copy_asset(source, media), copy_asset(e['audio'], media)
        info = probe(video)
        if int(next(x for x in info['streams'] if x['codec_type']=='video').get('nb_frames',-1)) != e['frames']:
            raise ValueError('Graded derivative lost frames/handles')
        add(video, 'Raquel — '+e['scene'], 'video', 0, e['start'], e['duration'], e['frames'], e['cutIn'], (2160,3840), dict(x=0,y=0,width=p['width'],height=p['height']), e['scene'])
        add(audio, 'Voz — '+e['scene'], 'audio', 0, e['start'], e['duration'], e['frames'], e['cutIn'], pair=e['scene'])
    max_layers = max((len(sc['layers']) for sc in p['scenes']), default=0)
    for sc in p['scenes']:
        for index, layer in enumerate(sc['layers']):
            if layer.get('native') or layer.get('crop') or layer.get('clipPath') or layer.get('rotation') or layer.get('transition','cut') != 'cut':
                raise ValueError('Prepare native-size masked PNG with preserved origin before export: '+layer['id'])
            from cutout_contract import validate_cutout
            source_asset = resolve(layer.get('premiereSrc') or layer['src'])
            if not layer.get('cutoutProvenance'):
                raise ValueError('Original resolution and editable mask provenance required: '+layer['id'])
            validate_cutout(source_asset, layer['cutoutProvenance'])
            asset = copy_asset(source_asset, media)
            with Image.open(asset) as im:
                if asset.suffix.lower()!='.psd' and im.mode != 'RGBA': raise ValueError('RGBA required')
                size = im.size
            if layer.get('premiereSrc'):
                with Image.open(resolve(layer['src'])) as preview_asset:
                    if preview_asset.size!=size:raise ValueError('PSD/preview canvas mismatch would shift geometry')
            if layer['from'] < 0 or layer['from']+layer['duration'] > sc['duration']:
                raise ValueError('Layer outside scene')
            add(asset, layer['id'], 'video', index+1, sc['from']+layer['from'], layer['duration'], p['durationInFrames'], size=size, rect=layer['rect'])
            clips[-1]['cutoutProvenance']=copy.deepcopy(layer['cutoutProvenance'])
    for index, label in enumerate(p['layout'].get('labels', [])):
        with Image.open(resolve(label['src'])) as im:
            im = im.convert('RGBA')
            cr = label.get('crop')
            if cr: im = im.crop((cr['x'],cr['y'],cr['x']+cr['width'],cr['y']+cr['height']))
            asset = media/('label-'+str(index)+'.png'); im.save(asset); size = im.size
        for sc in p['scenes']:
            start = min((l['from'] for l in sc['layers']), default=0) if p['layout'].get('revealOverlaysWithLooks') else 0
            add(asset,label['text'],'video',max_layers+1+index,sc['from']+start,sc['duration']-start,p['durationInFrames'],size=size,rect=dict(x=label['x']-label['width']/2,y=label['y'],width=label['width'],height=label['height']))
    if p.get('audioGainDb',0) != 0: raise ValueError('Voice gain must stay explicit and zero')
    for cue in p.get('soundEffects', []):
        if cue.get('gainDb',0) != 0: raise ValueError('Nonzero SFX gain requires host implementation')
        asset = copy_asset(resolve(cue['src']), media)
        info = probe(asset)
        frames = math.ceil(float(info['format']['duration'])*p['fps'])
        if cue['duration'] > frames: raise ValueError('SFX exceeds source')
        add(asset,'Dois estalos','audio',1,cue['from'],cue['duration'],frames)
    titles = output/'titles'; titles.mkdir()
    captions = []
    for index, word in enumerate(p['captions']):
        dest = titles/('word-%03d.mogrt' % index)
        make_title(template,word['text'],word.get('highlight',False),dest,position=caption_position,canvas=(p['width'],p['height']))
        captions.append({**word,'path':str(dest),'sha256':sha(dest),'track':max_layers+1+len(p['layout'].get('labels',[]))})
    package = {'schemaVersion':2,'job':job,**{k:p[k] for k in ('fps','width','height','durationInFrames')},'clips':clips,'captions':captions,'windows':windows,'captionTemplateSha256':sha(template),'captionApproval':approved,'snapshotSha256':s.digest(p),'importVerified':False,'masterApproved':False,
               'requiredHostChecks':['geometry','captions','avLinks','headHandles','tailHandles','saveReopen','mixLimiter'],
               'hostPlan':{'batchLimit':16,'expectedProjectPathRequired':True,'expectedSequenceIdRequired':True,'audioFallback':'Only after observed missing audio; overwrite with source In=0 then slip to sourceIn; verify timeline and source ranges','positions':'Pixel positions in clip.motion; read back every item after XML import','captions':'Import MOGRT on recorded track, trim to duration, confirm actual track and render words','limiter':'Native mix Hard Limiter; verify saved state and measured output; not applied by XML','unknownOutcome':'Stop mutations, inspect recovery and read back; never blind retry'}}
    s.write(output/'snapshot.json',p,True)
    write_xml(package,output/(s.safe_id(job)+'-premiere.xml'))
    package['xml']={'path':str(output/(job+'-premiere.xml')),'sha256':sha(output/(job+'-premiere.xml'))}
    # Preserve recovery originals and masks in immutable, content-addressed package copies.
    dependencies={}
    def remember(path):
        path=Path(path).resolve();dependencies[str(path)]={'path':str(path),'sha256':sha(path)}
    for clip in clips:
        remember(clip['path'])
        provenance=clip.get('cutoutProvenance')
        if provenance:
            records=[provenance['original']]
            recovery=provenance['recovery']
            records += [recovery[k] for k in ('pixels','mask','document','inspection') if k in recovery]
            for record in records:
                frozen=copy_asset(record['path'],output/'recovery')
                record['sourcePath']=record['path'];record['path']=str(frozen);remember(frozen)
    for title in captions:remember(title['path'])
    template_copy=copy_asset(template,output/'templates');remember(template_copy)
    package['captionTemplatePath']=str(template_copy)
    s.write(output/'dependencies.json',{'schemaVersion':1,'files':list(dependencies.values())},True)
    package['dependencies']={'path':str(output/'dependencies.json'),'sha256':sha(output/'dependencies.json')}
    s.write(output/'package.json',package,True)
    s.write(output/'metrics.json',metrics.report(),True)
    return package
