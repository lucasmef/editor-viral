"""Apply the reviewed local move patch only to the exact installed 1.24.0 file."""
from pathlib import Path
import hashlib
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / '.runtime/premiere-pro-mcp-1.24.0/package/dist/tools/timeline.js'
original = (HERE / 'timeline-1.24.0.original.js').read_text()
assert hashlib.sha256(original.encode()).hexdigest() == '838c268a12910eab2e32d175f9368c430cf3cc4e3bb272d9f0b8c20fe096d86d', 'Upstream backup checksum mismatch'
patched = 'import { safeMoveScript } from "./safe-move-script.js";\n' + original
start = patched.index('        move_clip: {')
pos = patched.index('                const nodeId = escapeForExtendScript(args.node_id);', start)
patched = patched[:pos] + '''                if (args.new_track_index !== undefined) {
                    return sendCommand(buildToolScript(safeMoveScript(args.node_id, args.new_start_seconds, args.new_track_index)), bridgeOptions);
                }
''' + patched[pos:]
old_description = 'EXPERIMENTAL (undocumented QE DOM for track changes): Move a clip to a new position on the timeline; optional track moves use Premiere\'s QE API and may not work on every version.'
new_description = 'Local safe-move-v1 patch: cross-track moves require a collision-free route and compare all A/V clip identities, ranges and readable effects after each step. Refuses occupied final ranges, linked or animated moved clips, and transition-bearing route tracks. May use an existing empty track; never creates one. Same-track calls without new_track_index retain upstream behavior. Uses experimental QE for track changes.'
patched = patched.replace(old_description, new_description)
current = TARGET.read_text()
# Also recognize the exact pre-description local variant used during validation.
pre_description = patched.replace(new_description, old_description)
if current not in (original, patched, pre_description):
    raise SystemExit('Unrecognized installed code; refusing to overwrite another change/version.')
if '--restore' in sys.argv:
    TARGET.write_text(original)
    print('Restored original 1.24.0 timeline handler; local helper is now unused.')
    raise SystemExit(0)
TARGET.write_text(patched)
helper = (HERE/'safe-move-script.js').read_bytes()
(TARGET.parent/'safe-move-script.js').write_bytes(helper)
print('Applied premiere-pro-mcp 1.24.0 + local safe-move-v1')
print('upstream sha256',hashlib.sha256(original.encode()).hexdigest())
print('patched sha256',hashlib.sha256(patched.encode()).hexdigest())
print('helper sha256',hashlib.sha256(helper).hexdigest())
