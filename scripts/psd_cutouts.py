"""Programmatic PSD mask edits in NEW files, preserving original layer pixels.
Pinned adapter: psd-tools 1.10.9. Never resizes, flattens or rewrites the source PSD.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
DEPS=Path(__file__).resolve().parents[1]/'.runtime/psd-deps'
if DEPS.is_dir():sys.path.insert(0,str(DEPS))
from PIL import Image
from psd_tools import PSDImage
from psd_tools.constants import ChannelID, Compression, Tag
from psd_tools.psd.layer_and_mask import MaskData, MaskFlags, ChannelInfo, ChannelData
from pipeline_cache import sha


def layer_at(psd, indices):
    layer=psd
    for i in indices:layer=layer[int(i)]
    if layer.is_group():raise ValueError('Select a pixel layer, not a group')
    return layer


def pixels(layer):
    # topil reads the layer channels, not the masked/rendered composite.
    image=layer.topil()
    if image is None:raise ValueError('Layer has no readable raster pixels')
    return hashlib.sha256(image.tobytes()).hexdigest()


def inspect(path):
    psd=PSDImage.open(path)
    return {'path':str(Path(path).resolve()),'sha256':sha(path),'pixelSize':list(psd.size),'depth':psd.depth,
            'layers':[{'name':l.name,'kind':l.kind,'bbox':list(l.bbox),'hasMask':l.has_mask(),'visible':l.visible} for l in psd.descendants()]}


def write_single_layer_psd(psd, layer, mask, output):
    """Conservative PSD v1 encoding for one full-canvas raster layer.

    Adobe PSD specification: signed layer count marks merged transparency;
    channel lengths include compression; mask payload is 20 bytes.
    Keep raster samples and ICC resources, omit stale application descriptors.
    """
    import struct
    pack = struct.pack
    def block(data): return pack('>I', len(data)) + data
    w, h = psd.size
    raster = layer.topil().convert('RGBA')
    if raster.size != (w, h) or layer.bbox != (0, 0, w, h):
        raise ValueError('Conservative PSD writer requires full-canvas raster')
    rgba = list(raster.split())
    merged = raster.copy()
    from PIL import ImageChops
    merged.putalpha(ImageChops.multiply(rgba[3], mask))
    # Original alpha and RGB channels, plus separate editable user mask.
    channels = [(-1, rgba[3]), (0, rgba[0]), (1, rgba[1]), (2, rgba[2]), (-2, mask)]
    payloads = [pack('>H', 0) + im.tobytes() for _, im in channels]
    mask_record = pack('>4iBB2x', 0, 0, h, w, 0, 0)
    name = layer.name.encode('macroman', errors='replace')[:255]
    pascal = bytes([len(name)]) + name
    pascal += b'\0' * (-len(pascal) % 4)
    unicode_name = layer.name.encode('utf-16be')
    name_data = pack('>I', len(unicode_name)//2) + unicode_name
    name_tag = b'8BIMluni' + block(name_data)
    name_tag += b'\0' * (-len(name_data) % 2)
    extra = block(mask_record) + block(b'') + pascal + name_tag
    record = pack('>4iH', 0, 0, h, w, len(channels))
    record += b''.join(pack('>hI', channel_id, len(data)) for (channel_id, _), data in zip(channels, payloads))
    record += b'8BIMnorm' + bytes([255, 0, 8, 0]) + block(extra)
    layer_info = pack('>h', -1) + record + b''.join(payloads)
    layer_info += b'\0' * (len(layer_info) % 2)
    layer_and_mask = block(layer_info) + block(b'')
    # Color profile and other image resources are retained from the input.
    resources = psd._record.image_resources.tobytes()
    header = b'8BPS' + pack('>H6xHIIHH', 1, 4, h, w, 8, 3)
    merged_bytes = pack('>H', 0) + b''.join(c.tobytes() for c in merged.split())
    Path(output).write_bytes(header + block(b'') + resources + block(layer_and_mask) + merged_bytes)


def mask_layer(source, indices, mask_path, output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if source==output or output.exists():raise ValueError('PSD output must be a new version')
    original_hash=sha(source)
    psd=PSDImage.open(source)
    if psd.depth!=8 or psd.pil_mode not in ('RGB','RGBA'):
        raise ValueError('Mask writer currently verified only for 8-bit RGB PSD; preserve other formats unchanged')
    layer=layer_at(psd,indices)
    before=pixels(layer)
    all_pixels=[(l.name,list(l.bbox),pixels(l)) for l in psd.descendants() if l.kind=='pixel']
    mask=Image.open(mask_path).convert('L')
    if mask.size!=psd.size:raise ValueError('Mask must retain full PSD canvas; no resize allowed')
    if layer.has_vector_mask():raise ValueError('Vector mask requires a separate verified adapter')
    mask_data=ChannelData(Compression.RLE)
    mask_data.set_data(mask.tobytes(),mask.width,mask.height,8)
    ids=[i for i,c in enumerate(layer._record.channel_info) if c.id==ChannelID.USER_LAYER_MASK]
    if ids:
        i=ids[0];layer._channels[i]=mask_data
        layer._record.channel_info[i].length=len(mask_data.data)+2
    else:
        layer._channels.append(mask_data)
        layer._record.channel_info.append(ChannelInfo(ChannelID.USER_LAYER_MASK,len(mask_data.data)+2))
    layer._record.mask_data=MaskData(top=0,left=0,bottom=mask.height,right=mask.width,background_color=0,flags=MaskFlags())
    # Refresh merged preview too: Premiere may read the composite rather than layers.
    if psd._record.header.channels not in (3,4):raise ValueError('Extra PSD channels require a separate adapter')
    if len(psd)==1 and indices==[0] and layer.kind=='pixel' and layer.bbox==(0,0,*psd.size) and layer.blend_mode.value==b'norm':
        write_single_layer_psd(psd,layer,mask,output)
    else:
        psd._record.header.channels=4
        psd._updated_layers=True
        psd._update_record()
        composite=psd.composite(viewport=(0,0,*psd.size),force=True).convert('RGBA')
        psd._record.image_data.set_data([c.tobytes() for c in composite.split()],psd._record.header)
        psd._record.layer_and_mask_information.layer_info.layer_count=-abs(psd._record.layer_and_mask_information.layer_info.layer_count)
        # Write the record directly: save() would rebuild and lose the negative count.
        with output.open('wb') as stream:psd._record.write(stream)
    reopened=PSDImage.open(output);after=layer_at(reopened,indices)
    if reopened.size!=psd.size or pixels(after)!=before or not after.has_mask() or after.mask.topil().tobytes()!=mask.tobytes():
        raise ValueError('PSD round-trip failed; output is not approved')
    if [(l.name,list(l.bbox),pixels(l)) for l in reopened.descendants() if l.kind=='pixel']!=all_pixels:raise ValueError('Another layer changed')
    if sha(source)!=original_hash:raise ValueError('Original changed unexpectedly')
    result={'documentSha256':sha(output),'sourceSha256':original_hash,'pixelSize':list(psd.size),'layer':indices,
            'editableMasksVerified':True,'originalPixelsRetained':True,'layerPixelsSha256':before,
            'maskSha256':sha(mask_path),'method':'psd-tools 1.10.9 save/reopen, raw pixel hash and user-mask bytes compared',
            'premiereVisualVerified':False,'photoshopOpenVerified':False,
            'mergedTransparencyFlagVerified':reopened._record.layer_and_mask_information.layer_info.layer_count<0}
    output.with_suffix('.inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result


def export_png(source, output):
    output=Path(output)
    if output.exists():raise ValueError('Use new PNG output')
    psd=PSDImage.open(source)
    if psd.depth!=8:raise ValueError('8-bit PNG adapter must not silently reduce source bit depth')
    image=psd.composite(viewport=(0,0,*psd.size),force=True)
    if image is None or image.size!=psd.size:raise ValueError('Composite lost original canvas')
    image.convert('RGBA').save(output)
    return {'sourceSha256':sha(source),'pngSha256':sha(output),'pixelSize':list(image.size),'resampled':False,'editableSource':str(Path(source).resolve()),'visualReview':'required for unsupported PSD blend/effect features'}


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('inspect');a.add_argument('source')
    a=sub.add_parser('mask');a.add_argument('source');a.add_argument('--layer',required=True);a.add_argument('--mask',required=True);a.add_argument('--out',required=True)
    a=sub.add_parser('png');a.add_argument('source');a.add_argument('--out',required=True)
    a=ap.parse_args()
    result=inspect(a.source) if a.cmd=='inspect' else mask_layer(a.source,[int(x) for x in a.layer.split('/')],a.mask,a.out) if a.cmd=='mask' else export_png(a.source,a.out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
