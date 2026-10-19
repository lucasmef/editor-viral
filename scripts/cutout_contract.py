"""Lossless-size cutout provenance. PNG alpha is not an editable layer mask."""
from pathlib import Path
from PIL import Image
from pipeline_cache import sha


def verify_asset(record):
    p = Path(record['path']).resolve()
    if sha(p) != record['sha256']:
        raise ValueError('Asset changed: '+str(p))
    return p


def validate_cutout(png, provenance):
    """Permit empty-canvas trimming only when its original pixel coordinates survive.
    Scaling belongs to Premiere Motion. No spatial resampling during PNG extraction.
    PSD masks require human/tool inspection evidence: a .psd suffix proves nothing.
    """
    png = Path(png)
    if provenance.get('assetSha256', provenance.get('pngSha256')) != sha(png):
        raise ValueError('Cutout provenance does not match PNG')
    original = verify_asset(provenance['original'])
    original_size = tuple(provenance['original']['pixelSize'])
    with Image.open(original) as im:
        if im.size != original_size:
            raise ValueError('Declared original pixel size differs from file')
    with Image.open(png) as im:
        output_size = im.size
        if png.suffix.lower()!='.psd' and im.mode != 'RGBA': raise ValueError('PNG must contain RGBA transparency')
    if provenance.get('resampled') is not False:
        raise ValueError('No-resampling declaration required')
    crop = provenance.get('canvasCrop', [0,0,*original_size])
    x,y,w,h = crop
    if any(type(v) is not int for v in crop) or min(x,y)<0 or min(w,h)<=0 or x+w>original_size[0] or y+h>original_size[1]:
        raise ValueError('Invalid original-pixel crop coordinates')
    if output_size != (w,h):
        raise ValueError('PNG was downsampled or its canvas coordinates were lost')
    recovery = provenance['recovery']
    if png.suffix.lower()=='.psd' and recovery.get('kind')!='layered-psd':raise ValueError('PSD source requires layer/mask round-trip evidence')
    if recovery['kind'] == 'separate-mask':
        pixels = verify_asset(recovery['pixels'])
        mask = verify_asset(recovery['mask'])
        with Image.open(pixels) as source, Image.open(mask) as alpha:
            if source.size != original_size or alpha.size != original_size:
                raise ValueError('Recoverable pixels and mask must keep original resolution')
        if sha(pixels) != provenance['original']['sha256']:
            raise ValueError('Recovery pixels must be the unchanged original')
    elif recovery['kind'] == 'layered-psd':
        psd = verify_asset(recovery['document'])
        if psd.suffix.lower() != '.psd': raise ValueError('Expected layered PSD')
        inspection = recovery['inspection']
        verify_asset(inspection)
        import json
        evidence = json.loads(Path(inspection['path']).read_text())
        if evidence.get('documentSha256') != sha(psd) or not evidence.get('editableMasksVerified') or not evidence.get('originalPixelsRetained') or not evidence.get('method'):
            raise ValueError('PSD requires actual layer/mask inspection evidence')
    else:
        raise ValueError('PNG alpha alone cannot restore discarded pixels')
    return {'pngSize':output_size,'originalSize':original_size,'canvasCrop':crop,'recoverable':True,'resampled':False}
