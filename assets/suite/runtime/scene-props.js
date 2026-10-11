import * as THREE from 'three';
export function createSceneProps(actor,suite){
 const objects={},left=(actor.getObjectByName('Hand.L')||actor.getObjectByName('HandL')||actor.getObjectByName('Hand_L')),right=(actor.getObjectByName('Hand.R')||actor.getObjectByName('HandR')||actor.getObjectByName('Hand_R')),point=new THREE.Vector3(),rotation=new THREE.Quaternion(),wet=[];
 const make=(id,geometry,color)=>{const o=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.55}));o.castShadow=true;o.visible=false;suite.scene.add(o);objects[id]=o;return o;};
 make('bottle',new THREE.CylinderGeometry(.026,.026,.17,16),'#8eb7be');
 make('phone',new THREE.BoxGeometry(.07,.13,.008),'#272331');
 make('book',new THREE.BoxGeometry(.15,.20,.028),'#77424b');
 make('towel',new THREE.BoxGeometry(.09,.15,.016),'#eee2d6');
 const cigarette=make('cigarette',new THREE.CylinderGeometry(.003,.003,.045,8),'#dbcfc4');cigarette.rotation.z=Math.PI/2;
 make('brush',new THREE.BoxGeometry(.006,.14,.006),'#dfc5b5');
 const whip=new THREE.Group();whip.visible=false;suite.scene.add(whip);objects.whip=whip;
 const handle=new THREE.Mesh(new THREE.CylinderGeometry(.012,.015,.17,12),new THREE.MeshStandardMaterial({color:'#241719'}));handle.rotation.z=Math.PI/2;whip.add(handle);
 const whipPoints=Array.from({length:32},(_,i)=>new THREE.Vector3(.08+i*.017,-.65*(i/31)**1.4,.045*Math.sin(i*.23)));
 const lash=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(whipPoints),40,.0045,6,false),handle.material);whip.add(lash);
 const shoes=new THREE.Group();shoes.visible=false;suite.scene.add(shoes);objects.shoes=shoes;
 for(const x of [-.1,.1]){const sole=new THREE.Mesh(new THREE.BoxGeometry(.07,.018,.20),handle.material);sole.position.set(x,.02,0);shoes.add(sole);const strap=new THREE.Mesh(new THREE.TorusGeometry(.029,.004,6,16,Math.PI),handle.material);strap.position.set(x,.03,.045);shoes.add(strap);}
 actor.traverse(o=>{if(o.isMesh&&o.material?.name==='Peach skin'){o.material=o.material.clone();wet.push(o.material);}});
 let held=null,hasWhip=false,barefoot=false,sweat=0;
 function hold(id){for(const [key,o] of Object.entries(objects))if(key!=='shoes')o.visible=key===id;held=id;hasWhip=id==='whip';}
 function sandals(on){actor.traverse(o=>{if(/^(Sandal_|Ankle_strap|Toe_strap|Heel_strap|Block_heel)/.test(o.name)){o.visible=on;o.userData.hiddenByClothing=!on;}});barefoot=!on;shoes.visible=!on;if(!on)shoes.position.copy(actor.position).add(new THREE.Vector3(.3,0,.2));}
 function sleeves(on){actor.traverse(o=>{if(o.name.startsWith('Sleeve.')){o.visible=on;o.userData.hiddenByClothing=!on;}});}
 function perspiration(value){sweat=value;for(const m of wet){m.roughness=value?.40:.72;}}
 function update(now){
  if(!held)return;const bone=held==='whip'?right:left;if(!bone)return;
  bone.getWorldPosition(point);bone.getWorldQuaternion(rotation);const prop=objects[held];
  prop.position.copy(point);prop.quaternion.copy(rotation);
  if(held==='book')prop.rotation.z+=Math.PI/2;
  if(held==='towel')prop.position.y+=.035;
 }
 return {hold,sandals,sleeves,perspiration,update,get status(){return {held,hasWhip,barefoot,sweat};},objects};
}
