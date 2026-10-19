import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import studio_native as n
import look_studio as ls
class NativeStudioTests(unittest.TestCase):
 def setUp(self):
  self.layer={'id':'coat','mediaId':'m-original','from':3,'duration':97,'rect':{'x':20,'y':30,'width':200,'height':300},'crop':{'x':4,'y':5,'width':200,'height':300,'imageWidth':400,'imageHeight':600},'clipPath':'polygon(0 0,100% 0,100% 100%)','transition':'cut','fadeFrames':0,'label':'coat','color':'transparent'}
  self.d={'project.json':{'width':1440,'height':2560,'scenes':[{'id':'s','duration':100,'layers':[self.layer],'looks':[{'id':'girl','layerIds':['coat']}]}]},'finishing.json':{'videoMediaId':'4k'}}
  view={**self.layer,'id':'s-coat','src':'a.png'};view.pop('mediaId')
  self.p={'videoId':'test','width':1440,'height':2560,'fps':60,'durationInFrames':100,'scenes':[{'id':'s','from':0,'duration':100,'layers':[view]}],'_nativeOriginal':copy.deepcopy(self.d['project.json'])}
 def source(self,tmp):return ls.generate(self.p,Path(tmp),'status.json')
 def test_crop_transforms_timing_reopen_and_undo(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=self.source(tmp);initial=n.parse(path);edited=copy.deepcopy(initial)
   props=edited['layers'][0]['props'];props.update({'cropTop':.11,'cropLeft':.03,'from':5,'durationInFrames':90,'hidden':False,'playbackRate':1})
   props['style'].update(rotate='12deg',scale='1.2 0.9',opacity=.7,transformOrigin='50% 50%',translate='44px 55px')
   saved=n.apply(self.d,self.p,initial,edited);l=saved['project.json']['scenes'][0]['layers'][0]
   self.assertEqual(l['crop'],self.layer['crop']);self.assertEqual(l['clipPath'],self.layer['clipPath']);self.assertEqual(saved['finishing.json'],self.d['finishing.json'])
   self.assertEqual(l['native']['props']['cropTop'],.11);self.assertEqual(l['from'],5)
   reopened=copy.deepcopy(self.p);reopened['scenes'][0]['layers']=[{**l,'id':'s-coat','src':'a.png'}];reopened['scenes'][0]['layers'][0].pop('mediaId')
   path=ls.generate(reopened,Path(tmp),'status.json');again=n.parse(path)
   self.assertEqual(again['layers'][0]['props'],props)
   restored=n.apply(saved,self.p,initial,initial);self.assertNotIn('cropTop',restored['project.json']['scenes'][0]['layers'][0]['native']['props'])
 def test_delete_duplicate_and_undo_restore_look_membership(self):
  with tempfile.TemporaryDirectory() as tmp:
   initial=n.parse(self.source(tmp));dupe={'layers':initial['layers']*2}
   saved=n.apply(self.d,self.p,initial,dupe);self.assertEqual(saved['project.json']['scenes'][0]['looks'][0]['layerIds'],['coat','coat-copy-2'])
   deleted=n.apply(saved,self.p,initial,{'layers':[]});self.assertEqual(deleted['project.json']['scenes'][0]['layers'],[])
   restored=n.apply(deleted,self.p,initial,initial);self.assertEqual(restored['project.json']['scenes'][0]['looks'][0]['layerIds'],['coat'])
 def test_native_expressions_roundtrip_and_execution_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=self.source(tmp);source=path.read_text();source=source.replace('"scale":1,','"scale":interpolate(useCurrentFrame(),[0,30],[1,1.2],{extrapolateRight:"clamp"}),')
   path.write_text(source);parsed=n.parse(path);expr=parsed['layers'][0]['props']['style']['scale'];self.assertEqual(expr['$expr'],'call')
   self.assertIn('interpolate(',n.expression(expr))
   path.write_text(source.replace('interpolate(useCurrentFrame(),[0,30],[1,1.2],{extrapolateRight:"clamp"})','fetch("https://invalid")'))
   with self.assertRaises(ValueError):n.parse(path)
 def test_asset_change_and_cross_scene_timing_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   initial=n.parse(self.source(tmp));ed=copy.deepcopy(initial);ed['layers'][0]['assetSignature']='different'
   with self.assertRaises(ValueError):n.apply(self.d,self.p,initial,ed)
   ed=copy.deepcopy(initial);ed['layers'][0]['props']['durationInFrames']=500
   with self.assertRaises(ValueError):n.apply(self.d,self.p,initial,ed)
