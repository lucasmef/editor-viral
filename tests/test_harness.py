import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('harness',ROOT/'scripts/video_harness.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old=h.ROOT;h.ROOT=self.root
        (self.root/'public').mkdir();(self.root/'public/video.mov').write_bytes(b'test fixture')
        (self.root/'review.txt').write_text('Fixture only, never production approval')
        im=Image.new('RGBA',(20,20),(0,0,0,0));im.paste((80,20,90,255),(5,5,15,15));im.save(self.root/'public/still.png')
        self.p={'schemaVersion':1,'width':1440,'height':2560,'fps':60,'durationInFrames':60,'timingStatus':'reviewed','layout':{'labels':[],'caption':{'x':100,'y':200,'width':400,'fontSize':40}},'source':None,'shots':[{'src':'video.mov','inFrame':0,'outFrame':60,'from':0}], 'reviews':{s:{'status':'passed','evidence':'review.txt'} for s in ('cuts','timing','stills','captions','visual','audio')},'scenes':[{'id':'one','from':0,'duration':60,'layers':[{'id':'a','src':'still.png','from':0,'duration':60,'rect':{'x':10,'y':10,'width':100,'height':200},'transition':'cut','fadeFrames':0}]}],'captions':[{'text':'azul','from':0,'duration':30}]}
    def tearDown(self): h.ROOT=self.old;self.tmp.cleanup()
    def test_valid_fixture(self): self.assertTrue(h.validate(self.p,True,False)['ready'])
    def test_draft_blocks_master(self):
        self.p['timingStatus']='draft';self.assertFalse(h.validate(self.p,True,False)['ready'])
    def test_missing_asset_is_error(self):
        self.p['scenes'][0]['layers'][0]['src']='missing.png';self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_placeholder_blocks_final(self):
        self.p['scenes'][0]['layers'][0]['src']=None;self.assertFalse(h.validate(self.p,True,False)['ready'])
    def test_cut_gap(self):
        self.p['shots'][0]['from']=1;self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_caption_overlap(self):
        self.p['captions'].append({'text':'marinho','from':20,'duration':30});self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_asset_outside_canvas(self):
        self.p['scenes'][0]['layers'][0]['rect']['x']=1430;self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_atlas_window_outside_source(self):
        self.p['scenes'][0]['layers'][0]['crop']={'x':15,'y':0,'width':10,'height':20,'imageWidth':20,'imageHeight':20}
        self.assertIn('Janela ultrapassa o atlas: a',h.validate(self.p,False,False)['errors'])
    def test_atlas_dimensions_match_image(self):
        self.p['shots']=[]
        self.p['scenes'][0]['layers'][0]['crop']={'x':0,'y':0,'width':20,'height':20,'imageWidth':30,'imageHeight':30}
        self.assertIn('Dimensões do atlas divergentes: still.png',h.validate(self.p,False,True)['errors'])
    def test_wrong_preset(self):
        self.p['fps']=30;self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_path_traversal(self):
        self.p['shots'][0]['src']='../secret.mov';self.assertTrue(h.validate(self.p,True,False)['errors'])
    def test_claimed_review_needs_evidence(self):
        self.p['reviews']['visual']['evidence']='missing.txt';self.assertFalse(h.validate(self.p,True,False)['ready'])
    def test_opaque_png_rejected(self):
        Image.new('RGB',(20,20),'red').save(self.root/'public/still.png');self.p['shots']=[]
        self.assertIn('Still sem transparência útil: still.png',h.validate(self.p,True,True)['errors'])
    def test_fully_transparent_png_rejected(self):
        Image.new('RGBA',(20,20),(0,0,0,0)).save(self.root/'public/still.png');self.p['shots']=[]
        self.assertTrue(h.validate(self.p,True,True)['errors'])
    def test_empty_renderer_is_not_ready(self):
        h.ROOT=ROOT;p=json.loads((ROOT/'src/empty-project.json').read_text());r=h.validate(p,True,False)
        self.assertFalse(r['ready']);self.assertTrue(r['pending']);self.assertIn('Cenas não cobrem a duração do projeto',r['errors'])

if __name__=='__main__':unittest.main()
