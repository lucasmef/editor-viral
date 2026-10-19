import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render_finishing import compile_finishing
class Host:
 def stage_file(self,mid):return 'media/'+mid+'.wav'
class FinishingTests(unittest.TestCase):
 def setUp(self):self.p={'scenes':[{'id':'b','duration':60},{'id':'a','duration':90}]}
 def test_cue_follows_scene_after_reorder(self):
  cue={'scene':'a','frame':12,'duration':20,'mediaId':'click','gainDb':-20}
  self.assertEqual(compile_finishing(Host(),self.p,{'soundEffects':[cue]})[0][0]['from'],72)
  self.p['scenes'].reverse()
  self.assertEqual(compile_finishing(Host(),self.p,{'soundEffects':[cue]})[0][0]['from'],12)
 def test_invalid_time_gain_and_scene_rejected(self):
  base={'scene':'a','frame':12,'duration':20,'mediaId':'click','gainDb':-20}
  for change in [{'scene':'missing'},{'frame':90},{'duration':200},{'gainDb':float('nan')},{'gainDb':4}]:
   with self.assertRaises(ValueError):compile_finishing(Host(),self.p,{'soundEffects':[{**base,**change}]})
 def test_unknown_or_nonfinite_grade_rejected(self):
  for grade in [{'gamma':1},{'contrast':float('nan')},{'saturation':3},{'warmth':-.1},{'warmth':.5}]:
   with self.assertRaises(ValueError):compile_finishing(Host(),self.p,{'colorGrade':grade})
 def test_warmth_is_optional_and_preserved(self):
  self.assertEqual(compile_finishing(Host(),self.p,{'colorGrade':{'warmth':.055}})[1],{'warmth':.055})
  self.assertEqual(compile_finishing(Host(),self.p,{})[1],{})
if __name__=='__main__':unittest.main()

class PreviewScaleTests(unittest.TestCase):
 def test_preview_scale_does_not_bypass_master_gate(self):
  import studio as s
  with self.assertRaisesRegex(ValueError,'exclusiva de prévia'):s.render('missing',None,master=True,preview_scale=1)
 def test_invalid_scale_rejected_before_loading_job(self):
  import studio as s
  with self.assertRaisesRegex(ValueError,'Escala de prévia inválida'):s.render('missing',None,preview_scale=2)
