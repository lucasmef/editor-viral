import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import studio as s
import face_connector as fc
import test_studio as shared

class FaceConnectorTests(unittest.TestCase):
    setUp=shared.StudioTests.setUp
    tearDown=shared.StudioTests.tearDown
    save=shared.StudioTests.save

    def run_fixture(self):
        work=self.root/'run';work.mkdir()
        (work/'base.mov').write_bytes(b'base')
        self.ep={k:self.root/('engine-'+k) for k in ['python','runner','ffmpeg','backend','shader','library','preset']}
        for k,p in self.ep.items():p.write_text(k)
        m={'version':fc.VERSION,'binding':fc.binding(s,'one'),'connectorSha256':s.sha(fc.__file__),
           'baseSha256':s.sha(work/'base.mov'),'engineRoot':str(self.root),
           'engineHashes':{k:s.sha(v)for k,v in self.ep.items()}}
        s.write(work/'base.json',m)
        return work,m

    def test_original_not_proxy_or_previous_finish(self):
        b=fc.binding(s,'one');self.assertEqual(b['segments'][0]['mediaId'],self.mid)
        self.assertNotIn('layers',b);self.assertNotIn('audioGainDb',b)

    def test_current_rejects_changed_source_bytes(self):
        w,m=self.run_fixture();self.raw.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'modificada'):fc.current(s,'one',w)

    def test_same_duration_reorder_rejected(self):
        scene=copy.deepcopy(self.d['project.json']['scenes'][0]);scene['id']='b';scene['clip']['inFrame']=300
        self.d['project.json']['scenes'].append(scene);self.save();w,m=self.run_fixture()
        self.d['project.json']['scenes'].reverse();self.save()
        with self.assertRaisesRegex(ValueError,'corte'):fc.current(s,'one',w)

    def test_resolution_change_rejected(self):
        w,m=self.run_fixture();self.d['project.json']['width']=720;self.save()
        with self.assertRaisesRegex(ValueError,'formato'):fc.current(s,'one',w)

    def test_overlay_or_audio_change_does_not_change_base(self):
        w,m=self.run_fixture();self.d['project.json']['scenes'][0]['captions'][0]['text']='new'
        self.d['finishing.json']['audioGainDb']=3;self.save()
        with patch.object(fc,'engine_paths',return_value=self.ep):fc.current(s,'one',w)

    def test_base_tamper_rejected(self):
        w,m=self.run_fixture();(w/'base.mov').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Base alterada'):fc.current(s,'one',w)

    def test_engine_change_rejected(self):
        w,m=self.run_fixture();self.ep['shader'].write_text('changed')
        with patch.object(fc,'engine_paths',return_value=self.ep),self.assertRaisesRegex(ValueError,'Motor mudou'):fc.current(s,'one',w)

    def test_existing_work_refused_without_subprocess(self):
        w,m=self.run_fixture()
        with patch.object(fc,'invoke')as run,self.assertRaisesRegex(ValueError,'já existe'):fc.base(s,'one',w)
        run.assert_not_called()

    def test_unreviewed_template_cannot_start_analysis(self):
        w,m=self.run_fixture();r=self.root/'review.json'
        s.write(r,{'sourceSha256':m['baseSha256'],**{k:m['binding'][k]for k in ('width','height','frames','fps')},'reviewed':False})
        with patch.object(fc,'engine_paths',return_value=self.ep),patch.object(fc,'invoke')as run,self.assertRaisesRegex(ValueError,'pendente'):fc.prepare(s,'one',w,r)
        run.assert_not_called()

    def test_review_for_other_source_rejected(self):
        w,m=self.run_fixture();r=self.root/'review.json';s.write(r,{'sourceSha256':'other'})
        with patch.object(fc,'engine_paths',return_value=self.ep),self.assertRaisesRegex(ValueError,'outra base'):fc.prepare(s,'one',w,r)

    def test_review_cannot_omit_scene_cut(self):
        w,m=self.run_fixture();r=self.root/'review.json';s.write(r,{'sourceSha256':m['baseSha256'],**{k:m['binding'][k]for k in ('width','height','frames','fps')},'reviewed':True,'reviewNotes':'fixture','cuts':[]})
        with patch.object(fc,'engine_paths',return_value=self.ep),self.assertRaisesRegex(ValueError,'omite corte'):fc.prepare(s,'one',w,r)

    def test_gpu_failure_never_falls_back_or_attaches(self):
        w,m=self.run_fixture()
        with patch.object(fc,'analysis_current',return_value=(m,self.ep,{})),patch.object(fc,'invoke',side_effect=ValueError('GPU unavailable'))as run,patch.object(s,'attach_finish')as attach:
            with self.assertRaisesRegex(ValueError,'GPU'):fc.render(s,'one',w)
        self.assertEqual(len(run.call_args_list),1);self.assertIn('doctor',run.call_args.args[0]);attach.assert_not_called();self.assertFalse((w/'treated.mov').exists())

    def test_processed_video_preserves_treated_audio(self):
        self.d['finishing.json'].update(audioMediaId=self.pid,audioEditHash=s.edit_hash(self.d),audioGainDb=0)
        self.save()
        with patch.object(s,'register',return_value=self.mid):s.attach_finish('one','video',self.raw,'fixture')
        after=s.load('one')['finishing.json'];self.assertEqual(after['audioMediaId'],self.pid);self.assertEqual(after['audioGainDb'],0)
        self.assertEqual(s.status('one')['checkpoints']['preproduction'],'pending')

    def test_audio_attach_retains_video_binding(self):
        self.d['finishing.json']['videoConnector']={'fixture':'binding'};self.save()
        with patch.object(s,'register',return_value=self.pid):s.attach_finish('one','audio',self.raw,'fixture')
        self.assertEqual(s.load('one')['finishing.json']['videoConnector'],{'fixture':'binding'})

    def test_generic_video_replacement_clears_old_binding(self):
        self.d['finishing.json']['videoConnector']={'fixture':'old'};self.save()
        with patch.object(s,'register',return_value=self.pid):s.attach_finish('one','video',self.raw,'fixture')
        self.assertNotIn('videoConnector',s.load('one')['finishing.json'])

    def test_cache_tamper_rejected_before_render(self):
        w,m=self.run_fixture();a=w/'analysis';a.mkdir();(a/'tracking.npz').write_bytes(b'valid')
        s.write(a/'analysis.json',{'files':{'tracking.npz':s.sha(a/'tracking.npz')}})
        s.write(w/'prepared.json',{'baseManifestSha256':s.sha(w/'base.json'),'analysisSha256':s.sha(a/'analysis.json')})
        (a/'tracking.npz').write_bytes(b'tamper')
        with patch.object(fc,'engine_paths',return_value=self.ep),self.assertRaisesRegex(ValueError,'Cache adulterado'):fc.analysis_current(s,'one',w)

    def test_failed_runner_has_persistent_log_and_no_success(self):
        with self.assertRaisesRegex(ValueError,'falhou'):fc.invoke([sys.executable,'-c','raise SystemExit(2)'],self.root/'runner.log')
        self.assertTrue((self.root/'runner.log').is_file())

    def test_report_cannot_claim_cpu_fallback(self):
        w,m=self.run_fixture();s.write(w/'treated.report.json',{'version':'editor-metal-F5-v1','backend':'cpu','device':'CPU'})
        with patch.object(fc,'analysis_current',return_value=(m,self.ep,{})),self.assertRaisesRegex(ValueError,'Metal real'):fc.verified_report(s,'one',w)

    def test_attach_requires_temporal_review_before_mutation(self):
        w,m=self.run_fixture();out=w/'treated.mov';out.write_bytes(b'video');s.write(w/'treated.report.json',{})
        s.write(w/'verified.json',{'reportSha256':s.sha(w/'treated.report.json'),'outputSha256':s.sha(out),'compareCPU':True})
        r={'outputSha256':s.sha(out)};e=self.root/'temporal.json'
        s.write(e,{'outputSha256':s.sha(out),'baseSha256':m['baseSha256'],'editHash':m['binding']['editHash'],'reviewed':False})
        with patch.object(fc,'verified_report',return_value=(m,r,{})),patch.object(s,'attach_finish')as attach,self.assertRaisesRegex(ValueError,'pendente'):fc.attach(s,'one',out,'fixture',w,e)
        attach.assert_not_called()

    def test_attached_report_tamper_invalidates_compile(self):
        w,m=self.run_fixture();rp=w/'treated.report.json';s.write(rp,{'outputSha256':'x'});e=self.root/'temporal.json';s.write(e,{})
        self.d['finishing.json'].update(videoMediaId=self.mid,videoEditHash=s.edit_hash(self.d),videoConnector={'binding':m['binding'],'work':str(w),'reportSha256':s.sha(rp),'temporalReview':str(e),'temporalReviewSha256':s.sha(e)})
        s.write(rp,{'changed':True})
        with self.assertRaisesRegex(ValueError,'Evidência Metal'):s.compile_job(self.d)

if __name__=='__main__':unittest.main()
