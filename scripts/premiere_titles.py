"""Versioned editable Premiere Basic Title adapter; preserves BinaryHash metadata."""
import base64
import gzip
import io
import json
import struct
import uuid
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path


def unzip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n) for n in z.namelist()}


def zipped(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return buffer.getvalue()


def text_nodes(root):
    for element in root.iter('StartKeyframeValue'):
        try:
            raw = base64.b64decode(element.text or '', validate=True)
            value = json.loads(raw[8:8+int.from_bytes(raw[:4], 'little')].decode('utf-16le'))
            value['mTextParam']['mStyleSheet']['mText']
        except (ValueError, KeyError, UnicodeError, TypeError):
            continue
        yield element, value


def make_title(template, text, highlight, output, position=None, canvas=(1440, 2560)):
    if not text.strip():
        raise ValueError('Empty caption')
    outer = unzip(Path(template).read_bytes())
    inner = unzip(outer['project.prgraphic'])
    projects = [n for n in inner if n.endswith('.prproj')]
    if len(projects) != 1:
        raise ValueError('Unsupported title template')
    name = projects[0]
    root = E.fromstring(gzip.decompress(inner[name]))
    nodes = list(text_nodes(root))
    if len(nodes) != 1:
        raise ValueError('Template must have exactly one text payload')
    element, value = nodes[0]
    value['mTextParam']['mStyleSheet']['mText'] = text
    value['mTextParam']['mShadowVisible'] = bool(highlight)
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-16le')
    element.text = base64.b64encode(struct.pack('<II', len(raw), 0) + raw).decode()
    for frame in root.iter('FrameRect'):
        frame.text = '0,0,%s,%s' % canvas
    if position is not None:
        for param in root.iter('PointComponentParam'):
            if param.findtext('Name') == 'Position':
                start = param.find('StartKeyframe')
                fields = start.text.split(',')
                fields[1:3] = [str(position[0]/canvas[0]), str(position[1]/canvas[1])]
                start.text = ','.join(fields)
    inner[name] = gzip.compress(E.tostring(root, encoding='utf-8', xml_declaration=True), mtime=0)
    outer['project.prgraphic'] = zipped(inner)
    definition = json.loads(outer['definition.json'].decode('utf-8-sig'))
    definition['capsuleID'] = str(uuid.uuid5(uuid.NAMESPACE_OID, element.text))
    definition['capsuleName'] = text
    definition['capsuleNameLocalized'] = {'strDB': [{'localeString': 'en_US', 'str': text}]}
    for control in definition.get('clientControls', []):
        if control.get('type') == 6:
            for v in control.get('value', {}).get('strDB', []):
                v['str'] = text
    outer['definition.json'] = json.dumps(definition, ensure_ascii=False).encode()
    Path(output).write_bytes(zipped(outer))


def inspect_title(path):
    outer = unzip(Path(path).read_bytes())
    inner = unzip(outer['project.prgraphic'])
    project = next(v for k, v in inner.items() if k.endswith('.prproj'))
    nodes = list(text_nodes(E.fromstring(gzip.decompress(project))))
    if len(nodes) != 1:
        raise ValueError('Invalid title payload')
    return nodes[0][1]['mTextParam']
