import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import studio as s
import hair_connector as hair
import hair_controls as hc
import test_studio as shared


class HairConnectorTests(unittest.TestCase):
    tearDown = shared.StudioTests.tearDown
    save = shared.StudioTests.save

    def setUp(self):
        shared.StudioTests.setUp(self)
        cache = dict(kind='hair-alpha-cache', schemaVersion=1, binding=hc.edit_binding(self.d['project.json']),
                     scenes=[dict(id='a', frames=60, fullSize=[720,1280], background={})])
        cache['cacheId'] = hc.digest(cache)
        self.cache = self.root/'cache.json'; s.write(self.cache, cache)
        with patch.object(hair, 'validate_external'):
            hair.setup(s, 'one', self.cache, python=sys.executable)
        self.d = s.load('one')

    def run_fixture(self, partial=False):
        work = self.root/'hair-run'; out = work/'render'; out.mkdir(parents=True)
        result = out/'result-pcm.mov'; result.write_bytes(b'hair output fixture')
        req = hair.request(s, self.d)
        s.write(out/'config.json', req['controls'])
        report = dict(technicalPass=True, pcmBitExact=True, ptsVerified=True, sourceAlphaUnchanged=True,
            binding=req['binding'], cacheId=req['cache']['cacheId'], configSha256=s.sha(out/'config.json'),
            scripts={k:v for k,v in req['scripts'].items() if k!='hair_connector.py'},
            upstream={'sha256':req['upstreamMediaId'][2:]} if req['upstreamMediaId'] else None,
            fullCut=not partial, selection=[dict(scene='a',start=0,end=60)], frames=60, fps=60,
            quality='preview', size=[720,1280], outputs=[dict(file=result.name,sha256=s.sha(result),frames=60,size=[720,1280])])
        s.write(out/'report.json', report)
        s.write(work/'stage.json', dict(version=hair.VERSION, request=req, reportSha256=s.sha(out/'report.json')))
        return work, result

    def attached(self):
        work, path = self.run_fixture()
        with patch.object(s.vh,'probe',return_value={'format':{'duration':'1'}}): hair.attach(s,'one',work)
        self.d=s.load('one'); return work,path

    def test_settings_are_job_owned_and_snapshotted(self):
        rev=s.checkpoint('one','fixture')
        self.assertEqual(s.read_snapshot('one',rev)['documents']['finishing.json']['hair']['controls'],self.d['finishing.json']['hair']['controls'])
        self.assertFalse(self.d['finishing.json']['hair']['enabled'])

    def test_export_does_not_mutate_job(self):
        hair.configure(s,'one',output=self.root/'export.json')
        self.assertEqual(s.load('one'),self.d)
        with self.assertRaises(FileExistsError):hair.configure(s,'one',output=self.root/'export.json')

    def test_adjustment_invalidates_postproduction_only(self):
        before=s.fingerprints(self.d)
        self.d['finishing.json']['hair']['controls']['defaults']['alpha']['featherPx']=1
        after=s.fingerprints(self.d)
        self.assertEqual(before['production'],after['production'])
        self.assertNotEqual(before['postproduction'],after['postproduction'])

    def test_invalid_settings_fail_without_mutation(self):
        c=copy.deepcopy(self.d['finishing.json']['hair']['controls']);c['defaults']['alpha']['black']=2
        s.write(self.root/'bad.json',c)
        with self.assertRaises(ValueError):hair.configure(s,'one',self.root/'bad.json')
        self.assertEqual(s.load('one'),self.d)

    def test_same_duration_trim_is_stale(self):
        self.attached();self.d['project.json']['scenes'][0]['clip']['inFrame']+=1
        with self.assertRaisesRegex(ValueError,'corte'):hair.validate_attached(s,self.d)

    def test_scene_order_changes_binding(self):
        p=copy.deepcopy(self.d['project.json']); other=copy.deepcopy(p['scenes'][0]);other['id']='b';p['scenes'].append(other)
        self.assertNotEqual(hc.edit_binding(p),hc.edit_binding({**p,'scenes':list(reversed(p['scenes']))}))

    def test_controls_change_requires_recomposition(self):
        self.attached();self.d['finishing.json']['hair']['controls']['defaults']['intensity']=.8
        with self.assertRaisesRegex(ValueError,'desatualizado'):hair.validate_attached(s,self.d)

    def test_caption_still_audio_changes_do_not_invalidate_hair(self):
        self.attached();self.d['project.json']['scenes'][0]['captions'][0]['text']='new'
        self.d['project.json']['scenes'][0]['layers']=[{'id':'new','mediaId':self.pid}]
        self.d['finishing.json'].update(audioMediaId=self.pid,audioEditHash=s.edit_hash(self.d),audioGainDb=2)
        self.assertEqual(hair.validate_attached(s,self.d),self.d['finishing.json']['hair']['output']['mediaId'])

    def test_changing_makeup_base_invalidates_hair(self):
        self.attached();self.d['finishing.json'].update(videoMediaId=self.mid,videoEditHash=s.edit_hash(self.d))
        with self.assertRaisesRegex(ValueError,'desatualizado'):hair.validate_attached(s,self.d)

    def test_resolution_change_invalidates_result(self):
        self.attached();self.d['project.json'].update(width=720,height=1280)
        with self.assertRaisesRegex(ValueError,'desatualizado'):hair.validate_attached(s,self.d)

    def test_preview_cannot_enter_master(self):
        self.attached()
        with self.assertRaisesRegex(ValueError,'amostra'):hair.validate_attached(s,self.d,True)

    def test_partial_cannot_attach(self):
        w,_=self.run_fixture(partial=True)
        with self.assertRaisesRegex(ValueError,'parcial'):hair.attach(s,'one',w)
        self.assertFalse(s.load('one')['finishing.json']['hair']['enabled'])

    def test_output_tamper_blocks_compile(self):
        _,p=self.attached();p.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'alterado'):s.compile_job(self.d)

    def test_cache_tamper_blocks_compile(self):
        self.attached();self.cache.write_text('{}')
        with self.assertRaisesRegex(ValueError,'changed'):s.compile_job(self.d)

    def test_report_tamper_blocks_compile(self):
        w,_=self.attached();(w/'render/report.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'alterado'):s.compile_job(self.d)

    def test_upstream_not_replaced_and_audio_preserved(self):
        self.d['finishing.json'].update(videoMediaId=self.mid,videoEditHash=s.edit_hash(self.d),audioMediaId=self.pid,audioEditHash=s.edit_hash(self.d),audioGainDb=4)
        self.save();self.attached();f=self.d['finishing.json']
        self.assertEqual(f['videoMediaId'],self.mid);self.assertEqual(f['audioMediaId'],self.pid);self.assertEqual(f['audioGainDb'],4)
        self.assertEqual(s.status('one')['checkpoints']['postproduction'],'pending')

    def test_compile_uses_hair_then_disable_restores_base(self):
        self.d['finishing.json'].update(videoMediaId=self.mid,videoEditHash=s.edit_hash(self.d));self.save();self.attached()
        with patch.object(s,'stage_file',side_effect=lambda m:m),patch.object(s.vh,'probe',return_value={'format':{'duration':'100' if False else '1'}}):
            # Original/proxy checks require enough media duration; attached check requires exact timeline.
            def probe(path):return {'format':{'duration':'1' if str(path).endswith(self.d['finishing.json']['hair']['output']['mediaId']) or str(path).endswith(self.mid) else '100'}}
            with patch.object(s.vh,'probe',side_effect=probe):
                compiled=s.compile_job(self.d)
            self.assertEqual(compiled['source'],self.d['finishing.json']['hair']['output']['mediaId'])
        hair.disable(s,'one');d=s.load('one')
        self.assertEqual(d['finishing.json']['hair']['controls'],self.d['finishing.json']['hair']['controls'])
        self.assertIsNone(hair.validate_attached(s,d))

    def test_disabled_stale_result_does_not_block_other_editing(self):
        self.attached();hair.disable(s,'one');d=s.load('one');d['project.json']['scenes'][0]['clip']['inFrame']+=1
        self.assertIsNone(hair.validate_attached(s,d));self.assertEqual(hair.summary(s,d)['state'],'stale')

    def test_no_recursive_hair_base(self):
        self.attached();self.d['finishing.json'].update(videoMediaId=self.d['finishing.json']['hair']['output']['mediaId'],videoEditHash=s.edit_hash(self.d))
        with self.assertRaisesRegex(ValueError,'própria base'):hair.request(s,self.d)

    def test_failed_processor_does_not_attach_or_change_config(self):
        with patch.object(hair,'invoke',side_effect=ValueError('fixture failure')):
            with self.assertRaisesRegex(ValueError,'failure'):hair.render(s,'one',self.root/'failed')
        self.assertEqual(s.load('one'),self.d);self.assertFalse((self.root/'failed/stage.json').exists())


try:
    import cv2
    import numpy as np
except ImportError: cv2=None


@unittest.skipIf(cv2 is None,'OpenCV is required')
class UpstreamCompositionTests(unittest.TestCase):
    def test_light_hair_and_treated_subject_pixels_are_preserved(self):
        import hair_base
        full=np.full((40,40,3),245,np.uint8)  # Bright foreground must not be reclassified.
        plate=np.full_like(full,80,dtype=np.float32);effect=np.ones((40,40),np.float32)
        effect[10:30,10:30]=0
        result=hair_base.compose(full,plate,effect,np.array([[1,0,0],[0,1,0]],np.float32))
        np.testing.assert_array_equal(result[10:30,10:30],full[10:30,10:30])
        self.assertTrue((result[:5]==80).all())

    def test_bypass_is_exact_even_with_fractional_roi_scale(self):
        import hair_base
        rng=np.random.default_rng(42);full=rng.integers(0,256,(51,35,3),dtype=np.uint8)
        result=hair_base.compose(full,np.full((16,16,3),100,np.float32),np.zeros((16,16),np.float32),np.array([[1.3,0,2.5],[0,1.3,2.5]],np.float32))
        np.testing.assert_array_equal(result,full)
