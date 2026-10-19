"""Versioned, non-destructive controls for cached subject alpha and a fixed video donor.

Coordinates named Px are pixels of the alpha working canvas, except donorOffsetNative.
This module does not infer hair from RGB and never writes the source alpha.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

VERSION = 'hair-controls-v1'
ALPHA = dict(black=0., white=1., gamma=1., offsetPx=0., featherPx=.6,
             featherMode='outward', protectOpaque=True)
BACKGROUND = dict(donorOffsetNative=[0., 0.], gainRgb=[1., 1., 1.],
                  offsetRgb=[0., 0., 0.], featherPx=0., patchOffsetPx=[0., 0.])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def edit_binding(project):
    return {'fps': project['fps'], 'scenes': [
        {'id': s['id'], 'mediaId': s['clip']['mediaId'],
         'inFrame': s['clip']['inFrame'], 'frames': s['duration']}
        for s in project['scenes']]}


def number(v, lo, hi, name):
    require(type(v) in (int, float) and math.isfinite(v) and lo <= v <= hi,
            f'{name}: expected a finite number in [{lo}, {hi}]')


def keys(obj, allowed, name):
    require(isinstance(obj, dict), f'{name}: expected an object')
    require(not set(obj) - set(allowed), f'{name}: unknown keys {set(obj) - set(allowed)}')


def vector(value, n, lo, hi, name):
    require(isinstance(value, list) and len(value) == n, f'{name}: expected {n} numbers')
    for v in value:
        number(v, lo, hi, name)


def alpha_settings(override, inherited=None):
    keys(override, ALPHA, 'alpha')
    a = {**(inherited or ALPHA), **override}
    number(a['black'], 0, 1, 'alpha.black')
    number(a['white'], 0, 1, 'alpha.white')
    require(a['white'] > a['black'], 'alpha.white must exceed black')
    number(a['gamma'], .1, 10, 'alpha.gamma')
    number(a['offsetPx'], -32, 32, 'alpha.offsetPx')
    number(a['featherPx'], 0, 32, 'alpha.featherPx')
    require(a['featherMode'] in ('outward', 'symmetric'), 'Unknown featherMode')
    require(type(a['protectOpaque']) is bool, 'protectOpaque must be boolean')
    return a


def background_settings(override, inherited=None):
    keys(override, BACKGROUND, 'background')
    b = {**copy.deepcopy(inherited or BACKGROUND), **override}
    vector(b['donorOffsetNative'], 2, -8192, 8192, 'donorOffsetNative')
    vector(b['gainRgb'], 3, .25, 4, 'gainRgb')
    vector(b['offsetRgb'], 3, -128, 128, 'offsetRgb')
    vector(b['patchOffsetPx'], 2, -512, 512, 'patchOffsetPx')
    number(b['featherPx'], 0, 128, 'background.featherPx')
    return b


def interval(item, n, allowed):
    keys(item, allowed, 'interval')
    require(type(item.get('from')) is int and type(item.get('to')) is int
            and 0 <= item['from'] < item['to'] <= n, 'Invalid scene-local interval [from,to)')
    fade = item.get('fadeFrames', 12)
    require(type(fade) is int and 0 <= fade <= 120, 'fadeFrames must be an integer 0..120')
    return {**item, 'fadeFrames': fade}


def validate_config(config, cache):
    keys(config, ('schemaVersion', 'cacheId', 'defaults', 'scenes'), 'config')
    require(config.get('schemaVersion') == 1, 'Unsupported controls schema')
    require(config.get('cacheId') == cache['cacheId'], 'Controls belong to another alpha cache')
    defaults = config.get('defaults', {})
    keys(defaults, ('alpha', 'intensity', 'background'), 'defaults')
    da = alpha_settings(defaults.get('alpha', {}))
    intensity = defaults.get('intensity', 1.)
    number(intensity, 0, 1, 'intensity')
    background_settings(defaults.get('background', {}))
    overrides = config.get('scenes', {})
    keys(overrides, [s['id'] for s in cache['scenes']], 'scenes')
    result = {}
    for scene in cache['scenes']:
        v = overrides.get(scene['id'], {})
        keys(v, ('alpha', 'background', 'intensity', 'intervals', 'bypass'), scene['id'])
        a = alpha_settings(v.get('alpha', {}), da)
        b = background_settings(defaults.get('background', {}),
                                background_settings(scene.get('background', {})))
        b = background_settings(v.get('background', {}), b)
        strength = v.get('intensity', intensity)
        number(strength, 0, 1, 'intensity')
        require(isinstance(v.get('intervals', []), list) and isinstance(v.get('bypass', []), list),
                'intervals and bypass must be arrays')
        segments = []
        for entry in v.get('intervals', []):
            e = interval(entry, scene['frames'], ('from', 'to', 'fadeFrames', 'alpha', 'intensity'))
            e['alpha'] = alpha_settings(e.get('alpha', {}), a)
            e['intensity'] = e.get('intensity', strength)
            number(e['intensity'], 0, 1, 'intensity')
            segments.append(e)
        segments.sort(key=lambda e: e['from'])
        for left, right in zip(segments, segments[1:]):
            require(left['to'] + left['fadeFrames'] <= right['from'] - right['fadeFrames'],
                    'Adjustment intervals or their fades overlap; combine them explicitly')
        bypass = [interval(e, scene['frames'], ('from', 'to', 'fadeFrames')) for e in v.get('bypass', [])]
        result[scene['id']] = dict(alpha=a, background=b, intensity=strength,
                                    intervals=segments, bypass=bypass)
    return result


def interval_weight(frame, item):
    start, end, fade = item['from'], item['to'], item['fadeFrames']
    if start <= frame < end:
        return 1.
    if not fade:
        return 0.
    x = (frame - start + fade + 1) / (fade + 1) if frame < start else (end + fade - frame) / (fade + 1)
    x = max(0., min(1., x))
    return x*x*(3-2*x)


def blur(mask, sigma):
    import cv2
    if sigma == 0:
        return mask.copy()
    radius = max(1, math.ceil(3*sigma))
    return cv2.GaussianBlur(mask, (2*radius+1, 2*radius+1), sigma,
                            borderType=cv2.BORDER_REPLICATE)


def adjust_alpha(raw, settings, protected=None):
    import cv2
    import numpy as np
    require(raw.ndim == 2 and np.isfinite(raw).all() and raw.min() >= 0 and raw.max() <= 1,
            'Alpha must be finite, single-channel and in 0..1')
    a = np.clip((raw - settings['black']) / (settings['white'] - settings['black']), 0, 1)
    a = np.power(a, 1. / settings['gamma']).astype(np.float32)
    offset = settings['offsetPx']
    if offset:
        radius = abs(offset)
        low = int(math.floor(radius)); fraction = radius-low
        op = cv2.dilate if offset > 0 else cv2.erode
        def morph(r):
            if not r:
                return a
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1, 2*r+1))
            return op(a, kernel, borderType=cv2.BORDER_REPLICATE)
        a = morph(low)*(1-fraction) + morph(low+1)*fraction
    soft = blur(a, settings['featherPx'])
    a = np.maximum(a, soft) if settings['featherMode'] == 'outward' else soft
    if settings['protectOpaque']:
        a = np.where(raw == 1, 1., a)
    if protected is not None:
        require(protected.shape == raw.shape and np.isfinite(protected).all()
                and protected.min() >= 0 and protected.max() <= 1, 'Invalid manual protection mask')
        a = np.maximum(a, protected)
    return np.clip(a, 0, 1).astype(np.float32)


def frame_controls(raw, settings, frame, protected=None):
    a = adjust_alpha(raw, settings['alpha'], protected)
    strength = settings['intensity']
    for item in settings['intervals']:
        weight = interval_weight(frame, item)
        if weight:
            alt = adjust_alpha(raw, item['alpha'], protected)
            a = a*(1-weight) + alt*weight
            strength = strength*(1-weight) + item['intensity']*weight
    for item in settings['bypass']:
        strength *= 1-interval_weight(frame, item)
    return a, strength


def prepare_patch(raw, settings):
    import cv2
    import numpy as np
    h, w = raw.shape
    require(np.isfinite(raw).all() and raw.min() >= 0 and raw.max() <= 1, 'Invalid patch mask')
    dx, dy = settings['patchOffsetPx']
    shifted = cv2.warpAffine(raw, np.array([[1, 0, dx], [0, 1, dy]], np.float32),
                            (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) if dx or dy else raw.copy()
    out = blur(shifted, settings['featherPx'])
    if settings['featherPx'] or dx or dy:
        # Keep an explicit fade to zero at the processing canvas boundary.
        yy, xx = np.mgrid[:h, :w]
        distance = np.minimum.reduce([xx, yy, w-1-xx, h-1-yy]).astype(np.float32)
        ramp = np.clip(distance / max(2., 3*settings['featherPx']), 0, 1)
        out *= ramp*ramp*(3-2*ramp)
    require(max(out[0].max(), out[-1].max(), out[:, 0].max(), out[:, -1].max()) == 0,
            'Patch must fade to zero at all ROI boundaries')
    return out.astype(np.float32)


def donor_maps(scene, background, patch):
    import numpy as np
    w, h = scene['alphaSize']; dw, dh = scene['donorSize']
    x, y, rw, rh = scene['roi']; bx, by, bw, bh = scene['donorRoi']
    require(abs(rw/w - rh/h) < 1e-6 and abs(bw/dw - bh/dh) < 1e-6,
            'Working pixels must have square native scaling')
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    dx, dy = background['donorOffsetNative']
    # Pixel centers of the two resampled native canvases.
    mx = ((x+(xx+.5)*(rw/w)-dx-bx)/(bw/dw)-.5).astype(np.float32)
    my = ((y+(yy+.5)*(rh/h)-dy-by)/(bh/dh)-.5).astype(np.float32)
    active = patch > 0
    require(not active.any() or (mx[active].min() >= 0 and my[active].min() >= 0
            and mx[active].max() <= dw-1 and my[active].max() <= dh-1),
            'Donor offset exceeds cached background coverage; prepare a larger donorRoi')
    return mx, my


def composite(image, donor_frame, alpha, patch, strength, maps, background):
    import cv2
    import numpy as np
    donor = cv2.remap(donor_frame, *maps, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    gain = np.array(background['gainRgb'][::-1], np.float32)
    offset = np.array(background['offsetRgb'][::-1], np.float32)
    donor = np.clip(donor*gain + offset, 0, 255)
    effective = patch*(1-alpha)*strength
    delta = (donor-image.astype(np.float32))*effective[..., None]
    out = np.clip(np.rint(image+delta), 0, 255).astype(np.uint8)
    return out, effective, donor
