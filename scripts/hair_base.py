"""Composition on an optional existing video finish; never runs skin processing."""
import subprocess
import json
import os
from fractions import Fraction
from pathlib import Path

import hair_controls as hc
import video_harness as vh

PCM = {'pcm_s16le': ('s16le', 2), 'pcm_s24le': ('s24le', 3), 'pcm_f32le': ('f32le', 4)}


def inspect(path, size, frames):
    exe = vh.binary('ffprobe'); env = dict(os.environ)
    if (Path(exe).parent/'libavdevice.dylib').exists(): env['DYLD_LIBRARY_PATH'] = str(Path(exe).parent)
    info = json.loads(subprocess.check_output([exe, '-v', 'error', '-show_streams', '-of', 'json', str(path)], env=env))
    videos = [v for v in info['streams'] if v['codec_type'] == 'video']
    audios = [a for a in info['streams'] if a['codec_type'] == 'audio']
    hc.require(len(videos) == len(audios) == 1, 'Hair upstream needs one video and one audio stream')
    v, a = videos[0], audios[0]
    hc.require(v['width'] * size[1] == v['height'] * size[0] and
               v['width'] >= size[0] and v['height'] >= size[1], 'Upstream must match aspect and cannot be upscaled')
    hc.require(all(Fraction(v[k]) == 60 for k in ('r_frame_rate', 'avg_frame_rate')), 'Upstream must be CFR 60 fps')
    # This editor's ProRes 422 Standard writer encodes limited range, but MOV/nclc
    # carries no range flag and this ffprobe omits color_range for that codec.
    prores_contract = (v['codec_name']=='prores' and v.get('pix_fmt')=='yuv422p10le'
                       and str(v.get('profile')) in ('Standard','2') and v.get('color_range') in (None,'unknown'))
    hc.require(all(v.get(k) == 'bt709' for k in ('color_space', 'color_transfer', 'color_primaries'))
               and (v.get('color_range') == 'tv' or prores_contract), 'Upstream must be limited-range Rec.709')
    hc.require(v.get('sample_aspect_ratio', '1:1') in ('1:1', 'N/A') and
               not float(v.get('tags', {}).get('rotate', 0)) and
               all(not float(d.get('rotation', 0)) for d in v.get('side_data_list', [])), 'Upstream geometry is not normalized')
    hc.require(a['codec_name'] in PCM and a['sample_rate'] == '48000' and a['channels'] == 2,
               'Upstream audio must be PCM16/24/float stereo 48kHz')
    # No fps filter here: catch discontinuities instead of hiding them.
    lines = subprocess.check_output([vh.binary('ffmpeg'), '-v', 'error', '-xerror', '-i', str(path),
        '-map', '0:v:0', '-fps_mode', 'passthrough', '-f', 'framemd5', '-'], text=True).splitlines()
    tb = Fraction(next(x.split(':', 1)[1].strip() for x in lines if x.startswith('#tb 0:')))
    rows = [x.split(',') for x in lines if x and not x.startswith('#')]
    hc.require(len(rows) == frames and all(Fraction(int(x[2])) * tb == Fraction(i, 60)
               and Fraction(int(x[3])) * tb == Fraction(1, 60) for i, x in enumerate(rows)), 'Upstream frames/PTS differ from cut')
    raw = audio(path, a['codec_name'])
    hc.require(len(raw) == frames * 800 * 2 * PCM[a['codec_name']][1], 'Upstream PCM length differs from cut')
    return dict(path=str(Path(path).resolve()), sha256=hc.sha(path), codec=a['codec_name'],
                size=[v['width'], v['height']], frames=frames,
                rangePolicy='editor-prores422-limited' if prores_contract else 'explicit-tv')


def audio(path, codec, start=None, end=None):
    args = [vh.binary('ffmpeg'), '-v', 'error', '-i', str(path), '-map', '0:a:0']
    if start is not None:
        args += ['-af', f'atrim=start_sample={start*800}:end_sample={end*800},asetpts=PTS-STARTPTS']
    return subprocess.check_output(args + ['-c:a', codec, '-f', PCM[codec][0], '-'])


def audio_file(path, raw, codec):
    subprocess.run([vh.binary('ffmpeg'), '-v', 'error', '-n', '-f', PCM[codec][0], '-ar', '48000', '-ac', '2',
                    '-i', '-', '-c:a', 'copy', str(path)], input=raw, check=True)


class Reader:
    """Sequential CFR decoding; prefix skipped by reading, never approximate seeking."""
    def __init__(self, path, size):
        self.size = size
        self.index = 0
        self.process = subprocess.Popen([vh.binary('ffmpeg'), '-v', 'error', '-i', str(path), '-map', '0:v:0',
            '-vf', f'scale={size[0]}:{size[1]}:flags=lanczos:in_color_matrix=bt709:in_range=tv:out_range=pc',
            '-fps_mode', 'passthrough', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)

    def read(self, index):
        import numpy as np
        hc.require(index >= self.index, 'Cannot rewind upstream reader')
        while self.index <= index:
            raw = self.process.stdout.read(self.size[0] * self.size[1] * 3)
            hc.require(len(raw) == self.size[0] * self.size[1] * 3, 'Upstream ended early')
            self.index += 1
        return np.frombuffer(raw, np.uint8).reshape(self.size[1], self.size[0], 3).copy()

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        self.process.stdout.close()
        self.process.wait()


def compose(full, plate, effective, affine):
    """Premultiplied patch, opaque subject untouched. No RGB hair classifier."""
    import cv2
    import numpy as np
    size = (full.shape[1], full.shape[0])
    e = cv2.warpAffine(effective, affine, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    p = cv2.warpAffine(plate.astype(np.float32)*effective[:, :, None], affine, size,
                       flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    result = np.clip(np.rint(full.astype(np.float32)*(1-e[:, :, None])+p), 0, 255).astype(np.uint8)
    hc.require(np.array_equal(result[e == 0], full[e == 0]), 'Protected upstream pixels changed')
    return result


def production_encoder(path, size):
    return subprocess.Popen([vh.binary('ffmpeg'), '-v', 'error', '-n', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', f'{size[0]}x{size[1]}', '-r', '60', '-i', '-', '-an', '-vf',
        'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
        '-c:v', 'prores_ks', '-profile:v', '2', '-pix_fmt', 'yuv422p10le', '-threads', '2',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
        '-video_track_timescale', '60000', '-movflags', '+write_colr', str(path)], stdin=subprocess.PIPE)
