import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import hair_controls as h
import hair_finish as finish
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None


class ControlContractTests(unittest.TestCase):
    def setUp(self):
        self.cache = dict(cacheId='fixture', scenes=[dict(id='scene', frames=100, background={})])
        self.config = dict(schemaVersion=1,cacheId='fixture',defaults={},scenes={})

    def test_unknown_control_is_not_silently_ignored(self):
        self.config['defaults']['alpha']={'feathrePx':2}
        with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_reversed_levels_and_nonfinite_values_rejected(self):
        for a in ({'black':.7,'white':.3},{'gamma':float('nan')},{'offsetPx':float('inf')},{'protectOpaque':1}):
            self.config['defaults']['alpha']=a
            with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_wrong_cache_rejected(self):
        self.config['cacheId']='other'
        with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_background_cannot_follow_head_through_intervals(self):
        self.config['scenes']['scene']={'intervals':[{'from':10,'to':20,'background':{'donorOffsetNative':[3,4]}}]}
        with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_interval_fades_cannot_overlap(self):
        self.config['scenes']['scene']={'intervals':[{'from':20,'to':30,'fadeFrames':10},{'from':35,'to':45,'fadeFrames':10}]}
        with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_interval_scene_bounds(self):
        self.config['scenes']['scene']={'bypass':[{'from':90,'to':101}]}
        with self.assertRaises(ValueError):h.validate_config(self.config,self.cache)

    def test_cut_fingerprint_ignores_captions_but_detects_trim_order(self):
        p={'fps':60,'scenes':[{'id':'a','duration':10,'clip':{'mediaId':'m-x','inFrame':3},'captions':[]}, {'id':'b','duration':15,'clip':{'mediaId':'m-x','inFrame':30}}]}
        first=h.digest(h.edit_binding(p));p['scenes'][0]['captions']=[{'text':'new'}]
        self.assertEqual(first,h.digest(h.edit_binding(p)))
        p['scenes'].reverse();self.assertNotEqual(first,h.digest(h.edit_binding(p)))

    def test_half_open_bypass_and_fades(self):
        e={'from':20,'to':30,'fadeFrames':3}
        self.assertEqual(h.interval_weight(20,e),1);self.assertEqual(h.interval_weight(29,e),1)
        self.assertLess(h.interval_weight(30,e),1);self.assertEqual(h.interval_weight(33,e),0)
        self.assertEqual(h.interval_weight(16,e),0)
        self.assertLess(h.interval_weight(17,e),h.interval_weight(18,e))

    def test_intensity_and_alpha_inherit_at_each_level(self):
        self.config['defaults']={'alpha':{'gamma':1.2},'intensity':.7}
        self.config['scenes']['scene']={'alpha':{'offsetPx':2},'intervals':[{'from':20,'to':30,'alpha':{'featherPx':1}}]}
        s=h.validate_config(self.config,self.cache)['scene']
        self.assertEqual(s['intervals'][0]['alpha']['gamma'],1.2)
        self.assertEqual(s['intervals'][0]['alpha']['offsetPx'],2)
        self.assertEqual(s['intervals'][0]['intensity'],.7)

    def test_partial_requires_known_scene(self):
        for sid,frames in [(None,'0:5'),('bad',None),('scene','99:101')]:
            with self.assertRaises(ValueError):finish.selection(self.cache,sid,frames)

    def test_modified_cached_asset_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'alpha';p.write_bytes(b'original');a=finish.resource_file(p,Path(d));p.write_bytes(b'changed')
            with self.assertRaises(ValueError):finish.verify_asset(a)


@unittest.skipUnless(cv2 is not None,'Numerical tests require the documented OpenCV hair environment')
class MaskBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.raw=np.zeros((48,64),np.float32);self.raw[12:36,16:48]=1

    def test_accepted_feather_keeps_highlight_and_matches_v11(self):
        self.raw[12,16:20]=[.82,.9,.96,1]
        expected=np.maximum(self.raw,cv2.GaussianBlur(self.raw,(5,5),.6,borderType=cv2.BORDER_REPLICATE))
        out=h.adjust_alpha(self.raw,h.ALPHA)
        np.testing.assert_array_equal(out,expected)
        self.assertTrue(np.all(out>=self.raw))

    def test_expansion_and_contraction_have_correct_direction(self):
        base=h.alpha_settings({'featherPx':0,'protectOpaque':False})
        expand=h.adjust_alpha(self.raw,{**base,'offsetPx':2})
        contract=h.adjust_alpha(self.raw,{**base,'offsetPx':-2})
        self.assertGreater(expand.sum(),self.raw.sum());self.assertLess(contract.sum(),self.raw.sum())

    def test_fractional_offset_between_integer_offsets(self):
        base=h.alpha_settings({'featherPx':0,'protectOpaque':False})
        half=h.adjust_alpha(self.raw,{**base,'offsetPx':.5});one=h.adjust_alpha(self.raw,{**base,'offsetPx':1})
        self.assertTrue(np.all(half>=self.raw));self.assertTrue(np.all(half<=one));self.assertTrue(np.any((half>0)&(half<1)))

    def test_levels_gamma_and_opaque_protection(self):
        raw=np.array([[0,.25,.5,.75,1]],np.float32)
        out=h.adjust_alpha(raw,h.alpha_settings({'black':.25,'white':.75,'gamma':2,'featherPx':0}))
        np.testing.assert_allclose(out,[[0,0,np.sqrt(.5),1,1]],atol=1e-6)
        protected=h.adjust_alpha(self.raw,h.alpha_settings({'offsetPx':-3,'featherPx':0}))
        np.testing.assert_array_equal(protected[self.raw==1],1)

    def test_manual_protection_is_final_even_with_contraction(self):
        protect=np.zeros_like(self.raw);protect[10:20,12:22]=1
        out=h.adjust_alpha(self.raw,h.alpha_settings({'offsetPx':-4,'protectOpaque':False}),protect)
        self.assertTrue(np.all(out[protect==1]==1))

    def test_symmetric_feather_is_distinct_and_raw_is_immutable(self):
        before=self.raw.copy();out=h.adjust_alpha(self.raw,h.alpha_settings({'featherMode':'symmetric','protectOpaque':False}))
        self.assertLess(out[12,16],1);np.testing.assert_array_equal(self.raw,before)

    def test_bypass_exact_and_ramp_local_to_scene(self):
        cfg=h.validate_config({'schemaVersion':1,'cacheId':'x','scenes':{'s':{'bypass':[{'from':5,'to':10,'fadeFrames':2}]} }},
                              {'cacheId':'x','scenes':[{'id':'s','frames':20}]})['s']
        a,strength=h.frame_controls(self.raw,cfg,6);self.assertEqual(strength,0)
        self.assertEqual(h.frame_controls(self.raw,cfg,0)[1],1)
        yy,xx=np.mgrid[:48,:64].astype(np.float32);image=np.full((48,64,3),50,np.uint8);donor=np.full_like(image,200)
        out,_,_=h.composite(image,donor,a,np.ones_like(a),strength,(xx,yy),h.BACKGROUND)
        np.testing.assert_array_equal(out,image)

    def test_patch_feather_has_zero_canvas_boundary(self):
        raw=np.zeros((48,64),np.float32);raw[1:30,1:40]=1
        out=h.prepare_patch(raw,h.background_settings({'featherPx':4}))
        self.assertEqual(max(out[0].max(),out[-1].max(),out[:,0].max(),out[:,-1].max()),0)

    def test_donor_coverage_rejects_large_translation(self):
        s={'roi':[0,0,64,48],'alphaSize':[64,48],'donorRoi':[0,0,64,48],'donorSize':[64,48]}
        with self.assertRaises(ValueError):h.donor_maps(s,h.background_settings({'donorOffsetNative':[50,0]}),self.raw)

    def test_opacity_and_rgb_are_independent_of_bright_hair(self):
        image=np.full((48,64,3),245,np.uint8);donor=np.zeros_like(image);yy,xx=np.mgrid[:48,:64].astype(np.float32)
        out,_,_=h.composite(image,donor,self.raw,np.ones_like(self.raw),1,(xx,yy),h.BACKGROUND)
        np.testing.assert_array_equal(out[self.raw==1],image[self.raw==1])

    def test_background_rgb_channel_order_and_subject_protection(self):
        image=np.full((48,64,3),30,np.uint8);donor=np.full_like(image,100)
        yy,xx=np.mgrid[:48,:64].astype(np.float32)
        cfg=h.background_settings({'gainRgb':[1.2,1, .8],'offsetRgb':[10,0,-10]})
        out,_,_=h.composite(image,donor,self.raw,np.ones_like(self.raw),1,(xx,yy),cfg)
        np.testing.assert_array_equal(out[0,0],[70,100,130])
        np.testing.assert_array_equal(out[self.raw==1],image[self.raw==1])


if __name__=='__main__':unittest.main()
