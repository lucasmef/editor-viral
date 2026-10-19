"""Deterministic review sheets: original, reconstruction, alpha and progressive states.
Metrics flag differences; they never approve fidelity or modify production cutouts.
"""
import html
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import studio as s
from pipeline_cache import sha, Metrics


def checked(item):
    p = Path(item['path']).resolve()
    if sha(p) != item['sha256']:
        raise ValueError('Reference changed: '+str(p))
    return p


def load_rgba(path):
    if Path(path).suffix.lower()=='.psd':
        from psd_cutouts import PSDImage
        doc=PSDImage.open(path)
        image=doc.composite(viewport=(0,0,*doc.size),force=True)
        if image is None:raise ValueError('PSD composite unavailable')
        return image.convert('RGBA')
    with Image.open(path) as im:return im.convert('RGBA')


def placed(item, size):
    image = load_rgba(checked(item))
    if item.get('mask'):
        with Image.open(checked(item['mask'])) as mask:
            mask = mask.convert('L')
            if mask.size != image.size:
                raise ValueError('Mask canvas must match original')
            image.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
    rect = item['rect']
    target = (round(rect['width']), round(rect['height']))
    if min(target) <= 0:
        raise ValueError('Invalid dimensions')
    if abs(target[0]/image.width-target[1]/image.height) > .01:
        raise ValueError('Review refuses distorted assets')
    layer = Image.new('RGBA', size)
    layer.alpha_composite(image.resize(target, Image.Resampling.LANCZOS), (round(rect['x']), round(rect['y'])))
    return layer


def build(plan_path, output):
    plan = s.read(plan_path)
    output = Path(output)
    if output.exists(): raise ValueError('Use a new review directory')
    output.mkdir(parents=True)
    report = {'schemaVersion':1,'planSha256':sha(plan_path),'scenes':[],'approved':False,'review':'human-required'}
    metrics = Metrics()
    pages = []
    for scene in plan['scenes']:
        sid = s.safe_id(scene['id'])
        size = tuple(plan['canvas'])
        with metrics.measure('scene-review',scene=sid):
            background = Image.open(checked(scene['frame'])).convert('RGBA')
            if background.size != size: raise ValueError('Real frame must match review canvas')
            reference = placed(scene['reference'],size)
            layers = scene['layers']
            for layer in layers:
                if not 0 <= layer['from'] < layer['to'] <= scene['duration']:
                    raise ValueError('Layer timing out of scene')
            by_id = {l['id']:l for l in layers}
            for contact in scene.get('contacts',[]):
                base=by_id[contact['base']];upper=by_id[contact['overlay']]
                if contact.get('method')!='overlay-with-without' or not contact.get('alignmentEvidence'):
                    raise ValueError('Cinto/tênis requires aligned with/without states')
                if not upper.get('mask') or not contact.get('feather') or contact['feather'].get('scope')!='contact-only':
                    raise ValueError('Contact requires editable mask and localized soft feather')
                checked(upper['mask'])
                if not (base['from']<=upper['from'] and base['to']>=upper['to']):
                    raise ValueError('Original base must remain beneath the complement')
                if layers.index(base)>=layers.index(upper):raise ValueError('Complement must be above unchanged base')
            if len(by_id) != len(layers): raise ValueError('Duplicate layer ID')
            for layer in layers:
                if layer.get('pairedBase'):
                    base = by_id[layer['pairedBase']]
                    if layer['rect'] != base['rect'] or Image.open(checked(layer)).size != Image.open(checked(base)).size:
                        raise ValueError('Front/base lost shared canvas or transform')
            rendered = {l['id']:placed(l,size) for l in layers}
            frames = sorted({0,scene['duration']-1} | {f for l in layers for t in (l['from'],l['to']) for f in (t-1,t) if 0<=f<scene['duration']})
            folder = output/sid;folder.mkdir()
            files=[]
            def save(image,name):
                image.save(folder/name); files.append(name)
            save(Image.alpha_composite(background,reference),'reference.png')
            for frame in frames:
                composition = Image.new('RGBA',size)
                active=[]
                for layer in layers:
                    if layer['from'] <= frame < layer['to']:
                        composition = Image.alpha_composite(composition,rendered[layer['id']]);active.append(layer['id'])
                # Guides are review-only and stay out of production sources.
                composite = Image.alpha_composite(background,composition)
                draw = ImageDraw.Draw(composite)
                draw.rectangle((size[0]*.06,size[1]*.06,size[0]*.94,size[1]*.94),outline='#00ffff',width=2)
                save(composite,f'state-{frame:05d}.png')
            final_frame=scene.get('comparisonFrame',scene['duration']-1)
            assembly=Image.new('RGBA',size)
            for layer in layers:
                if layer['from']<=final_frame<layer['to']:assembly=Image.alpha_composite(assembly,rendered[layer['id']])
            # Compare premultiplied visible color over neutral backgrounds; hidden RGB is irrelevant.
            def visible(im):return Image.alpha_composite(Image.new('RGBA',size,(96,96,96,255)),im).convert('RGB')
            delta=ImageChops.difference(visible(reference),visible(assembly))
            save(delta,'difference.png');save(assembly.getchannel('A'),'alpha.png')
            save(Image.blend(visible(reference),visible(assembly),.5),'overlay.png')
            from PIL import ImageStat
            mean=ImageStat.Stat(delta).mean
            rois=[]
            for i,roi in enumerate(scene.get('regions',[])):
                box=tuple(roi['box'])
                a=visible(reference).crop(box);b=visible(assembly).crop(box)
                strip=Image.new('RGB',(a.width*2,a.height));strip.paste(a,(0,0));strip.paste(b,(a.width,0))
                save(strip,f'contact-{i}.png');rois.append(roi)
            report['scenes'].append({'id':sid,'frames':frames,'comparisonFrame':final_frame,'meanAbsoluteRGBDifference':mean,'regions':rois,'files':[{ 'path':str(folder/f),'sha256':sha(folder/f)} for f in files],'review':'pending'})
            cards=''.join(f'<figure><img loading="lazy" src="{sid}/{f}"><figcaption>{html.escape(f)}</figcaption></figure>' for f in files)
            pages.append(f'<section><h2>{html.escape(sid)}</h2><div class="grid">{cards}</div></section>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Revisão por cena</title><style>body{background:#171717;color:#eee;font:16px system-ui} .grid{display:flex;overflow:auto;gap:12px}figure{margin:0;flex:0 0 28vw}img{width:100%;max-height:75vh;object-fit:contain}figcaption{padding:8px}h1,h2,p{margin:20px}</style><h1>Referência, encaixes e estados</h1><p>Diferenças são alertas. Aprovação visual continua pendente. Abra cada imagem para conferir bordas em 100%.</p>'+''.join(pages))
    s.write(output/'review.json',report,True);s.write(output/'metrics.json',metrics.report(),True)
    return report
