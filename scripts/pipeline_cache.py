"""Measured, content-keyed derivative cache. No editorial files are removed."""
import hashlib
import json
import os
import shutil
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class Metrics:
    def __init__(self):
        self.events = []

    @contextmanager
    def measure(self, stage, **details):
        start = time.perf_counter()
        event = dict(stage=stage, **details)
        try:
            yield event
            event['ok'] = True
        except BaseException:
            event['ok'] = False
            raise
        finally:
            event['seconds'] = time.perf_counter() - start
            self.events.append(event)

    def report(self):
        return {'schemaVersion': 1, 'events': self.events,
                'costOrder': sorted(self.events, key=lambda e: e['seconds'], reverse=True)}


class ProbeCache:
    """One probe per unchanged file in this invocation; no stale persistent stat trust."""
    def __init__(self, probe, metrics=None):
        self.probe = probe
        self.values = {}
        self.metrics = metrics or Metrics()

    def __call__(self, path):
        path = Path(path).resolve()
        st = path.stat()
        key = (str(path), st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        if key not in self.values:
            with self.metrics.measure('probe', path=str(path)):
                self.values[key] = self.probe(path)
        return self.values[key]


def cached_build(root, recipe, inputs, suffix, build, metrics=None):
    """Hash inputs and result on every use; exclusive lock, publish only complete outputs."""
    root = Path(root)
    if root.is_symlink():
        raise ValueError('Cache root is a symlink')
    root.mkdir(parents=True, exist_ok=True)
    metrics = metrics or Metrics()
    with metrics.measure('input-hashing', files=len(inputs)):
        identity = {'version': 1, 'recipe': recipe, 'inputs': [sha(p) for p in inputs]}
    key = fingerprint(identity)
    target = root / (key + suffix)
    receipt = root / (key + '.json')
    lock = root / (key + '.lock')
    # Another writer must finish before a retry; never delete another process's lock.
    with lock.open('x'):
        try:
            if target.is_file() and receipt.is_file():
                with metrics.measure('cache-validation', key=key):
                    record = json.loads(receipt.read_text())
                    valid = record.get('identity') == identity and record.get('sha256') == sha(target)
                if valid:
                    metrics.events.append({'stage': 'cache-hit', 'seconds': 0, 'ok': True, 'key': key})
                    return target
            temp = root / ('.' + key + '-' + uuid.uuid4().hex + suffix)
            try:
                with metrics.measure('build', key=key):
                    build(temp)
                if not temp.is_file() or not temp.stat().st_size:
                    raise ValueError('Builder did not produce a nonempty file')
                record = {'identity': identity, 'sha256': sha(temp)}
                os.replace(temp, target)
                rtemp = root / ('.' + key + '.json')
                rtemp.write_text(json.dumps(record, sort_keys=True))
                os.replace(rtemp, receipt)
            finally:
                temp.unlink(missing_ok=True)
            return target
        finally:
            lock.unlink()


def copy_asset(source, directory):
    """Content names prevent collisions between same-named per-scene WAV files."""
    source = Path(source)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = sha(source)
    destination = directory / (digest + source.suffix.lower())
    if destination.exists():
        if sha(destination) != digest:
            raise ValueError('Corrupt package asset: ' + str(destination))
    else:
        shutil.copy2(source, destination)
        if sha(destination) != digest:
            raise ValueError('Copy verification failed')
    return destination
