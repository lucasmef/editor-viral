"""Extract timed frames and a local Whisper transcript for an existing reference."""
import argparse,json,subprocess,io,os
import storage
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('--id',required=True);p.add_argument('--times',default='0.1,0.3,0.5,0.8,1.1,1.4,1.7,2,2.3,2.6,2.9,3.2');p.add_argument('--transcribe',action='store_true');a=p.parse_args()
out=storage.roots(ROOT)['edit']/'_editor/references'/a.id;out.mkdir(parents=True,exist_ok=True)
ff=str(ROOT/'.local-bin/ffmpeg')
times=[float(t) for t in a.times.split(',')]
sheet=Image.new('RGB',(1200,382*((len(times)+5)//6)),(25,25,25));draw=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 r=subprocess.run([ff,'-v','error','-ss',str(t),'-i',str(a.video),'-frames:v','1','-vf','scale=200:-1','-f','image2pipe','-vcodec','mjpeg','-threads','1','-'],capture_output=True,check=True)
 im=Image.open(io.BytesIO(r.stdout));im.thumbnail((200,356));x=i%6*200;y=i//6*382;sheet.paste(im,(x,y+24));draw.text((x+4,y+5),f'{a.id} {t:.2f}s',fill='white')
sheet.save(out/'frames.jpg')
(out/'provenance.json').write_text(json.dumps({'source':str(a.video.resolve()),'sampled_seconds':times},indent=2))
if a.transcribe:
 subprocess.run([ff,'-v','error','-y','-i',str(a.video),'-vn','-ac','1','-ar','16000',str(out/'audio.wav')],check=True)
 os.environ['PATH']=str(ROOT/'.local-bin')+os.pathsep+os.environ['PATH']
 import mlx_whisper
 r=mlx_whisper.transcribe(str(out/'audio.wav'),path_or_hf_repo=str(ROOT/'.runtime/models/whisper-small'),language='pt',word_timestamps=True,verbose=False)
 (out/'transcript.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print(a.id,r['text'])
print(out/'frames.jpg')
