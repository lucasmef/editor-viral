import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import look_studio as ls

class LookStudioTests(unittest.TestCase):
 def setUp(self):
  layer={'id':'pants','rect':{'x':100,'y':200,'width':300,'height':600},'mediaId':'original','crop':{'x':2},'from':8,'duration':90,'clipPath':'unchanged'}
  self.d={'project.json':{'width':1440,'height':2560,'scenes':[{'id':'scene','layers':[layer]}]},'style.json':{'guides':.06},'finishing.json':{'4k':'preserved'}}
  self.p={'scenes':[{'layers':[{'id':'scene-pants','rect':copy.deepcopy(layer['rect'])}]}]}
  self.edits=[{'id':'scene-pants','x':110,'y':220,'scale':1.1}]
 def test_move_resize_preserves_media_crops_timing_and_finishing(self):
  result,changes=ls.apply_geometry(self.d,self.p,self.edits)
  actual=result['project.json']['scenes'][0]['layers'][0]
  self.assertEqual(actual['rect'],{'x':110,'y':220,'width':330,'height':660})
  original=self.d['project.json']['scenes'][0]['layers'][0]
  self.assertEqual({k:v for k,v in actual.items() if k!='rect'},{k:v for k,v in original.items() if k!='rect'})
  self.assertEqual(result['finishing.json'],self.d['finishing.json']);self.assertEqual(len(changes),1)
  self.assertEqual(original['rect']['x'],100)
 def test_missing_duplicate_outside_and_nonfinite_rejected(self):
  for edits in [[],self.edits*2,[{**self.edits[0],'scale':float('nan')}],[{**self.edits[0],'x':1400}]]:
   with self.assertRaises(ValueError):ls.apply_geometry(self.d,self.p,edits)
 def test_stale_session_cannot_overwrite_project(self):
  with patch.object(ls.st,'load',return_value={**self.d,'new':'external change'}):
   with self.assertRaisesRegex(ValueError,'fora desta sessão'):ls.save_geometry('x',self.d,self.p,self.edits)
 def test_save_reload_and_undo_preserve_exact_source(self):
  with tempfile.TemporaryDirectory() as root:
   home=Path(root)
   for name,value in self.d.items():ls.st.write(home/name,value)
   def read_job(job):return {name:ls.st.read(home/name) for name in self.d}
   with patch.object(ls.st,'load',side_effect=read_job),patch.object(ls.st,'jobdir',return_value=home):
    saved,count=ls.save_geometry('x',self.d,self.p,self.edits)
    self.assertEqual(count,1);self.assertEqual(saved,read_job('x'))
    restored,count=ls.save_geometry('x',saved,self.p,[{'id':'scene-pants','x':100,'y':200,'scale':1}])
    self.assertEqual(restored,self.d);self.assertEqual(len(list((home/'history').glob('*.json'))),2)
 def test_native_parser_only_accepts_transform_literals(self):
  source='const L=()=> <Interactive.Div data-piece="a" style={{translate:"10px 20px",scale:1,transformOrigin:"0px 0px"}}><span/></Interactive.Div>;'
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'index.tsx';path.write_text(source);a=ls.parse(path)
   path.write_text(source.replace('10px 20px','30px 40px').replace('scale:1','scale:1.2'));b=ls.parse(path)
   self.assertEqual(a['signature'],b['signature']);self.assertEqual(b['layers'][0]['scale'],1.2)
   path.write_text(source.replace('0px 0px','50% 50%'));self.assertNotEqual(a['signature'],ls.parse(path)['signature'])
   path.write_text(source.replace('scale:1','scale:interpolate(frame,[0,2],[1,2])'))
   with self.assertRaises(ValueError):ls.parse(path)
