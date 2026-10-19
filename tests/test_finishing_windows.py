import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from finishing_windows import select

class WindowTests(unittest.TestCase):
    def setUp(self):
        self.windows=[dict(scene='a',sourceMediaId='original',sourceIn=40,sourceOut=260,packFrom=0),dict(scene='b',sourceMediaId='original',sourceIn=940,sourceOut=1160,packFrom=220)]
        self.p={'fps':60,'scenes':[dict(id='a',clip=dict(mediaId='original',inFrame=100),duration=100),dict(id='b',clip=dict(mediaId='original',inFrame=1000),duration=100)]}
    def test_reorder_keeps_source_offsets(self):
        expected=select(self.windows,self.p)
        self.p['scenes'].reverse()
        self.assertEqual(select(self.windows,self.p),expected)
    def test_extend_and_trim_within_handles(self):
        self.p['scenes'][0]['clip']['inFrame']=40;self.p['scenes'][0]['duration']=220
        self.assertEqual(select(self.windows,self.p)['a'],0)
        self.p['scenes'][0]['clip']['inFrame']=120;self.p['scenes'][0]['duration']=80
        self.assertEqual(select(self.windows,self.p)['a'],80)
    def test_outside_window_rejected(self):
        for start,duration in [(39,100),(100,161)]:
            p=copy.deepcopy(self.p);p['scenes'][0]['clip']['inFrame']=start;p['scenes'][0]['duration']=duration
            with self.assertRaises(ValueError):select(self.windows,p)
    def test_changed_source_rejected(self):
        self.p['scenes'][0]['clip']['mediaId']='other'
        with self.assertRaises(ValueError):select(self.windows,self.p)
    def test_duplicate_and_missing_rejected(self):
        with self.assertRaises(ValueError):select(self.windows*2,self.p)
        with self.assertRaises(ValueError):select(self.windows[:1],self.p)
    def test_frame_rate_change_rejected(self):
        self.p['fps']=30
        with self.assertRaises(ValueError):select(self.windows,self.p)

class SealTests(unittest.TestCase):
    def test_evidence_and_output_identity_are_checked(self):
        import tempfile, json, hashlib
        from types import SimpleNamespace
        from finishing_windows import compiled
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); evidence=root/'report.json';evidence.write_text('{}')
            sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            seal={'version':'finishing-windows-v1','format':[2160,3840,60],'videoMediaId':'treated','windows':[dict(scene='a',sourceMediaId='raw',sourceIn=40,sourceOut=260,packFrom=0)],'evidence':{str(evidence):sha(evidence)}}
            path=root/'sealed.json';path.write_text(json.dumps(seal))
            host=SimpleNamespace(sha=sha,read=lambda p:json.loads(Path(p).read_text()),resolve=lambda mid:mid)
            d={'project.json':{'fps':60,'scenes':[dict(id='a',clip=dict(mediaId='raw',inFrame=100),duration=100)]},'finishing.json':{'windows':{'work':t,'sealSha256':sha(path),'videoMediaId':'treated'}}}
            self.assertEqual(compiled(host,d)['starts'],{'a':60})
            evidence.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'Evidência'):compiled(host,d)
            evidence.write_text('{}');d['finishing.json']['windows']['videoMediaId']='other'
            with self.assertRaisesRegex(ValueError,'Mídia'):compiled(host,d)
            d['finishing.json']['windows']['videoMediaId']='treated';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'Selo'):compiled(host,d)
