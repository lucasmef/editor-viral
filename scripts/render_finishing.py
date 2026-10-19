"""Compile scene-local sound cues and conservative base-only color controls."""
import math

def compile_finishing(host, project, finish):
    offsets={};cursor=0
    for scene in project['scenes']:
        offsets[scene['id']]=(cursor,scene);cursor+=scene['duration']
    sounds=[]
    for cue in finish.get('soundEffects',[]):
        if cue.get('scene') not in offsets:raise ValueError('Cena de efeito sonoro inexistente')
        offset,scene=offsets[cue['scene']];frame=cue.get('frame');duration=cue.get('duration');gain=cue.get('gainDb',-18)
        if type(frame)is not int or not 0<=frame<scene['duration']:raise ValueError('Frame de efeito sonoro inválido')
        if type(duration)is not int or not 0<duration<=cursor-offset-frame:raise ValueError('Duração de efeito sonoro inválida')
        if type(gain)not in (int,float) or not math.isfinite(gain) or not -60<=gain<=0:raise ValueError('Ganho de efeito sonoro inválido')
        sounds.append({'src':host.stage_file(cue['mediaId']),'from':offset+frame,'duration':duration,'gainDb':gain})
    grade=finish.get('colorGrade',{})
    if not isinstance(grade,dict) or set(grade)-{'brightness','contrast','saturation','warmth'}:raise ValueError('Controle de cor inválido')
    for key,value in grade.items():
        if type(value)not in (int,float) or not math.isfinite(value) or not ((0<=value<=.3) if key=='warmth' else (.5<=value<=1.5)):raise ValueError('Valor de cor inválido')
    return sounds,grade
