import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {RoomEnvironment} from './vendor/RoomEnvironment.js';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
import {createFaceExpressions} from './face-expression.js';

const scene=new THREE.Scene();scene.background=new THREE.Color('#21171e');scene.fog=new THREE.Fog('#21171e',5,12);
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;document.body.prepend(renderer.domElement);
const camera=new THREE.PerspectiveCamera(36,innerWidth/innerHeight,.02,25);camera.position.set(0,1.05,3.45);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.97,0);controls.enableDamping=true;controls.minDistance=.45;controls.maxDistance=5;controls.maxPolarAngle=Math.PI*.56;
const env=new RoomEnvironment(),p=new THREE.PMREMGenerator(renderer);scene.environment=p.fromScene(env,.04).texture;scene.environmentIntensity=.35;env.dispose();p.dispose();
scene.add(new THREE.HemisphereLight('#efe0e2','#4c2d35',.9));
const key=new THREE.DirectionalLight('#ffe2ce',1.65);key.position.set(1.6,3,2);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.camera.left=key.shadow.camera.bottom=-1.2;key.shadow.camera.right=key.shadow.camera.top=1.2;key.shadow.camera.near=.1;key.shadow.camera.far=8;key.shadow.bias=-.0004;key.shadow.normalBias=.015;scene.add(key);
const rim=new THREE.DirectionalLight('#c591b4',.85);rim.position.set(-1,2,-2);scene.add(rim);
const floor=new THREE.Mesh(new THREE.CircleGeometry(7,64),new THREE.MeshStandardMaterial({color:'#392b32',roughness:.94}));floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
const gltf=await new GLTFLoader().loadAsync('../models/lisa-first-rig.glb');const model=gltf.scene;scene.add(model);model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;}});
const mixer=new THREE.AnimationMixer(model),actions=new Map(gltf.animations.map(c=>[c.name,mixer.clipAction(c)]));
const skeleton=new THREE.SkeletonHelper(model);skeleton.visible=false;scene.add(skeleton);
let current=null,paused=false,speech=false,manualBlink=0,nextBlink=3.2,blinkStart=-10,last=performance.now(),elapsed=0,dirty=true;
const morphValues={Blink:0,MouthOpen:0,Smile:.15,Angry:0,Sad:0};
const faceExpression=createFaceExpressions(model),liveMorphs={Blink:0,Smile:.15,Angry:0,Sad:0};
function morph(name,value){liveMorphs[name]=value;model.traverse(o=>{const i=o.morphTargetDictionary?.[name];if(i!==undefined)o.morphTargetInfluences[i]=value;});faceExpression(liveMorphs.Smile,liveMorphs.Angry,liveMorphs.Sad,liveMorphs.Blink);dirty=true;}
const select=document.getElementById('action');for(const name of actions.keys()){const o=document.createElement('option');o.value=name;o.textContent=name;select.append(o);}
function play(name,immediate=false){const next=actions.get(name);if(!next)return;if(immediate)mixer.stopAllAction();next.reset().setEffectiveWeight(1).setLoop(THREE.LoopRepeat,Infinity);next.clampWhenFinished=false;if(name.startsWith('Turn')||['SitDown','StandUp','LieDown','GetUp'].includes(name)){next.setLoop(THREE.LoopOnce,1);next.clampWhenFinished=true;}next.play();if(current&&current!==next){if(immediate)current.stop();else current.crossFadeTo(next,.28,false);}current=next;select.value=name;model.position.set(0,name==='Lie'?.2:['Sit','Tea'].includes(name)?.23:0,0);controls.target.set(0,name==='Lie'?.15:['Sit','Tea'].includes(name)?.65:.97,name==='Lie'?-.5:0);document.getElementById('caption').textContent=name+' · Drag to orbit · Scroll to zoom · H hides controls';dirty=true;}
function setView(id){const view={front:[[0,1.03,3.4],[0,.96,0]],side:[[3.3,1.04,.04],[0,.96,0]],back:[[0,1.04,-3.4],[0,.96,0]],face:[[0,1.65,.76],[0,1.64,0]]}[id];if(!view)return;camera.position.set(...view[0]);controls.target.set(...view[1]);controls.update();dirty=true;}
select.onchange=()=>play(select.value);document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
document.querySelectorAll('[data-morph]').forEach(e=>e.oninput=()=>{morphValues[e.dataset.morph]=+e.value;morph(e.dataset.morph,+e.value);});
document.getElementById('faceToggle').onclick=()=>document.getElementById('faceControls').classList.toggle('open');
document.getElementById('pause').onclick=()=>{paused=!paused;document.getElementById('pause').textContent=paused?'Resume':'Pause';dirty=true;};
document.getElementById('blink').onclick=()=>{if(paused){morph('Blink',1);setTimeout(()=>morph('Blink',morphValues.Blink),180);}else blinkStart=elapsed;dirty=true;};document.getElementById('speech').onclick=()=>{speech=!speech;document.getElementById('speech').classList.toggle('active',speech);dirty=true;};
let wireframe=false;document.getElementById('bones').onclick=()=>{skeleton.visible=!skeleton.visible;dirty=true;};document.getElementById('wire').onclick=()=>{wireframe=!wireframe;const materials=new Set();model.traverse(o=>{if(o.isMesh)materials.add(o.material);});for(const m of materials)m.wireframe=wireframe;dirty=true;};
document.getElementById('room').onclick=()=>location.href='./room.html';document.getElementById('fullscreen').onclick=()=>document.documentElement.requestFullscreen().catch(()=>{});
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);dirty=true;});addEventListener('keydown',e=>{if(e.key.toLowerCase()==='h')document.body.classList.toggle('clean');});controls.addEventListener('change',()=>dirty=true);
function updateMorphs(t){if(!paused&&t>nextBlink){blinkStart=t;nextBlink=t+3.2+Math.random()*2.5;}const b=t-blinkStart;const auto=b>=0&&b<.20?Math.sin(piClamp(b/.2)*Math.PI):0;morph('Blink',Math.max(morphValues.Blink,auto));morph('MouthOpen',speech?(Math.sin(t*11)+Math.sin(t*17)*.35+1.3)/2.65:morphValues.MouthOpen);morph('Angry',select.value==='Angry'?.9:morphValues.Angry);morph('Sad',select.value==='Sad'?.8:morphValues.Sad);morph('Smile',morphValues.Smile);}
const piClamp=x=>Math.max(0,Math.min(1,x));
function frame(now){requestAnimationFrame(frame);const dt=Math.min((now-last)/1000,.08);last=now;if(document.hidden)return;if(!paused){elapsed+=dt;mixer.update(dt);updateMorphs(elapsed);dirty=true;}controls.update();if(dirty){renderer.render(scene,camera);dirty=false;}}
play('Idle',true);morph('Smile',.15);requestAnimationFrame(frame);document.getElementById('loader').remove();
window.lisaCharacter={ready:true,model,mixer,actions,scene,camera,renderer,controls,play,setView,morph,setPaused(value){paused=value;dirty=true;},get status(){let skinned=0,morphMeshes=0;model.traverse(o=>{if(o.isSkinnedMesh)skinned++;if(o.morphTargetDictionary)morphMeshes++;});return {clip:select.value,paused,skinnedMeshes:skinned,morphMeshes,clips:[...actions.keys()],triangles:renderer.info.render.triangles,drawCalls:renderer.info.render.calls};}};
