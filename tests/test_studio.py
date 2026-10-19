import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import studio as s

class StudioTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=s.ROOT;s.ROOT=self.root
  (self.root/'src').mkdir();(self.root/'src/Root.tsx').write_text('fixture engine')
  self.raw=self.root/'raw.mov';self.raw.write_bytes(b'original');self.proxy=self.root/'proxy.mp4';self.proxy.write_bytes(b'proxy')
  self.mid=s.register(self.raw,'original',inspect=False);self.pid=s.register(self.proxy,'proxy',inspect=False)
  self.d={'project.json':{'schemaVersion':2,'videoId':'one','width':1440,'height':2560,'fps':60,'scenes':[{'id':'a','duration':60,'script':'Teste','clip':{'mediaId':self.mid,'inFrame':120,'proxy':{'mediaId':self.pid,'inFrame':0,'sourceInFrame':120}},'layers':[],'captions':[{'text':'teste','from':4,'duration':20}],'events':[{'id':'gesture','kind':'gesture','frame':12}]}]},'brief.json':{'text':'fixture'},'looks.json':{'options':[]},'style.json':{'layout':{'labels':[],'caption':{'x':0,'y':0,'width':300,'fontSize':40}}},'finishing.json':{'audioGainDb':0}}
  self.save()
 def tearDown(self):s.ROOT=self.old;self.temp.cleanup()
 def save(self):
  for n,d in self.d.items():s.write(s.jobdir('one')/n,d)
 def approve(self,stage):
  e=self.root/(stage+'.json');s.write(e,{'fingerprint':s.fingerprints(self.d)[stage],'notes':'fixture only; no real approval','userApproval':'fixture test','checks':{k:'passed' for k in ('cuts','looks','gestures','captions','stills','visual','audio','color','retouch')}})
  return s.approve('one',stage,e,'test-fixture')
 def approve_all(self):
  for st in s.STAGES:self.approve(st)
 def test_wrong_relink_same_filename(self):
  wrong=self.root/'wrong/raw.mov';wrong.parent.mkdir();wrong.write_bytes(b'wrong')
  with self.assertRaisesRegex(ValueError,'SHA-256'):s.relink(self.mid,wrong)
 def test_offline_and_return(self):
  self.raw.rename(self.root/'renamed.mov')
  self.assertEqual(s.status('one')['media'][0 if s.media_ids(self.d)[0]==self.mid else 1]['state'],'offline')
  s.relink(self.mid,self.root/'renamed.mov');self.assertEqual(s.resolve(self.mid),(self.root/'renamed.mov').resolve())
 def test_snapshot_and_fork_preserve_scene(self):
  rev=s.checkpoint('one','fixture');self.d['project.json']['scenes'][0]['captions'][0]['text']='changed';self.save()
  s.fork('one',rev,'two');self.assertEqual(s.load('two')['project.json']['scenes'][0]['captions'][0]['text'],'teste');self.assertEqual(s.records('two'),[])
 def test_snapshot_tamper_rejected(self):
  rev=s.checkpoint('one','fixture');p=s.jobdir('one')/'revisions'/rev/'snapshot.json';d=s.read(p);d['job']='tampered';s.write(p,d)
  with self.assertRaisesRegex(ValueError,'Snapshot alterado'):s.fork('one',rev,'two')
 def test_audio_change_invalidates_only_post(self):
  self.approve_all();self.d['finishing.json']['audioGainDb']=3;self.save();states=s.status('one')['checkpoints']
  self.assertEqual(states,{'preproduction':'approved','production':'approved','postproduction':'stale'})
 def test_cut_change_invalidates_all(self):
  self.approve_all();self.d['project.json']['scenes'][0]['clip']['inFrame']+=1;self.save();self.assertTrue(all(v=='stale' for v in s.status('one')['checkpoints'].values()))
 def test_evidence_tamper_invalidates(self):
  self.approve('preproduction');(self.root/'preproduction.json').write_text('{}');self.assertEqual(s.status('one')['checkpoints']['preproduction'],'stale')
 def test_approval_without_real_reference_rejected(self):
  e=self.root/'empty.json';s.write(e,{'notes':'no human approval'})
  with self.assertRaises(ValueError):s.approve('one','preproduction',e,'fixture')
 def test_skip_checkpoint_rejected(self):
  with self.assertRaisesRegex(ValueError,'anterior'):self.approve('production')
 def test_master_without_approval_blocked(self):
  with self.assertRaisesRegex(ValueError,'Master bloqueado'):s.render('one',self.root/'master.mov',True)
 def test_cut_only_cannot_be_master(self):
  with self.assertRaisesRegex(ValueError,'exclusivo de prévia'):
   s.render('one',self.root/'master.mov',master=True,cut_only=True)
 def test_engine_change_invalidates_production(self):
  self.approve_all();(self.root/'src/Root.tsx').write_text('different');states=s.status('one')['checkpoints'];self.assertEqual(states['preproduction'],'approved');self.assertEqual(states['production'],'stale')
 def test_assemble_reorder_keeps_local_events(self):
  b=copy.deepcopy(self.d['project.json']['scenes'][0]);b['id']='b';b['captions'][0]['text']='second';self.d['project.json']['scenes'].append(b);self.save();rev=s.checkpoint('one','fixture')
  s.assemble('mix',[f'one:{rev}:b',f'one:{rev}:a']);scenes=s.load('mix')['project.json']['scenes'];self.assertEqual(scenes[0]['captions'][0]['text'],'second');self.assertEqual(scenes[1]['events'][0]['frame'],12)
 def test_compile_reorder_remaps_global_times(self):
  b=copy.deepcopy(self.d['project.json']['scenes'][0]);b['id']='b';self.d['project.json']['scenes'].append(b)
  with patch.object(s,'stage_file',return_value='fixture.mp4'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d)
  self.assertEqual([x['from'] for x in p['captions']],[4,64]);self.assertEqual([x['from'] for x in p['shots']],[0,60])
 def test_proxy_trim_follows_original_offset(self):
  self.d['project.json']['scenes'][0]['clip']['inFrame']=130
  with patch.object(s,'stage_file',return_value='fixture.mp4'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d)
  self.assertEqual(p['shots'][0]['inFrame'],10)
 def test_master_uses_original(self):
  with patch.object(s,'stage_file',return_value='fixture.mp4') as f,patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d,True)
  f.assert_called_with(self.mid);self.assertEqual(p['shots'][0]['inFrame'],120)
 def test_gesture_moves_layer(self):
  self.d['project.json']['scenes'][0]['layers']=[{'id':'coat','mediaId':self.mid,'from':0,'duration':60,'anchor':'gesture','offsetFrames':2}]
  with patch.object(s,'stage_file',return_value='fixture.mp4'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d)
  self.assertEqual(p['scenes'][0]['layers'][0]['from'],14);self.assertEqual(p['scenes'][0]['layers'][0]['duration'],46)
 def test_unknown_anchor_rejected(self):
  self.d['project.json']['scenes'][0]['layers']=[{'anchor':'missing'}];self.assertIn('Âncora inexistente',s.validate_job(self.d))
 def test_mutated_original_not_resolved(self):
  self.raw.write_bytes(b'mutated');self.assertRaises(ValueError,s.resolve,self.mid)


class ReleaseTests(unittest.TestCase):
 setUp=StudioTests.setUp
 tearDown=StudioTests.tearDown
 save=StudioTests.save
 approve=StudioTests.approve
 approve_all=StudioTests.approve_all
 def release_fixture(self):
  self.approve_all();out=self.root/'master.mov';out.write_bytes(b'fixture master');s.write(out.with_suffix('.project.json'),{'fixture':True});s.write(out.with_suffix('.report.json'),{'job':'one','master':True,'revision':'fixture','fingerprints':s.fingerprints(self.d),'outputSha256':s.sha(out),'manifestSha256':s.sha(out.with_suffix('.project.json')),'verification':{'technical_pass':True}})
  e=self.root/'final-evidence.json';s.write(e,{'outputSha256':s.sha(out),'userApproval':'fixture only','notes':'fixture playback','checks':{'visual':'passed','audio':'passed','completePlayback':'passed'}});return out,e
 def test_release_requires_exact_export(self):
  out,e=self.release_fixture();out.write_bytes(b'altered')
  with self.assertRaisesRegex(ValueError,'mudou'):s.release('one',out,e,'fixture')
 def test_release_requires_listening(self):
  out,e=self.release_fixture();d=s.read(e);d['checks']['audio']='not-verified';s.write(e,d)
  with self.assertRaisesRegex(ValueError,'incompleta'):s.release('one',out,e,'fixture')
 def test_valid_release_rechecks_technical_file(self):
  out,e=self.release_fixture()
  with patch.object(s.vh,'verify',return_value={'technical_pass':True}) as verify:r=s.release('one',out,e,'fixture')
  self.assertTrue(verify.called);self.assertEqual(r['outputSha256'],s.sha(out));published=Path(r['publishedOutput']);self.assertEqual(published.read_bytes(),out.read_bytes());self.assertEqual(list(published.parent.iterdir()),[published])
 def test_processed_audio_stale_after_reorder(self):
  self.d['finishing.json'].update(audioMediaId=self.pid,audioEditHash=s.edit_hash(self.d));self.d['project.json']['scenes'][0]['clip']['inFrame']+=1
  with self.assertRaisesRegex(ValueError,'outro corte'):s.compile_job(self.d)
 def test_archive_missing_invalidates_check(self):
  backup=self.root/'backup.mov';backup.write_bytes(self.raw.read_bytes());s.relink(self.mid,backup,True);self.assertTrue(s.archive_check(self.mid)['verifiedCopyAccessible']);backup.unlink();self.assertFalse(s.archive_check(self.mid)['verifiedCopyAccessible'])

class CaptionTests(unittest.TestCase):
 def test_omitting_word_does_not_move_others(self):
  import caption_rules as c
  words=[{'text':'com','from':10,'duration':8},{'text':'azul,','from':20,'duration':12},{'text':'não','from':35,'duration':10}]
  captions=c.build(words,{'omit':['com','não']},['azul']);self.assertEqual([x['text'] for x in captions],['azul','não']);self.assertEqual(captions[0]['from'],20);self.assertTrue(captions[0]['highlight'])


class LookReviewTests(unittest.TestCase):
 tearDown=StudioTests.tearDown
 save=StudioTests.save
 approve=StudioTests.approve
 def setUp(self):
  StudioTests.setUp(self);scene=self.d['project.json']['scenes'][0]
  scene['layers']=[{'id':'girl-top','mediaId':self.mid,'rect':{'x':1}},{'id':'boy-top','mediaId':self.pid,'rect':{'x':2}}]
  scene['looks']=[{'id':'girl','layerIds':['girl-top']},{'id':'boy','layerIds':['boy-top']}];self.save()
 def look_review(self,key):
  e=self.root/(key.replace(':','-')+'.json');s.write(e,{'fingerprint':s.look_fingerprints(self.d)[key],'notes':'fixture only','userApproval':'test fixture','checks':{k:'passed' for k in ('styling','cutout','composition','timing')}});s.review_look('one',key,e,'fixture')
 def test_changed_boy_preserves_girl(self):
  self.look_review('a:girl');self.look_review('a:boy');self.d['project.json']['scenes'][0]['layers'][1]['rect']['x']=9;self.save();states=s.look_status('one');self.assertEqual(states['a:girl']['state'],'approved');self.assertEqual(states['a:boy']['state'],'stale')
 def test_shared_caption_invalidates_both(self):
  self.look_review('a:girl');self.look_review('a:boy');self.d['project.json']['scenes'][0]['captions'][0]['text']='new';self.save();self.assertTrue(all(x['state']=='stale' for x in s.look_status('one').values()))
 def test_individual_reviews_do_not_approve_video(self):
  self.look_review('a:girl');self.look_review('a:boy');self.assertEqual(s.status('one')['checkpoints']['production'],'pending')
 def test_scene_frame_range(self):
  b=copy.deepcopy(self.d['project.json']['scenes'][0]);b['id']='b';self.d['project.json']['scenes'].append(b);self.assertEqual(s.scene_frames(self.d,'b'),'60-119')
 def test_required_look_review_blocks_production(self):
  self.d['project.json']['requireLookReview']=True;self.save();self.approve('preproduction')
  with self.assertRaisesRegex(ValueError,'individuais'):self.approve('production')
 def test_missing_layer_rejected(self):
  self.d['project.json']['scenes'][0]['looks'][0]['layerIds']=['missing'];self.assertRaises(ValueError,s.look_fingerprints,self.d)



 def test_4k_windows_override_proxy_preserve_delivery_and_captions(self):
  with patch.object(s.finishing_windows,'compiled',return_value={'mediaId':'4k','starts':{'a':60}}),patch.object(s,'stage_file',return_value='4k.mov') as stage,patch.object(s.vh,'probe',return_value={'format':{'duration':'10'}}):
   p=s.compile_job(self.d)
  self.assertEqual(p['width'],1440);self.assertEqual(p['height'],2560)
  self.assertEqual(p['shots'][0]['inFrame'],60);self.assertEqual(p['shots'][0]['outFrame'],120)
  self.assertEqual(p['captions'][0]['from'],4);self.assertEqual(stage.call_args_list[0].args,('4k',))
 def test_truncated_window_does_not_fall_back_to_raw(self):
  with patch.object(s.finishing_windows,'compiled',return_value={'mediaId':'4k','starts':{'a':60}}),patch.object(s,'stage_file',return_value='4k.mov'),patch.object(s.vh,'probe',return_value={'format':{'duration':'0.5'}}):
   with self.assertRaisesRegex(ValueError,'truncada'):s.compile_job(self.d)
 def test_base_framing_cannot_expose_edges_or_upscale_beyond_native_reserve(self):
  for base in ({'scale':1,'x':1,'y':0},{'scale':1.6,'x':0,'y':0},{'scale':1.15,'x':0,'y':300},{'scale':float('nan'),'x':0,'y':0}):
   self.d['style.json']['layout']['base']=base
   with self.assertRaisesRegex(ValueError,'Enquadramento'):s.compile_job(self.d)
 def test_base_framing_preserves_source_timing(self):
  self.d['style.json']['layout']['base']={'scale':1.15,'x':0,'y':90}
  before=s.edit_hash(self.d)
  with patch.object(s,'stage_file',return_value='fixture.mp4'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d)
  self.assertEqual(p['layout']['base'],{'scale':1.15,'x':0,'y':90})
  self.assertEqual(s.edit_hash(self.d),before);self.assertEqual(p['durationInFrames'],60)
 def test_guides_preview_only(self):
  self.d['style.json']['layout']['lookGuides']={'top':.14,'bottom':.68}
  with patch.object(s,'stage_file',return_value='fixture.mp4'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):
   preview=s.compile_job(self.d);master=s.compile_job(self.d,True)
  self.assertEqual(preview['previewGuides'],{'safeInset':.06,'lookTop':.14,'lookBottom':.68})
  self.assertIsNone(master['previewGuides'])
 def test_invalid_look_guides_rejected(self):
  for guides in ({'top':.7,'bottom':.2},{'top':.01,'bottom':.7},{'top':.2}):
   self.d['style.json']['layout']['lookGuides']=guides
   with self.assertRaisesRegex(ValueError,'Guias'):s.compile_job(self.d)
 def test_image_labels_are_staged_without_mutating_style(self):
  self.d['style.json']['layout']['labels']=[{'text':'girl','x':200,'y':154,'mediaId':self.mid}]
  before=copy.deepcopy(self.d['style.json'])
  with patch.object(s,'stage_file',return_value='fixture.png'),patch.object(s.vh,'probe',return_value={'format':{'duration':'100'}}):p=s.compile_job(self.d)
  self.assertEqual(p['layout']['labels'][0]['src'],'fixture.png')
  self.assertNotIn('mediaId',p['layout']['labels'][0])
  self.assertEqual(before,self.d['style.json'])

 def test_image_labels_participate_in_media_inventory(self):
  self.d['style.json']['layout']['labels']=[{'mediaId':'label-only'}]
  self.assertIn('label-only',s.media_ids(self.d))
