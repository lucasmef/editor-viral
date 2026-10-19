"""Storage roots: software stays in the repository; video data lives outside it."""
import json
import os
from pathlib import Path

KEYS = ('assets', 'edit', 'source', 'soundfx', 'ready', 'cache')

def roots(code_root):
    root = Path(code_root).resolve()
    config = Path(os.environ['EDITOR_STORAGE_CONFIG']) if os.environ.get('EDITOR_STORAGE_CONFIG') else root/'studio/storage.json'
    if not config.is_file():
        if os.environ.get('EDITOR_STORAGE_CONFIG') or root == Path(__file__).resolve().parents[1]:
            raise ValueError('Configuração de armazenamento ausente; não criar mídia dentro do editor')
        # Isolated test/fixture roots. Never fall back to a user's real media directories.
        return {k: root/'fixture-storage'/k for k in KEYS}
    data = json.loads(config.read_text())
    if data.get('schemaVersion') != 1 or set(data.get('roots', {})) != set(KEYS):
        raise ValueError('Configuração de armazenamento inválida')
    result = {k: Path(v).expanduser() for k,v in data['roots'].items()}
    for k,p in result.items():
        if not p.is_absolute() or p.resolve().is_relative_to(root):
            raise ValueError('Raiz de mídia deve ser absoluta e externa ao editor: '+k)
    resolved = [p.resolve() for p in result.values()]
    if any(a == b or a.is_relative_to(b) or b.is_relative_to(a) for i,a in enumerate(resolved) for b in resolved[i+1:]):
        raise ValueError('Raízes de mídia sobrepostas')
    return result

def external_output(code_root, path, ready=False):
    p = Path(path).expanduser().resolve()
    root = Path(code_root).resolve()
    # Fixtures without production configuration may write inside their sandbox.
    if (root/'studio/storage.json').exists() or os.environ.get('EDITOR_STORAGE_CONFIG'):
        r = roots(root)
        if p.is_relative_to(root):
            raise ValueError('Saída dentro do editor recusada; use Edit ou Cache')
        if p.is_relative_to(r['source'].resolve()):
            raise ValueError('Source é somente para originais')
        if not ready and p.is_relative_to(r['ready'].resolve()):
            raise ValueError('Prontos recebe somente exports liberados por release')
    return p
