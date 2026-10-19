import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import caption_rules as c
class CaptionContinuityTests(unittest.TestCase):
 def test_omissions_split_gap_and_preserve_speech(self):
  speech=[{'text':'azul','from':0,'duration':10},{'text':'com','from':10,'duration':8},{'text':'branco','from':20,'duration':10}]
  visible=c.build(speech,{'omit':['com']});original=copy.deepcopy(visible)
  result=c.continuous(visible,40,1)
  self.assertEqual([(x['text'],x['from'],x['duration']) for x in result],[('azul',1,14),('branco',15,25)])
  self.assertEqual(visible,original)
 def test_scene_boundary_coverage(self):
  a=c.continuous([{'text':'azul','from':2,'duration':4}],10,1)
  b=c.continuous([{'text':'preto','from':8,'duration':5}],20)
  covered=[f for x in a for f in range(x['from'],x['from']+x['duration'])]+[10+f for x in b for f in range(x['from'],x['from']+x['duration'])]
  self.assertEqual(covered,list(range(1,30)))
 def test_empty_scene_remains_empty(self):self.assertEqual(c.continuous([],60),[])
