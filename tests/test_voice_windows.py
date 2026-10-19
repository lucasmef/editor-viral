import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from voice_windows import sample_range
class Handles(unittest.TestCase):
 def test_trim_inside_window_retains_exact_source_samples(self):
  w={'sourceMediaId':'m-a','sourceIn':100,'sourceOut':400}
  sc={'clip':{'mediaId':'m-a','inFrame':130},'duration':150}
  self.assertEqual(sample_range(w,sc),(24000,144000))
  sc['clip']['inFrame']=100;sc['duration']=300
  self.assertEqual(sample_range(w,sc),(0,240000))
 def test_reject_unavailable_handle_or_wrong_source(self):
  w={'sourceMediaId':'m-a','sourceIn':100,'sourceOut':400}
  for mid,a,n in [('m-b',130,150),('m-a',99,150),('m-a',130,271)]:
   with self.assertRaises(ValueError):sample_range(w,{'clip':{'mediaId':mid,'inFrame':a},'duration':n})
