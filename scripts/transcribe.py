"""Local transcription; explicit input, external job output, no hard-coded video."""
import argparse,json,os
from pathlib import Path
import studio as s
p=argparse.ArgumentParser();p.add_argument('job');p.add_argument('audio',type=Path);p.add_argument('--prompt',default='');a=p.parse_args()
os.environ['PATH']=str(s.ROOT/'.local-bin')+os.pathsep+os.environ['PATH']
import mlx_whisper
r=mlx_whisper.transcribe(str(a.audio.resolve()),path_or_hf_repo=str(s.ROOT/'.runtime/models/whisper-small'),language='pt',word_timestamps=True,initial_prompt=a.prompt,verbose=False)
out=s.run_dir(a.job,'transcripts')/'transcript.json';s.write(out,r,True);print(out)
