import * as THREE from 'three';
export function createCinematicCamera(suite,actor){
 const head=actor.getObjectByName('Head'),hips=actor.getObjectByName('Hips'),h=new THREE.Vector3(),p=new THREE.Vector3(),target=new THREE.Vector3(),candidate=new THREE.Vector3(),direction=new THREE.Vector3(),ray=new THREE.Raycaster();
 let enabled=true,lastProbe=-10,obstacleDistance=Infinity,followYaw=0;
 const solid=[];suite.room.traverse(o=>{if(o.isMesh&&!o.material?.transparent&&!o.material?.isMeshBasicMaterial)solid.push(o);});
 function setEnabled(value){enabled=!!value;lastProbe=-10;}
 function update(now,dt,state){
  if(!enabled||suite.status.planMode)return false;
  actor.updateMatrixWorld(true);head.getWorldPosition(h);hips.getWorldPosition(p);
  const active=['walking','standing-up','getting-up','sitting-down','lying-down','exercise','prop-action'].includes(state.phase);
  if(!active&&state.area==='room'){suite.trackCamera([actor.position.x+.04,1.13,actor.position.z+2.7],[actor.position.x,.98,actor.position.z],46,dt);return true;}
  if(!active&&suite.views[state.area]){
   const shot=suite.views[state.area];target.fromArray(shot.target);candidate.fromArray(shot.pos);
   // Keep Lisa, not just the empty furniture, in the destination framing.
   target.lerp(h,.28);
   suite.trackCamera(candidate.toArray(),target.toArray(),shot.fov,dt);return true;
  }
  target.copy(h).multiplyScalar(.64).addScaledVector(p,.36);
  const yaw=actor.rotation.y+.65;
  followYaw+=((yaw-followYaw+Math.PI*3)%(Math.PI*2)-Math.PI)*Math.min(1,dt*2.3);
  const radius=state.phase==='exercise'?3.5:2.85;
  candidate.set(actor.position.x+Math.sin(followYaw)*radius,target.y+.45,actor.position.z+Math.cos(followYaw)*radius);
  candidate.x=THREE.MathUtils.clamp(candidate.x,-5.6,actor.position.x>5.8?8.35:5.70);
  candidate.z=THREE.MathUtils.clamp(candidate.z,-4.18,4.16);candidate.y=THREE.MathUtils.clamp(candidate.y,1.15,2.15);
  if(actor.position.x>5.6){candidate.z=Math.min(candidate.z,.56);candidate.x=Math.max(candidate.x,5.18);}
  // Probe a few times/second, not every render, and omit transparent room glass.
  if(now-lastProbe>300){direction.subVectors(candidate,target);const length=direction.length();ray.set(target,direction.normalize());ray.far=length;const hits=ray.intersectObjects(solid,false).filter(hit=>hit.distance>.25);obstacleDistance=hits.length?Math.max(.72,hits[0].distance-.16):Infinity;lastProbe=now;}
  direction.subVectors(candidate,target);if(direction.length()>obstacleDistance)candidate.copy(target).addScaledVector(direction.normalize(),obstacleDistance);
  suite.trackCamera(candidate.toArray(),target.toArray(),active?51:49,dt);return true;
 }
 return {setEnabled,update,get enabled(){return enabled;}};
}
