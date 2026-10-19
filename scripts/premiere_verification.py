"""Strict host readback comparison. Neither an MCP success nor an XML parse is proof."""
import argparse
from pathlib import Path
import studio as s


def assert_target(observed, project_path, sequence_id):
    if Path(observed['projectPath']).resolve()!=Path(project_path).resolve() or observed['sequenceId']!=sequence_id:
        raise ValueError('Project AND sequence must match before any dependent edit')
    if observed.get('recoveryRequired'):
        raise ValueError('Unknown host outcome: inspect/reconcile before another edit')


def compare(package, observed, project_path, sequence_id):
    assert_target(observed,project_path,sequence_id)
    errors=[];actual=observed['clips'];used=set();fps=package['fps']
    for expected in package['clips']:
        matches=[(i,c) for i,c in enumerate(actual) if c['name']==expected['name'] and c['kind']==expected['kind'] and c['track']==expected['track'] and abs(c['start']-expected['start'])<.01]
        if len(matches)!=1:
            errors.append('Missing/ambiguous clip: '+expected['id']);continue
        index,clip=matches[0];used.add(index)
        for k in ('start','duration','sourceIn'):
            if abs(clip[k]-expected[k])>.01:errors.append(f'{expected["id"]}: {k}')
        if clip.get('mediaSha256')!=expected['sha256']:errors.append(expected['id']+': media identity')
        if expected.get('motion'):
            motion=clip.get('motion',{})
            if abs(motion.get('scale',-1000)-expected['motion']['scale'])>.01 or any(abs(a-b)>.1 for a,b in zip(motion.get('position',[-10000,-10000]),expected['motion']['position'])):
                errors.append(expected['id']+': geometry')
        if expected.get('pair'):
            pair=[c for c in package['clips'] if c.get('pair')==expected['pair'] and c['id']!=expected['id']]
            if sorted(clip.get('linkedPackageIds',[]))!=sorted(c['id'] for c in pair):errors.append(expected['id']+': A/V link')
            if clip.get('sourceFrames')!=expected['sourceFrames']:errors.append(expected['id']+': source handles')
    # Native titles are recorded separately; no unexplained video/audio clones allowed.
    if len(used)!=len(actual):errors.append('Unexplained or duplicated timeline clips')
    titles=observed.get('captions',[])
    if len(titles)!=len(package.get('captions',[])):errors.append('Caption count')
    for expected,actual_title in zip(package.get('captions',[]),titles):
        if any(actual_title.get(k)!=expected[k] for k in ('text','from','duration')) or actual_title.get('templateSha256')!=package['captionTemplateSha256']:
            errors.append('Caption content/timing/template differs')
        if not actual_title.get('renderEvidence'):errors.append('Caption render evidence missing; text readback alone is insufficient')
    return {'technicalPass':not errors,'errors':errors,'editorialApproval':False,'fps':fps}


def persistence(package,before,after,project,sequence):
    checks=[compare(package,x,project,sequence) for x in (before,after)]
    return {'passed':all(c['technicalPass'] for c in checks),'beforeSave':checks[0],'afterReopen':checks[1],'editorialApproval':False}


def geometry_batches(package,observed,project,sequence):
    assert_target(observed,project,sequence)
    items=[]
    for c in package['clips']:
        if not c.get('motion'):continue
        matches=[x for x in observed['clips'] if x['name']==c['name'] and x['kind']==c['kind'] and x['track']==c['track'] and abs(x['start']-c['start'])<.01]
        if len(matches)!=1:raise ValueError('Inspect missing/ambiguous clip before applying geometry')
        items.append({'node_id':matches[0]['nodeId'],'position_x':c['motion']['position'][0],'position_y':c['motion']['position'][1],'scale':c['motion']['scale']})
    return [{'tool':'set_clip_properties_batch','expectedProjectPath':str(Path(project).resolve()),'expectedSequenceId':sequence,'items':items[i:i+16],'requiresReadback':True} for i in range(0,len(items),16)]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--package',required=True);ap.add_argument('--before-save',required=True);ap.add_argument('--after-reopen',required=True);ap.add_argument('--project',required=True);ap.add_argument('--sequence',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    result=persistence(s.read(a.package),s.read(a.before_save),s.read(a.after_reopen),a.project,a.sequence);s.write(a.out,result,True)
    if not result['passed']:raise SystemExit(2)
if __name__=='__main__':main()
