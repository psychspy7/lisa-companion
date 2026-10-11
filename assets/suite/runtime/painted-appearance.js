import * as THREE from 'three';
// Approved painted artwork is used only in controlled, frontal idle shots.
// Walking, turning and prop actions remain genuine skeletal 3D.
export async function createPaintedAppearance(actor,suite){
 const texture=await new THREE.TextureLoader().loadAsync('../references/lisa-standing-approved.png');texture.colorSpace=THREE.SRGBColorSpace;
 const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,uniforms:{art:{value:texture},opacity:{value:0},time:{value:0},blink:{value:0},speech:{value:0}},vertexShader:`
 uniform float time,blink,speech;varying vec2 vUv;
 void main(){vUv=uv;vec3 p=position;
 float face=exp(-pow((uv.x-.51)/.13,4.0)-pow((uv.y-.90)/.062,4.0));
 float eyes=max(exp(-pow((uv.x-.437)/.027,4.0)),exp(-pow((uv.x-.568)/.027,4.0)))*exp(-pow((uv.y-.902)/.010,4.0));
 p.y+=(.902-uv.y)*1.8*blink*eyes;
 float lips=exp(-pow((uv.x-.51)/.030,4.0)-pow((uv.y-.875)/.014,4.0));
 p.y+=sign(uv.y-.875)*speech*.012*lips;
 float chest=exp(-pow((uv.y-.69)/.16,2.0));p.x*=1.0+.006*sin(time*2.1)*chest;
 float hair=step(.50,uv.y)*(1.0-face)*smoothstep(.06,.25,abs(uv.x-.5));p.x+=.005*sin(time*1.7+uv.y*9.0)*hair;
 gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);
 }`,fragmentShader:`uniform sampler2D art;uniform float opacity;varying vec2 vUv;void main(){vec4 c=texture2D(art,vUv);if(c.a<.08)discard;gl_FragColor=vec4(c.rgb,c.a*opacity);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 }`});
 // Colour conversion is handled by Three's output pipeline, never by modifying the image.
 material.toneMapped=false;
 const geometry=new THREE.PlaneGeometry(1.8*767/2051,1.8,28,150);geometry.translate(0,.9,0);
 const plane=new THREE.Mesh(geometry,material);plane.position.z=.16;plane.castShadow=true;plane.customDepthMaterial=new THREE.MeshDepthMaterial({map:texture,alphaTest:.15,depthPacking:THREE.RGBADepthPacking});plane.renderOrder=2;actor.add(plane);let opacity=0;
 function update(dt,state,blink,speech,emotion){
  const camera=actor.worldToLocal(suite.camera.position.clone()),yaw=Math.atan2(camera.x,camera.z),front=Math.abs(yaw)<.16&&Math.abs(camera.y-1.0)<.6;
  const eligible=front&&state.posture==='standing'&&state.phase==='idle'&&state.area==='room'&&!state.cycle&&emotion==='Smile'&&!suite.status.planMode;
  opacity=THREE.MathUtils.damp(opacity,eligible?1:0,7,dt);material.uniforms.opacity.value=opacity;material.uniforms.time.value=state.elapsed;material.uniforms.blink.value=blink;material.uniforms.speech.value=speech;
  actor.traverse(o=>{if(o.isSkinnedMesh)o.visible=!o.userData.hiddenByClothing&&opacity<.5;});plane.visible=opacity>=.5;material.uniforms.opacity.value=plane.visible?1:0;
 }
 return {update,plane,get status(){return {mode:opacity>.5?'painted frontal shot':'skeletal 3D',opacity};}};
}
