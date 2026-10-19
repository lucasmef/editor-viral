"""Synthetic post-migration MatAnyone/Metal availability and hair render check."""
import os,sys,json
from pathlib import Path
import numpy as np
import cv2
import studio as s
import hair_connector as hair

base=Path(sys.argv[1]).resolve();os.environ['EDITOR_STORAGE_CONFIG']=str(base/'storage.json')
job='fixture';d=s.load(job);source=s.resolve(d['project.json']['scenes'][0]['clip']['mediaId'])
work=s.run_dir(job,'hair');work.mkdir(parents=True,exist_ok=True)
seed=np.zeros((128,128),np.uint8);seed[24:104,32:96]=255;cv2.imwrite(str(work/'seed.png'),seed)
patch=np.zeros((128,128),np.uint16);patch[8:120,8:120]=65535;cv2.imwrite(str(work/'patch.png'),patch)
plan={'schemaVersion':1,'project':str(s.jobdir(job)/'project.json'),'model':{'code':str(s.ROOT/'.runtime/hair/vendor/MatAnyone2-main'),'weights':str(s.ROOT/'.runtime/hair/models/matanyone2.pth'),'device':'mps'},'scenes':[{'id':'one','source':str(source),'seed':str(work/'seed.png'),'roi':[80,160,128,128],'alphaSize':[128,128],'fullSize':[360,640],'donorRoi':[0,0,360,640],'donorSize':[360,640],'detailBox':[0,0,128,128],'patchMask':str(work/'patch.png'),'background':{'donorOffsetNative':[0,0],'offsetRgb':[0,0,0]},'protection':[]}]}
s.write(work/'plan.json',plan,True)
prepared=hair.prepare(s,job,work/'plan.json',work/'prepared')
rendered=hair.render(s,job,work/'rendered')
hair.attach(s,job,work/'rendered')
mid=hair.validate_attached(s,s.load(job));assert mid
sys.path.insert(0,'/Users/lucas/Documents/Codex/rosto-natural/integrations/editor-metal-v1')
import backend
engine=backend.Engine()
s.write(base/'hair-metal-verification.json',{'synthetic':True,'prepared':prepared,'rendered':rendered,'attachedMediaId':mid,'metalDevice':engine.device,'editorialApproval':False})
print(base/'hair-metal-verification.json')
