from pathlib import Path
import json,shutil
from PIL import Image
base=Path(__file__).resolve().parents[2];source=base/'outputs/LISA-Source';assets=source/'godot/assets'
gen=Path('C:/Users/HP/.codex/generated_images/01a0fb84-487f-74a0-93c8-8e0fd5529baa')
for name,file in {'walk':'83a3da84-a74b-44b3-b222-ff8e5b7f6093','clothes':'6d37be8b-1721-4ffc-8138-6f71db257942'}.items():shutil.copy2(gen/('exec-'+file+'.png'),assets/(name+'.png'))
groups={'directions':['front','quarter','profile','back'],'living':['seated','tea','sleep','wave'],'actions':['command','angry','squat','ankle'],'grooming':['wash','hair','book','phone'],'props':['whip','water','stretch','sweat'],'expressions':['sad','kiss','brush','dryhair'],'walk':['walk0','walk1','walk2','walk3'],'clothes':['bare','sleeveless','sleeveless_bare','seated_bare']}
poses={}
for sheet,names in groups.items():
 im=Image.open(assets/(sheet+'.png')).convert('RGBA');w,h=im.size;alpha=im.getchannel('A')
 for i,name in enumerate(names):
  cell=(i%2*w//2,i//2*h//2,(i%2+1)*w//2,(i//2+1)*h//2)
  if sheet=='living' and i==2:cell=(0,h//2,640,h)
  if sheet=='living' and i==3:cell=(640,h//2,w,h)
  bounds=alpha.crop(cell).point(lambda a:255 if a>170 else 0).getbbox()
  if not bounds:raise ValueError(name+' lacks opaque body')
  x0,y0,x1,y1=bounds;x0+=cell[0];x1+=cell[0];y0+=cell[1];y1+=cell[1]
  x0=max(cell[0],x0-4);y0=max(cell[1],y0-4);x1=min(cell[2],x1+4);y1=min(cell[3],y1+4)
  height=0.75 if name=='sleep' else 1.38 if name in ['seated','seated_bare','tea','book','phone','ankle'] else 1.65 if name=='squat' else 1.8
  poses[name]={'sheet':sheet,'rect':[x0,y0,x1-x0,y1-y0],'height':height,'center':height/2}
(assets/'poses.json').write_text(json.dumps(poses,indent=2))
(assets/'provenance.json').write_text(json.dumps({'type':'illustrated 2.5D pose atlases','adult_character':True,'source':'User-approved Lisa reference; generated using OpenAI image tool in this chat','poses':len(poses),'deformable_model':False,'method':'Opaque-body bounds inspected; artwork unchanged; engine crops UV regions at runtime','files':list(groups)},indent=2))
print('Prepared',len(poses),'illustrated pose frames')
