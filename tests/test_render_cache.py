import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from render_cache import render_workspace


class RenderCacheTests(unittest.TestCase):
    def test_success_preserves_source_output_and_other_render(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            source = root / 'original.mov'
            output = root / 'approved.mp4'
            source.write_bytes(b'original')
            output.write_bytes(b'preview evidence')
            with render_workspace(root / 'cache') as first:
                (first / 'copy.mov').write_bytes(source.read_bytes())
                with render_workspace(root / 'cache') as second:
                    (second / 'link').symlink_to(source)
                self.assertFalse(second.exists())
                self.assertTrue(first.exists())
            self.assertFalse(first.exists())
            self.assertEqual(source.read_bytes(), b'original')
            self.assertEqual(output.read_bytes(), b'preview evidence')

    def test_failure_and_interrupt_remove_only_owned_directory(self):
        for error in (RuntimeError, KeyboardInterrupt):
            with tempfile.TemporaryDirectory() as base:
                unknown = Path(base) / 'render-public' / 'old-unclassified'
                unknown.mkdir(parents=True)
                with self.assertRaises(error):
                    with render_workspace(base) as work:
                        (work / 'partial.mov').write_bytes(b'partial')
                        raise error()
                self.assertFalse(work.exists())
                self.assertTrue(unknown.exists())

    def test_refuses_redirected_cache_parent(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / 'outside').mkdir()
            (root / 'render-public').symlink_to(root / 'outside')
            with self.assertRaises(ValueError):
                with render_workspace(root):
                    self.fail('must not enter')

    def test_staged_copy_is_independent_in_both_directions(self):
        from render_cache import stage_copy
        with tempfile.TemporaryDirectory() as base:
            root=Path(base);source=root/'source';destination=root/'copy'
            source.write_bytes(b'original')
            result=stage_copy(source,destination)
            self.assertIn(result['method'],('apfs-clone','copy'))
            source.write_bytes(b'changed source')
            self.assertEqual(destination.read_bytes(),b'original')
            destination.write_bytes(b'changed copy')
            self.assertEqual(source.read_bytes(),b'changed source')
            with self.assertRaises(ValueError):stage_copy(source,destination)
