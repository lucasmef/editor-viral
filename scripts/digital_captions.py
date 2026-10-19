"""Map ASR evidence into a test timeline. Never marks speech/listening approved."""
def map_words(words, segments, fps):
    mapped=[]
    for segment in segments:
        start,end=segment['sourceIn'],segment['sourceOut']
        offset=round(segment['timelineIn']*fps)
        limit=round(segment['timelineOut']*fps)
        local=[]
        for word in words:
            if word['end']<=start or word['start']>=end:continue
            a=offset+round((max(start,word['start'])-start)*fps)
            b=min(limit,offset+round((min(end,word['end'])-start)*fps))
            if b<=a:continue
            local.append({'text':word['word'].strip(),'from':a,'duration':b-a,
                          'sourceStart':word['start'],'sourceEnd':word['end'],
                          'segment':segment['id']})
        mapped.extend(local)
    mapped.sort(key=lambda w:w['from'])
    for a,b in zip(mapped,mapped[1:]):
        if a['from']>=b['from']:raise ValueError('Ambiguous overlapping word alignment')
        a['duration']=min(a['duration'],b['from']-a['from'])
    return mapped


def group_words(words, total, fps):
    groups=[];batch=[]
    def flush():
        if not batch:return
        groups.append({'from':batch[0]['from'],'duration':batch[-1]['from']+batch[-1]['duration']-batch[0]['from'],
                       'words':list(batch)})
        batch.clear()
    for word in words:
        if batch and (len(batch)>=3 or sum(len(w['text'])+1 for w in batch)+len(word['text'])>25
                      or word['segment']!=batch[-1]['segment']
                      or word['from']-(batch[-1]['from']+batch[-1]['duration'])>round(.35*fps)
                      or batch[-1]['text'].endswith(('.', '?', '!'))):flush()
        batch.append(word)
    flush()
    for i,g in enumerate(groups):
        limit=groups[i+1]['from'] if i+1<len(groups) else total
        g['duration']=min(limit-g['from'],g['duration']+round(.10*fps))
        if not 0<=g['from']<g['from']+g['duration']<=total:raise ValueError('Caption outside timeline')
    return groups
