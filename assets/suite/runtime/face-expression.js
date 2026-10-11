// Uses the original, unchanged expression sheet on the deformable face surfaces.
// Each eye gets its own material so blinks do not replace the mouth expression.
export function createFaceExpressions(actor){
 const parts=[];actor.traverse(o=>{if(o.isMesh&&o.material?.map&&o.name.startsWith('Painted_')){o.material=o.material.clone();o.material.map=o.material.map.clone();parts.push(o);}});
 let last='';
 return function setFace(smile,angry,sad,blink){
  const expression=angry>.5?'angry':sad>.5?'sad':smile>.25?'smile':'neutral',closed=blink>.75;
  const key=expression+'/'+closed;if(key===last)return;last=key;
  for(const o of parts){const offset=expression==='smile'?[.25,0]:expression==='angry'?[0,-.5]:[0,0];
   if(closed&&o.name.startsWith('Painted_eye')){offset[0]=.5;offset[1]=0;}
   o.material.map.offset.set(...offset);o.material.map.updateMatrix();
  }
 };
}
