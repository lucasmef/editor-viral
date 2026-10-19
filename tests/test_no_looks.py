"""Isolated fixtures; never evidence of approval for a real video."""
import copy
import unittest
from unittest.mock import patch
from test_studio import StudioTests, s
from test_harness import HarnessTests, h


class NoLooksStudioTests(unittest.TestCase):
    setUp = StudioTests.setUp
    tearDown = StudioTests.tearDown
    save = StudioTests.save

    def evidence(self, stage, checks):
        path = self.root / (stage + '.json')
        s.write(path, {'fingerprint': s.fingerprints(self.d)[stage],
                      'notes': 'Synthetic fixture only', 'userApproval': 'fixture',
                      'checks': {k: 'passed' for k in checks}})
        return path

    def test_no_looks_requires_real_cut_and_production_reviews(self):
        self.d['project.json']['editorialMode'] = 'no-looks'
        self.save()
        with self.assertRaisesRegex(ValueError, 'incompleta'):
            s.approve('one', 'preproduction', self.evidence('preproduction', []), 'fixture')
        s.approve('one', 'preproduction', self.evidence('preproduction', ['cuts']), 'fixture')
        with self.assertRaisesRegex(ValueError, 'incompleta'):
            s.approve('one', 'production', self.evidence('production', ['gestures','captions']), 'fixture')
        s.approve('one', 'production', self.evidence('production', ['gestures','captions','visual']), 'fixture')
        with self.assertRaisesRegex(ValueError, 'Master bloqueado'):
            s.render('one', self.root/'master.mov', master=True)

    def test_legacy_still_requires_looks(self):
        with self.assertRaisesRegex(ValueError, 'incompleta'):
            s.approve('one', 'preproduction', self.evidence('preproduction', ['cuts']), 'fixture')

    def test_mode_change_invalidates_cut_approval(self):
        s.approve('one', 'preproduction', self.evidence('preproduction', ['cuts','looks']), 'fixture')
        self.d['project.json']['editorialMode'] = 'no-looks'; self.save()
        self.assertEqual(s.status('one')['checkpoints']['preproduction'], 'stale')

    def test_no_looks_rejects_hidden_looks(self):
        self.d['project.json'].update(editorialMode='no-looks', requireLookReview=True)
        self.assertTrue(s.editorial_mode_errors(self.d))
        self.d['project.json']['requireLookReview'] = False
        self.d['looks.json']['options'] = [{'id':'real-look'}]
        self.save()
        with self.assertRaisesRegex(ValueError, 'incompatível'):
            s.approve('one', 'preproduction', self.evidence('preproduction', ['cuts']), 'fixture')

    def test_overlay_review_not_removed(self):
        self.d['project.json']['editorialMode'] = 'no-looks'
        self.d['project.json']['scenes'][0]['layers'] = [{'id':'overlay','mediaId':self.mid}]
        self.save()
        s.approve('one', 'preproduction', self.evidence('preproduction', ['cuts']), 'fixture')
        with self.assertRaisesRegex(ValueError, 'stills'):
            s.approve('one', 'production', self.evidence('production', ['gestures','captions','visual']), 'fixture')

    def test_init_neutral_and_compiler_propagates_mode(self):
        style = s.read(self.old/'studio/no-looks-style.json')
        with patch.object(s, 'read', return_value=style), patch.object(s.voice_connector, 'defaults', return_value=None):
            s.init_job('new', 'fixture', mode='no-looks')
        new = s.load('new')
        self.assertEqual(new['style.json']['layout']['labels'], [])
        self.assertFalse(new['style.json']['captionPolicy']['continuous'])
        self.assertEqual(s.records('new'), [])
        self.assertNotIn('voiceNeural', new['finishing.json'])
        self.d['project.json']['editorialMode'] = 'no-looks'
        with patch.object(s,'stage_file',return_value='fixture.mp4'), patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):
            self.assertEqual(s.compile_job(self.d)['editorialMode'], 'no-looks')


class NoLooksHarnessTests(unittest.TestCase):
    setUp = HarnessTests.setUp
    tearDown = HarnessTests.tearDown

    def test_empty_layers_allowed_but_caption_audio_visual_reviews_remain(self):
        self.p['editorialMode'] = 'no-looks'
        self.p['scenes'][0]['layers'] = []
        del self.p['reviews']['stills']
        self.assertTrue(h.validate(self.p,True,False)['ready'])
        for stage in ('cuts','captions','visual','audio'):
            p = copy.deepcopy(self.p); del p['reviews'][stage]
            self.assertFalse(h.validate(p,True,False)['ready'])
        del self.p['editorialMode']
        self.assertFalse(h.validate(self.p,True,False)['ready'])

    def test_placeholder_still_never_skipped(self):
        self.p['editorialMode'] = 'no-looks'
        self.p['scenes'][0]['layers'][0]['src'] = None
        self.assertFalse(h.validate(self.p,True,False)['ready'])
