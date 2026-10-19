"""Own only ephemeral render copies, never editorial outputs or shared staging."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def render_workspace(cache):
    parent = Path(cache) / 'render-public'
    if parent.is_symlink():
        raise ValueError('render-public não pode ser um link simbólico')
    parent.mkdir(parents=True, exist_ok=True)
    # Each invocation owns exactly one directory. Other renders are untouched.
    # Context teardown runs on success, Python exceptions and KeyboardInterrupt.
    # SIGKILL/power failure cannot run teardown: never sweep unknown leftovers.
    with TemporaryDirectory(prefix='render-', dir=parent) as temporary:
        yield Path(temporary)


def stage_copy(source, destination):
    """Private copy-on-write clone on APFS; independent copy elsewhere. Never hardlink."""
    import ctypes
    import os
    import shutil
    import sys
    source, destination = Path(source).resolve(), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Staging target already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'darwin':
        libc = ctypes.CDLL(None, use_errno=True)
        clone = getattr(libc, 'clonefile', None)
        if clone is not None:
            clone.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
            clone.restype = ctypes.c_int
            if clone(os.fsencode(source), os.fsencode(destination), 0) == 0:
                return {'method':'apfs-clone','bytes':source.stat().st_size}
            # clonefile is atomic; never overwrite a partial/unexpected target.
            if destination.exists():
                raise OSError('Unexpected target after failed clone')
    shutil.copy2(source, destination)
    return {'method':'copy','bytes':source.stat().st_size}
