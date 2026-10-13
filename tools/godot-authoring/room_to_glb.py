from pathlib import Path
import json,struct,base64
base=Path(__file__).resolve().parents[2];data=json.loads((base/'work/lisa-2.1/room-export.json').read_text());out=base/'outputs/LISA-Source/godot/assets';out.mkdir(parents=True,exist_ok=True)
blob=bytearray();doc={'asset':{'version':'2.0','generator':'Kitty Corp approved room converter'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'buffers':[],'bufferViews':[],'accessors':[],'images':[],'textures':[],'samplers':[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}]}
def view(raw,target=None):
 while len(blob)%4:blob.append(0)
 v={'buffer':0,'byteOffset':len(blob),'byteLength':len(raw)}
 if target:v['target']=target
 blob.extend(raw);doc['bufferViews'].append(v);return len(doc['bufferViews'])-1
def accessor(a,size,component=5126):
 raw=struct.pack('<'+('f' if component==5126 else 'I')*len(a),*a);v=view(raw,34963 if component!=5126 else 34962)
 d={'bufferView':v,'componentType':component,'count':len(a)//size,'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[size]}
 if size==3:d.update(min=[min(a[i::3]) for i in range(3)],max=[max(a[i::3]) for i in range(3)])
 doc['accessors'].append(d);return len(doc['accessors'])-1
tex={}
for key,url in data['textures'].items():
 raw=base64.b64decode(url.split(',')[1]);doc['images'].append({'bufferView':view(raw),'mimeType':'image/png'});doc['textures'].append({'sampler':0,'source':len(doc['images'])-1});tex[key]=len(doc['textures'])-1
mats={}
for key,m in data['materials'].items():
 pbr={'baseColorFactor':m['color']+[m['alpha']],'metallicFactor':m['metalness'],'roughnessFactor':m['roughness']}
 if m['texture']:pbr['baseColorTexture']={'index':tex[m['texture']]}
 material={'name':key,'pbrMetallicRoughness':pbr,'doubleSided':m['doubleSided'],'emissiveFactor':m['emissive']}
 if m['transparent']:material.update(alphaMode='BLEND')
 doc['materials'].append(material);mats[key]=len(doc['materials'])-1
geos={}
for key,g in data['geometries'].items():
 attrs={name:accessor(g['attrs'][src],size) for src,name,size in [('position','POSITION',3),('normal','NORMAL',3),('uv','TEXCOORD_0',2)] if src in g['attrs']}
 geos[key]={'attributes':attrs}
 if g['index']:geos[key]['indices']=accessor(g['index'],1,5125)
door_parents={}
for role,pivot in {'balcony_door':[6.02,.08,-2.17],'bathroom_door':[-.45,.07,-1.87]}.items():
 doc['nodes'].append({'name':'BalconyDoor' if role=='balcony_door' else 'BathroomDoor','translation':pivot,'children':[]})
 door_parents[role]=(len(doc['nodes'])-1,pivot)
 doc['scenes'][0]['nodes'].append(len(doc['nodes'])-1)
for n in data['nodes']:
 prim=dict(geos[n['geometry']],material=mats[n['material']]);doc['meshes'].append({'primitives':[prim]})
 matrix=n['matrix'][:]
 role=n.get('role','')
 if role in door_parents:
  index,pivot=door_parents[role]
  for i in range(3):matrix[12+i]-=pivot[i]
 doc['nodes'].append({'name':n['name'],'mesh':len(doc['meshes'])-1,'matrix':matrix})
 if role in door_parents:doc['nodes'][door_parents[role][0]]['children'].append(len(doc['nodes'])-1)
 else:doc['scenes'][0]['nodes'].append(len(doc['nodes'])-1)
while len(blob)%4:blob.append(0)
doc['buffers']=[{'byteLength':len(blob)}];raw=json.dumps(doc,separators=(',',':')).encode()
while len(raw)%4:raw+=b' '
result=struct.pack('<III',0x46546c67,2,12+8+len(raw)+8+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob
(out/'lisa-room.glb').write_bytes(result);(out/'room-layout.json').write_text(json.dumps({k:data[k] for k in ['anchors','views','fixtures']},indent=2))
print('Room GLB:',len(result),'bytes,',len(doc['nodes']),'meshes')
