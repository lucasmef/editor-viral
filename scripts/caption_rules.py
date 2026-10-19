"""Display-only filtering. Full spoken transcript is preserved by the caller."""
import re

def display_word(text):
 return ' '.join(re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE).split())

def build(words,policy,highlights=()):
 result=[];omit=set(policy.get('omit',[]))-set(policy.get('preserve',['não','sem','nem']))
 for word in words:
  text=display_word(word['text']) if not policy.get('punctuation',False) else word['text'].strip()
  if not text or text.casefold() in omit:continue
  # Each input is a timed spoken word; never compress the time of omitted words.
  result.append({'text':text,'from':word['from'],'duration':word['duration'],'highlight':text.casefold() in highlights})
 return result

def violations(captions,policy):
 errors=[];omit=set(policy.get('omit',[]))-set(policy.get('preserve',['não','sem','nem']))
 compounds=policy.get('compounds',['azul marinho','amarelo manteiga'])
 for c in captions:
  text=c['text']
  if not policy.get('punctuation',False) and text!=display_word(text):errors.append('Pontuação visual: '+text)
  if text.casefold() in omit:errors.append('Palavra omitível exibida: '+text)
  if policy.get('mode')=='word' and len(text.split())>1 and text.casefold() not in compounds:errors.append('Legenda precisa segmentação por palavra: '+text)
 return errors

def continuous(captions,duration,first_frame=0):
 """Hold visible words across omitted speech/pauses without changing speech timing."""
 if not captions:return []
 if not 0<=first_frame<duration:raise ValueError('Janela de legenda inválida')
 result=[dict(c) for c in sorted(captions,key=lambda c:c['from'])]
 boundaries=[first_frame]
 for left,right in zip(result,result[1:]):
  end=left['from']+left['duration'];start=right['from']
  boundary=(end+start)//2 if end<=start else start
  if not boundaries[-1]<boundary<duration:raise ValueError('Tempos de legenda incompatíveis')
  boundaries.append(boundary)
 boundaries.append(duration)
 for c,start,end in zip(result,boundaries,boundaries[1:]):c.update({'from':start,'duration':end-start})
 return result
