"""Real synthetic storage/voice/face-base/render smoke, isolated from user jobs."""
import json,os,subprocess,sys
from pathlib import Path
import studio as s
import storage
import voice_connector as voice
import face_connector as face

root=s.paths()['cache']/('storage-smoke-'+s.now().replace(':','-'))
root.mkdir(parents=True,exist_ok=False)
config=root/'storage.json';s.write(config,{'schemaVersion':1,'roots':{k:str(root/k) for k in storage.KEYS}})
os.environ['EDITOR_STORAGE_CONFIG']=str(config)
source=root/'source/fixture.mov';source.parent.mkdir()
subprocess.run([s.vh.binary('ffmpeg'),'-v','error','-f','lavfi','-i','testsrc2=size=360x640:rate=60',
 '-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1','-vf','setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709','-c:v','libx264','-preset','ultrafast',
 '-pix_fmt','yuv420p','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709',
 '-color_range','tv','-movflags','+write_colr','-c:a','pcm_s16le','-ac','2',str(source)],check=True)
mid=s.register(source,'original');s.init_job('fixture','SYNTHETIC TEST ONLY — no user approvals')
d=s.load('fixture');d['project.json'].update(width=360,height=640)
d['project.json']['scenes']=[{'id':'one','duration':60,'script':'fixture','clip':{'mediaId':mid,'inFrame':0},'layers':[],'captions':[{'text':'teste','from':0,'duration':60}],'events':[]}]
d['style.json']['layout']={'labels':[],'caption':{'x':30,'y':30,'width':300,'fontSize':24}}
for n,v in d.items():s.write(s.jobdir('fixture')/n,v)
e=root/'synthetic-approval.json';s.write(e,{'fingerprint':s.fingerprints(d)['preproduction'],'notes':'Automated synthetic fixture; no real footage or user decision','userApproval':'TEST FIXTURE ONLY','checks':{'cuts':'passed','looks':'passed'}})
s.approve('fixture','preproduction',e,'synthetic-fixture')
v=voice.process(s,'fixture');voice.validate_attached(s,s.load('fixture'),required=True)
f=face.base(s,'fixture',s.jobhome('fixture')/'face/base')
# Rename only our generated source; prove hash-based reconnection.
new=source.with_name('relocated.mov');source.rename(new);s.relink(mid,new);assert s.resolve(mid)==new
result=s.render('fixture',None)
try:s.render('fixture',s.jobhome('fixture')/'candidates/blocked.mov',master=True)
except ValueError:blocked=True
else:raise AssertionError('Master bypassed pending checkpoints')
s.write(root/'verification.json',{'synthetic':True,'voice':v,'faceBase':f,'render':result,'relink':True,'masterBlocked':blocked,'no174Changes':True})
print(root/'verification.json')
