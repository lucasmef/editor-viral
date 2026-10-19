import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from digital_captions import map_words,group_words

class DigitalCaptions(unittest.TestCase):
    def test_reordered_words_retain_source_and_negation(self):
        words=[{'word':'não','start':1,'end':1.3},{'word':'sim','start':4,'end':4.4}]
        segments=[{'id':'b','sourceIn':3.8,'sourceOut':4.8,'timelineIn':0,'timelineOut':1},
                  {'id':'a','sourceIn':.8,'sourceOut':1.8,'timelineIn':1,'timelineOut':2}]
        result=map_words(words,segments,60)
        self.assertEqual([w['text'] for w in result],['sim','não'])
        self.assertEqual([w['from'] for w in result],[12,72])
        self.assertEqual(result[1]['sourceStart'],1)

    def test_word_crossing_start_is_clamped_not_dropped(self):
        s=[{'id':'a','sourceIn':1,'sourceOut':2,'timelineIn':0,'timelineOut':1}]
        w=map_words([{'word':'O','start':.8,'end':1.2}],s,60)
        self.assertEqual((w[0]['from'],w[0]['duration']),(0,12))

    def test_groups_cannot_leak_across_next_caption_or_end(self):
        words=[dict(text='não',from_=0,duration=8,segment='a'),dict(text='sai.',from_=8,duration=10,segment='a'),dict(text='Fim',from_=19,duration=11,segment='b')]
        for w in words:w['from']=w.pop('from_')
        groups=group_words(words,30,60)
        self.assertEqual(groups[0]['from']+groups[0]['duration'],19)
        self.assertEqual(groups[-1]['from']+groups[-1]['duration'],30)
