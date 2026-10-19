import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import studio as s
import storage
from migrate_storage import relocate
import test_studio

class StorageTests(unittest.TestCase):
 setUp=test_studio.StudioTests.setUp
 tearDown=test_studio.StudioTests.tearDown
 save=test_studio.StudioTests.save
 def test_external_roots_and_staging(self):
  roots={k:str(self.root.parent/(self.root.name+'-'+k)) for k in storage.KEYS}
  # use a sibling directory to ensure production-config constraints are exercised
  with tempfile.TemporaryDirectory() as data:
   roots={k:str(Path(data)/k) for k in storage.KEYS}
   s.write(self.root/'studio/storage.json',{'schemaVersion':1,'roots':roots})
   try:
    mid=s.register(self.raw,'original',inspect=False)
    self.assertEqual(s.jobdir('one'),Path(roots['edit'])/'one/project')
    self.assertEqual(s.catalog_path(),Path(roots['edit'])/'_editor/media.json')
    staged=s.stage_file(mid)
    self.assertTrue((s.public_dir()/staged).is_file())
    self.assertFalse((self.root/'public').exists())
    still=self.root/'photo.png';still.write_bytes(b'asset')
    aid=s.register(still,'still',inspect=False)
    self.assertTrue(s.resolve(aid).is_relative_to(Path(roots['assets'])))
    fx=s.register(still,'sfx',inspect=False)
    self.assertTrue(any(Path(p).is_relative_to(Path(roots['soundfx'])) for p in s.registry()['media'][fx]['locations']))
    with self.assertRaises(ValueError):s.output_path(self.root/'out.mp4')
    with self.assertRaises(ValueError):s.output_path(Path(roots['ready'])/'pending.mov')
    with self.assertRaises(ValueError):s.output_path(Path(roots['source'])/'derived.mov')
    with self.assertRaises(ValueError):s.persistent_path(Path(roots['cache'])/'voice.wav')
   finally:(self.root/'studio/storage.json').unlink()
 def test_path_overlap_rejected(self):
  roots={k:str(self.root.parent/'data'/k) for k in storage.KEYS};roots['cache']=roots['edit']+'/cache'
  s.write(self.root/'studio/storage.json',{'schemaVersion':1,'roots':roots})
  with self.assertRaisesRegex(ValueError,'sobrepostas'):s.paths()
 def test_migration_rollback_and_retry(self):
  source=self.root/'old';source.mkdir();(source/'data').write_bytes(b'unchanged')
  other=self.root/'other';other.write_bytes(b'other')
  plan=[(source,self.root/'new'),(other,self.root/'other-new')];journal=self.root/'journal.json'
  with self.assertRaises(RuntimeError):relocate(plan,journal,fail_after=1)
  self.assertEqual((source/'data').read_bytes(),b'unchanged');self.assertTrue(other.exists())
  self.assertEqual(s.read(journal)['state'],'rolled-back')
  relocate(plan,journal)
  self.assertEqual((self.root/'new/data').read_bytes(),b'unchanged')
 def test_collision_preserves_sources(self):
  a=self.root/'a';b=self.root/'b';a.write_bytes(b'a');b.write_bytes(b'b')
  with self.assertRaises(ValueError):relocate([(a,b)],self.root/'journal.json')
  self.assertEqual(a.read_bytes(),b'a');self.assertEqual(b.read_bytes(),b'b')
