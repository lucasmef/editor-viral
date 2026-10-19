import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import takes_review as t
class TakeChoices(unittest.TestCase):
 def setUp(self):
  self.manifest={'job':'fixture','scenes':[{'id':'one','takes':[{'id':'a'},{'id':'b'}]},{'id':'two','takes':[{'id':'c'}]}]}
 def test_choice_does_not_approve_cut(self):
  r=t.validate_selection({'manifestHash':t.s.digest(self.manifest),'selected':{'one':'b','two':'c'}},self.manifest)
  self.assertTrue(r['complete']);self.assertEqual(r['scope'],'take-choice-only; fine-cut-review-pending');self.assertNotIn('approval',r)
 def test_stale_and_unknown_choices_rejected(self):
  for value in [{'manifestHash':'old','selected':{}},{'manifestHash':t.s.digest(self.manifest),'selected':{'one':'c'}},{'manifestHash':t.s.digest(self.manifest),'selected':{'unknown':'a'}}]:
   with self.assertRaises(ValueError):t.validate_selection(value,self.manifest)
 def test_partial_choice_remains_incomplete(self):
  r=t.validate_selection({'manifestHash':t.s.digest(self.manifest),'selected':{'one':'a'}},self.manifest)
  self.assertFalse(r['complete'])
