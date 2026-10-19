import copy
import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import studio as s
import voice_connector as v

REPO = Path(__file__).resolve().parents[1]


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old = s.ROOT
        s.ROOT = self.root
        (self.root/'studio').mkdir()
        s.write(self.root/'studio/default-style.json', s.read(REPO/'studio/default-style.json'))
        self.profile = s.read(REPO/'studio/default-voice.json')
        self.profile['bundle'] = str(REPO/self.profile['bundle'])
        s.write(self.root/'studio/default-voice.json', self.profile)
        s.init_job('test', 'Fixture only, no creative approval')
        self.source = self.root/'source.wav'
        with wave.open(str(self.source), 'wb') as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(48000)
            for left, right in [(1000,3000),(-500,1500),(5000,1000)]:
                f.writeframes(struct.pack('<hh',left,right)*48000)
        self.mid = s.register(self.source,'original')
        self.d = s.load('test')
        self.d['project.json']['scenes'] = [
            {'id':'late','duration':30,'script':'fixture','clip':{'mediaId':self.mid,'inFrame':120},'layers':[],'captions':[],'events':[]},
            {'id':'early','duration':30,'script':'fixture','clip':{'mediaId':self.mid,'inFrame':0},'layers':[],'captions':[],'events':[]},
        ]
        self.save()

    def tearDown(self):
        s.ROOT = self.old
        self.tmp.cleanup()

    def save(self):
        for name, doc in self.d.items():s.write(s.jobdir('test')/name,doc)

    def test_new_job_pins_profile_and_default_changes_do_not_migrate_it(self):
        self.assertEqual(self.d['finishing.json']['voiceNeural'], self.profile)
        changed=copy.deepcopy(self.profile);changed['version']='future'
        s.write(self.root/'studio/default-voice.json',changed)
        self.assertEqual(s.load('test')['finishing.json']['voiceNeural'],self.profile)
        legacy=copy.deepcopy(self.d);legacy['finishing.json'].pop('voiceNeural')
        self.assertFalse(v.enabled(legacy))

    def test_preproduction_preview_does_not_process(self):
        with patch.object(v,'process',side_effect=AssertionError('must not process')):
            self.assertNotIn('audioMediaId',v.prepare(s,'test')['finishing.json'])
        with self.assertRaisesRegex(ValueError,'corte inicial'):v.process(s,'test')

    def test_extraction_follows_order_samples_and_arithmetic_mean(self):
        work=self.root/'work';work.mkdir()
        out, sources, segments=v.extract(s,self.d,work)
        with wave.open(str(out)) as f:data=f.readframes(f.getnframes())
        def pcm24(value):return (value << 8).to_bytes(3,'little',signed=True)*2
        self.assertEqual(data,pcm24(3000)*24000+pcm24(2000)*24000)
        self.assertEqual([x['sourceStartSample'] for x in segments],[96000,0])
        self.assertEqual([x['outputStartSample'] for x in segments],[0,24000])
        self.assertEqual(set(sources),{self.mid})

    def test_nonzero_audio_timestamp_rejected(self):
        work=self.root/'work';work.mkdir()
        meta={'streams':[{'codec_type':'audio','channels':2,'start_time':'.020'}, {'codec_type':'video','start_time':'0'}]}
        with patch.object(v,'probe',return_value=meta),self.assertRaisesRegex(ValueError,'Timestamps'):
            v.extract(s,self.d,work)

    def test_offline_original_does_not_use_proxy(self):
        self.d['project.json']['scenes'][0]['clip']['proxy']={'mediaId':'m-proxy','inFrame':0,'sourceInFrame':120}
        work=self.root/'work';work.mkdir()
        with patch.object(s,'resolve',side_effect=ValueError('offline original')),self.assertRaisesRegex(ValueError,'offline original'):
            v.extract(s,self.d,work)

    def test_manual_attachment_disables_automatic_policy(self):
        s.attach_finish('test','audio',self.source,'manual fixture')
        self.assertFalse(v.enabled(s.load('test')))
        with patch.object(v,'process',side_effect=AssertionError('manual must be preserved')):
            self.assertIn('audioMediaId',v.prepare(s,'test')['finishing.json'])

    def test_no_implicit_master_audio_or_postproduction_approval(self):
        with self.assertRaisesRegex(ValueError,'Voz Neural pendente'):v.prepare(s,'test',master=True)
        with self.assertRaisesRegex(ValueError,'Voz Neural pendente'):s.compile_job(self.d,master=True)

    def test_profile_hash_failure_before_execution(self):
        bad=copy.deepcopy(self.profile);bad['manifestSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Manifesto'):v.bundle(s,bad)

    def test_recut_preview_drops_stale_audio_without_mutating_job(self):
        self.d['finishing.json'].update(audioMediaId='m-old',audioEditHash='old',audioConnector={'binding':{'editHash':'old'}})
        self.save()
        with patch.object(s,'status',return_value={'checkpoints':{'preproduction':'stale'}}):
            preview=v.prepare(s,'test')
        self.assertNotIn('audioMediaId',preview['finishing.json'])
        self.assertIn('audioMediaId',s.load('test')['finishing.json'])

    def test_binding_changes_on_same_duration_reorder(self):
        before=v.binding(s,self.d)
        self.d['project.json']['scenes'].reverse()
        self.assertNotEqual(before,v.binding(s,self.d))


if __name__=='__main__':unittest.main()
