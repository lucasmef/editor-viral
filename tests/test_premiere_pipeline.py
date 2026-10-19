import base64
import gzip
import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as E
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import studio as s
import editor_state as state
import premiere_package as package
import premiere_titles as titles
from pipeline_cache import Metrics, ProbeCache, cached_build, copy_asset, sha
from cutout_contract import validate_cutout
import scene_review

ROOT=Path(__file__).resolve().parents[1]

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data=b'original'):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
    def identity(self,p):return {'path':str(p),'sha256':sha(p)}
    def test_cache_reuse_invalidation_and_failed_build(self):
        p=self.file('source');calls=[];metrics=Metrics()
        def build(dest):calls.append(1);dest.write_bytes(p.read_bytes()+b' derived')
        a=cached_build(self.root/'cache',{'version':1},[p],'.bin',build,metrics)
        self.assertEqual(a,cached_build(self.root/'cache',{'version':1},[p],'.bin',build,metrics));self.assertEqual(len(calls),1)
        a.write_bytes(b'corrupt')
        cached_build(self.root/'cache',{'version':1},[p],'.bin',build,metrics);self.assertEqual(len(calls),2)
        p.write_bytes(b'new source')
        b=cached_build(self.root/'cache',{'version':1},[p],'.bin',build,metrics);self.assertNotEqual(a,b)
        def fail(dest):dest.write_bytes(b'partial');raise RuntimeError()
        with self.assertRaises(RuntimeError):cached_build(self.root/'cache',{'version':2},[p],'.bin',fail)
        self.assertFalse(list((self.root/'cache').glob('*.lock')))
        self.assertTrue(any(e['stage']=='cache-hit' for e in metrics.events))
    def test_probe_only_once_per_file_and_copy_no_basename_collision(self):
        a=self.file('a/voice.wav',b'a');b=self.file('b/voice.wav',b'b');calls=[]
        probe=ProbeCache(lambda p:calls.append(str(p)) or {'duration':1})
        probe(a);probe(a);probe(b);self.assertEqual(len(calls),2)
        self.assertNotEqual(copy_asset(a,self.root/'media'),copy_asset(b,self.root/'media'))
    def test_real_approved_title_unicode_and_binary_metadata(self):
        source=ROOT/'studio/templates/premiere/palavra-101-v1.mogrt'
        before=titles.inspect_title(source)
        out=self.root/'test.mogrt';titles.make_title(source,'azul-claro çã',False,out)
        after=titles.inspect_title(out)
        self.assertEqual(after['mStyleSheet']['mText'],'azul-claro çã');self.assertFalse(after['mShadowVisible'])
        self.assertEqual(before['mStyleSheet']['mFontName'],after['mStyleSheet']['mFontName'])
        def attrs(path):
            outer=titles.unzip(path.read_bytes());inner=titles.unzip(outer['project.prgraphic']);root=E.fromstring(gzip.decompress(next(v for k,v in inner.items() if k.endswith('.prproj'))))
            return [e.attrib for e,_ in titles.text_nodes(root)]
        self.assertEqual(attrs(source),attrs(out))
    def test_xml_links_geometry_stereo_and_scene_id(self):
        clips=[]
        for kind in ('video','audio'):
            c=dict(id=kind,name=kind,path=str(self.file(kind+'.mov')),kind=kind,track=0,start=0,duration=60,sourceFrames=180,sourceIn=60,pair='s1')
            if kind=='video':c.update(size=[2160,3840],motion={'scale':66.66666667,'position':[720,1280]})
            clips.append(c)
        p=dict(job='fixture',fps=60,width=1440,height=2560,durationInFrames=60,clips=clips)
        xml=self.root/'out.xml';package.write_xml(p,xml);root=E.parse(xml)
        self.assertEqual(root.find('sequence').get('id'),'sequence-fixture')
        for c in root.findall('.//clipitem'):
            self.assertEqual(c.findtext('in'),'60');self.assertEqual(c.findtext('out'),'120');self.assertEqual(len(c.findall('link')),3)
        self.assertEqual(root.find('.//audio/track/clipitem').get('premiereChannelType'),'stereo')
        self.assertEqual(len(root.findall('.//sequence/media/audio/track')),2)
    def test_cutout_rejects_downsample_and_missing_editable_mask(self):
        original=self.root/'original.png';Image.new('RGB',(100,200),'red').save(original)
        mask=self.root/'mask.png';Image.new('L',(100,200),128).save(mask)
        out=self.root/'piece.png';Image.new('RGBA',(100,200),(255,0,0,128)).save(out)
        p={'pngSha256':sha(out),'original':{**self.identity(original),'pixelSize':[100,200]},'resampled':False,'recovery':{'kind':'separate-mask','pixels':self.identity(original),'mask':self.identity(mask)}}
        self.assertTrue(validate_cutout(out,p)['recoverable'])
        Image.new('RGBA',(50,100)).save(out);p['pngSha256']=sha(out)
        with self.assertRaisesRegex(ValueError,'downsampled'):validate_cutout(out,p)
        Image.new('RGBA',(100,200)).save(out);p['pngSha256']=sha(out);p['recovery']['kind']='alpha-only'
        with self.assertRaisesRegex(ValueError,'cannot restore'):validate_cutout(out,p)
    def test_scene_review_progression_and_front_geometry(self):
        frame=self.root/'frame.png';ref=self.root/'reference.png';Image.new('RGB',(100,200),'gray').save(frame);Image.new('RGBA',(20,40),'red').save(ref)
        asset={**self.identity(ref),'rect':dict(x=10,y=20,width=20,height=40)}
        plan={'canvas':[100,200],'scenes':[{'id':'scene1','duration':60,'frame':self.identity(frame),'reference':asset,'layers':[{**asset,'id':'base','from':10,'to':60}],'regions':[{'name':'waist','box':[10,20,30,40]}]}]}
        f=self.root/'plan.json';s.write(f,plan)
        result=scene_review.build(f,self.root/'review');self.assertEqual(result['scenes'][0]['frames'],[0,9,10,59]);self.assertFalse(result['approved'])
        self.assertEqual(result['scenes'][0]['meanAbsoluteRGBDifference'],[0,0,0])
        plan['scenes'][0]['layers'].append({**asset,'id':'front','from':10,'to':60,'pairedBase':'base','rect':dict(x=11,y=20,width=20,height=40)})
        s.write(f,plan)
        with self.assertRaisesRegex(ValueError,'shared canvas'):scene_review.build(f,self.root/'review2')
    def test_release_rejects_other_file_and_changed_dependencies(self):
        master=self.file('master.mov');proj=self.file('test.prproj');dep=self.file('source.wav');deps=self.root/'deps.json';s.write(deps,{'files':[self.identity(dep)]})
        export=self.file('export.json',b'{}');pack=self.file('package.json',b'{}');review=self.file('review.json',b'{}');handoff=self.root/'handoff.json';s.write(handoff,{'package':self.identity(pack),'evidence':self.identity(review)})
        r={'producer':'premiere','job':'fixture','verification':{'technical_pass':True},'output':self.identity(master),'project':self.identity(proj),'dependencies':self.identity(deps),'exportEvidence':self.identity(export),'handoff':self.identity(handoff),'durationFrames':60}
        candidate=self.root/'candidate.json';s.write(candidate,r)
        evidence=self.root/'approval.json';e={'userApproval':'approved exact file','reviewer':'fixture','notes':'test','checks':{k:'passed' for k in state.FINAL_CHECKS},'outputSha256':'wrong','candidateSha256':sha(candidate)};s.write(evidence,e)
        with self.assertRaisesRegex(ValueError,'outro arquivo'):state.release_candidate('fixture',candidate,evidence)
        e['outputSha256']=sha(master);s.write(evidence,e);dep.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'alterado'):state.release_candidate('fixture',candidate,evidence)
    def test_candidate_and_release_use_external_provenance_and_exact_file(self):
        home=self.root/'job';project=self.file('fixture.prproj');master=self.file('master.mov');media=self.file('source.wav');package_file=self.file('package.json',b'{}')
        handoff_evidence=self.root/'handoff-review.json'
        s.write(handoff_evidence,{'userApproval':'fixture authorization','reviewer':'test','notes':'synthetic','checks':{k:'passed' for k in state.TRANSFER_CHECKS},'projectSha256':sha(project),'packageSha256':sha(package_file),'sequenceId':'seq'})
        deps=self.root/'dependencies.json';s.write(deps,{'files':[self.identity(media)]})
        export=self.root/'export.json';s.write(export,{'exportedByPremiere':True,'exportReceipt':'synthetic test only','outputSha256':sha(master),'projectSha256':sha(project),'sequenceId':'seq','durationFrames':60})
        with patch.object(s,'jobhome',return_value=home),patch.object(s,'jobdir',return_value=home/'project'),patch.object(s,'load',return_value={'fixture':True}),patch.object(s,'paths',return_value={'ready':self.root/'ready'}),patch.object(s.vh,'verify',return_value={'technical_pass':True}):
            state.record_handoff('fixture',project,'seq',package_file,handoff_evidence)
            candidate=state.register_candidate('fixture',master,project,'seq',deps,export)
            self.assertEqual(candidate['producer'],'premiere')
            self.assertNotIn('fingerprints',candidate)
            evidence=self.root/'approval.json';s.write(evidence,{'userApproval':'fixture exact file approval','reviewer':'test','notes':'synthetic only','checks':{k:'passed' for k in state.FINAL_CHECKS},'outputSha256':sha(master),'candidateSha256':sha(candidate['record'])})
            release=state.release_candidate('fixture',candidate['record'],evidence)
            self.assertEqual(Path(release['output']['path']).read_bytes(),master.read_bytes())
            master.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'alterado'):state.release_candidate('fixture',candidate['record'],evidence)

    def test_resume_does_not_promote_legacy_reports(self):
        home=self.root/'fixture';(home/'interchange/v1').mkdir(parents=True);s.write(home/'interchange/v1/report.json',{'handoffComplete':True})
        with patch.object(s,'jobhome',return_value=home),patch.object(s,'jobdir',return_value=home/'project'),patch.object(s,'load',return_value={'x':1}):
            r=state.resume('fixture')
        self.assertIsNone(r['activeHandoff']);self.assertEqual(len(r['legacyTransferReports']),1)
    def test_host_guard_wrong_sequence_unknown_outcome_and_persistence(self):
        import premiere_verification as v
        observed={'projectPath':str(self.root/'fixture.prproj'),'sequenceId':'fixture','clips':[]}
        with self.assertRaises(ValueError):v.assert_target(observed,observed['projectPath'],'production')
        with self.assertRaises(ValueError):v.assert_target({**observed,'recoveryRequired':True},observed['projectPath'],'fixture')
        c=dict(id='c1',name='base',kind='video',track=0,start=60,duration=60,sourceIn=60,sourceFrames=180,sha256='abc',motion={'scale':100,'position':[720,1280]})
        package={'fps':60,'clips':[c],'captions':[]}
        actual={**c,'mediaSha256':'abc','nodeId':'node1'}
        before={**observed,'clips':[actual]}
        self.assertTrue(v.persistence(package,before,before,observed['projectPath'],'fixture')['passed'])
        after={**observed,'clips':[{**actual,'sourceIn':0}]}
        self.assertFalse(v.persistence(package,before,after,observed['projectPath'],'fixture')['passed'])
        self.assertTrue(v.geometry_batches(package,before,observed['projectPath'],'fixture')[0]['requiresReadback'])

    def test_handle_sample_mismatch_rejected(self):
        video=self.file('source.mov');audio=self.file('voice.wav')
        p={'fps':60,'durationInFrames':60,'scenes':[{'id':'s1','from':0,'duration':60}]}
        m={'entries':[{'scene':'s1','file':str(video),'sha256':sha(video),'audio':str(audio),'audioSha256':sha(audio),'frames':180,'cutIn':60,'cutOut':120,'sourceWindow':{'sourceIn':0,'sourceOut':180}}]}
        def probe(path):
            if path.suffix=='.mov':return {'streams':[dict(codec_type='video',codec_name='prores',profile='Standard',width=2160,height=3840,avg_frame_rate='60/1',nb_frames='180')]}
            return {'streams':[dict(codec_type='audio',codec_name='pcm_s24le',sample_rate='48000',channels=2,time_base='1/48000',duration_ts=143999)]}
        with self.assertRaisesRegex(ValueError,'samples'):package.av_windows(p,m,probe)

if __name__=='__main__':unittest.main()
