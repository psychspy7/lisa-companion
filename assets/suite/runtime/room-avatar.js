import * as THREE from 'three';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
import {parseCommand,buildRoute,nodes} from './room-commands.js';
import {createFaceExpressions} from './face-expression.js';
import {createCinematicCamera} from './cinematic-camera.js';
import {connectNative} from './native-bridge.js';
import {createPaintedAppearance} from './painted-appearance.js';
import {createSceneProps} from './scene-props.js';
import {loading,opening} from './opening.js';

const suite=window.lisaRoom,$=id=>document.getElementById(id);
function settings(open){$('settings').hidden=!open;$('settings-toggle').setAttribute('aria-expanded',String(open));}
$('settings-toggle').onclick=()=>settings($('settings').hidden);$('settings-close').onclick=()=>settings(false);
$('edit-lisa').onclick=()=>location.href='./index.html';
$('lights').onclick=()=>suite.setLights(!suite.status.lightsOn);
document.addEventListener('keydown',e=>{if(e.key==='Escape')settings(false);});
loading('Loading Lisa’s character…',35);
const gltf=await new GLTFLoader().loadAsync('../models/lisa-first-rig.glb',e=>loading('Loading Lisa’s character…',35+(e.total?e.loaded/e.total:0)*55));
const actor=gltf.scene;actor.name='Lisa_Animated_Companion';actor.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;}});suite.scene.add(actor);
const mixer=new THREE.AnimationMixer(actor),actions=new Map(gltf.animations.map(c=>[c.name,mixer.clipAction(c)])),morphs=new Map();
const faceExpression=createFaceExpressions(actor);
const cinematic=createCinematicCamera(suite,actor);
const props=createSceneProps(actor,suite);
const painted=await createPaintedAppearance(actor,suite);cinematic.setEnabled(false);
let pendingCycle=null,activeCycle=null;
actor.traverse(o=>{for(const [name,index] of Object.entries(o.morphTargetDictionary||{})){if(!morphs.has(name))morphs.set(name,[]);morphs.get(name).push([o,index]);}});
function morph(name,value){for(const [o,i] of morphs.get(name)||[])o.morphTargetInfluences[i]=value;}
let current=null,clip='Idle',running=true,force=true,elapsed=0,accumulator=0,nextBlink=3.4,blinkStart=-10,speechLevel=0,smoothedLevel=0,lastShadow=0;
let phase='idle',posture='standing',area='room',route=[],sequence=[],transition=null,desired=null,gestureEnd=0,expression='Smile',follow=true,drinking=false,recognition=null,listening=false;
let audio=null,audioContext=null,analyser=null,audioUrl=null;
const trace=[];function record(event){trace.push({event,time:elapsed,position:actor.position.toArray()});if(trace.length>100)trace.shift();}
function play(name,instant=false,once=false){const next=actions.get(name)||actions.get('Idle');if(instant)mixer.stopAllAction();next.reset().setEffectiveWeight(1).setLoop(once?THREE.LoopOnce:THREE.LoopRepeat,once?1:Infinity);next.clampWhenFinished=once;next.play();if(current&&current!==next&&!instant)current.crossFadeTo(next,.22,false);current=next;clip=next.getClip().name;force=true;suite.renderer.shadowMap.needsUpdate=true;}
function reply(text){$('reply').textContent=text;if($('speak').checked&&'speechSynthesis' in window){speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.rate=.95;u.onstart=()=>{speechLevel=.28;};u.onend=u.onerror=()=>{speechLevel=0;};speechSynthesis.speak(u);}}
function activity(text){$('activity').textContent=text;}
function turnYaw(a,b,t){return a+(THREE.MathUtils.euclideanModulo(b-a+Math.PI,Math.PI*2)-Math.PI)*t;}
function beginTransition(step){transition={...step,start:elapsed,from:actor.position.clone(),yawFrom:actor.rotation.y};phase=step.phase;record(step.phase);play(step.clip,true,true);activity(step.label);}
function nextStep(){if(sequence.length){beginTransition(sequence.shift());return;}transition=null;if(pendingCycle&&!desired){const value=pendingCycle;pendingCycle=null;startCycle(value);return;}phase=posture==='lying'?'sleeping':posture==='seated'?'seated':'idle';play(posture==='lying'?'Lie':posture==='seated'?(drinking?'Tea':'Sit'):'Idle');if(desired){const d=desired;desired=null;travel(d);}}
const sofaSeat=[4.10,.23,1.35],sofaStand=[3.90,0,2.18],bedSeat=[2.03,.32,-1.57],bedLie=[2.03,.91,-1.65];
function standingSteps(){
 const steps=[];
 if(posture==='lying'){steps.push({phase:'getting-up',clip:'GetUp',duration:2.8,to:bedSeat,yaw:0,label:'Sitting up…',end(){posture='seated';}});steps.push({phase:'standing-up',clip:'StandUp',duration:1.4,to:nodes.bed,yaw:0,label:'Getting out of bed…',end(){posture='standing';}});}
 else if(posture==='seated')steps.push({phase:'standing-up',clip:'StandUp',duration:1.4,to:area==='bed'?nodes.bed:area==='toilet'?nodes.toiletFront:sofaStand,yaw:area==='bed'?0:-.30,label:'Standing up…',end(){posture='standing';}});
 return steps;
}
function startWalking(d){route=buildRoute(actor.position.toArray(),d.destination).map(p=>new THREE.Vector3(...p));phase='walking';record('walking:'+d.destination);play('Walk');activity('Walking to the '+d.destination+'…');if(follow)suite.moveCamera([.05,1.9,4.18],[0,1.2,-1.3],65);if(!route.length)arrive(d);}
function travel(d){if(transition){desired=d;reply('One moment, Sir. Let me finish getting settled.');return;}
 drinking=false;cup.visible=false;gestureEnd=0;desired=null;route=[];
 const steps=standingSteps();sequence=steps;if(steps.length){const last=steps.at(-1),end=last.end;last.end=()=>{end();startWalking(d);};nextStep();}
 else startWalking(d);
 pendingDestination=d;
}
let pendingDestination=null;
function arrive(d){route=[];area=d.destination;record('arrived:'+area);if(follow)suite.setView(area==='washbasin'?'wardrobe':area);
 if(area==='sofa'){sequence=[{phase:'sitting-down',clip:'SitDown',duration:1.4,to:sofaSeat,yaw:-.30,label:'Settling onto the sofa…',end(){posture='seated';drinking=d.activity==='tea';cup.visible=drinking;if(drinking)pendingCycle='tea_sip';activity(drinking?'Tea on the sofa':'Sitting with you');}}];nextStep();}
 else if(area==='bed'){sequence=[{phase:'sitting-down',clip:'SitDown',duration:1.4,to:bedSeat,yaw:0,label:'Sitting on the edge of the bed…',end(){posture='seated';}},
  {phase:'lying-down',clip:'LieDown',duration:2.8,to:bedLie,yaw:0,label:'Getting comfortable…',end(){posture='lying';suite.setLights(false);activity('Resting · room lights off');reply('Goodnight, Sir. Lights out.');}}];nextStep();}
 else if(area==='toilet'){sequence=[{phase:'sitting-down',clip:'SitDown',duration:1.4,to:nodes.toilet,yaw:0,label:'Settling down…',end(){posture='seated';activity('A private moment');}}];nextStep();}
 else{phase='idle';posture='standing';actor.rotation.y=area==='wardrobe'||area==='washbasin'?Math.PI:area==='balcony'?Math.PI/2:0;play('Idle');activity('At the '+area);if(pendingCycle){const name=pendingCycle;pendingCycle=null;startCycle(name);}}
}
function stop(){pendingCycle=null;activeCycle=null;desired=null;pendingDestination=null;route=[];gestureEnd=0;if(props.status.held!=='whip')props.hold(null);stopAudio();speechSynthesis?.cancel();if(transition){sequence=[];transition.end=()=>{posture=transition.clip==='LieDown'?'lying':transition.clip==='StandUp'?'standing':'seated';};reply('Okay, Sir. I’ll finish this movement and stay here.');}
 else{phase=posture==='lying'?'sleeping':posture==='seated'?'seated':'idle';play(posture==='lying'?'Lie':posture==='seated'?'Sit':'Idle');drinking=false;cup.visible=false;reply('Okay, Sir. Staying here.');activity('Stopped');}record('stop');}
function dispatch(d){
 if(!d||typeof d!=='object')return false;
 if(d.type==='lights'&&typeof d.on==='boolean'){suite.setLights(d.on);reply(d.on?'Lights on, Sir.':'Lights off. Cozy enough?');return true;}
 if(d.type==='stop'){stop();return true;}
 if(d.type==='move'&&Object.hasOwn(nodes,d.destination)&&['room','sofa','bed','wardrobe','bathroom','balcony','washbasin','shower','toilet'].includes(d.destination)){
  if(d.destination==='bed')suite.setLights(true);reply(d.destination==='bed'?'Alright, Sir. I’ll get comfortable.':'On my way to the '+d.destination+', Sir.');travel(d);return true;
 }
 if(d.type==='wake'){suite.setLights(true);travel({type:'move',destination:'room'});reply('I’m up, Sir. What’s the plan?');return true;}
 if(d.type==='gesture'&&['Wave','Command','Listen'].includes(d.name)){
  if(phase==='walking'||transition){reply('Let me get there first, Sir.');return false;}
  if(posture!=='standing'){reply('I’ll stand up first, Sir.');desired={type:'move',destination:'room'};travel(desired);return true;}
  play(d.name);phase='gesture';gestureEnd=elapsed+actions.get(d.name).getClip().duration;reply('Hey, Sir.');record('gesture:'+d.name);return true;
 }
 if(d.type==='expression'&&['Angry','Sad','Smile'].includes(d.name)){expression=d.name;force=true;reply(d.name==='Angry'?'That look says enough, Sir.':d.name==='Sad'?'A quieter moment.':'There. Happy, Sir?');return true;}
 if(d.type==='empty')return false;
 reply(d.type==='clarify'?'Where, Sir—sofa, bed, wardrobe, bathroom or balcony?':'Try a room command, Sir—“go to the balcony”, “have tea”, or “lights off”.');return false;
}

function cycleStage(){const stage=activeCycle.stages[0];play(stage.clip,false,true);phase=activeCycle.name==='exercise'?'exercise':'prop-action';activeCycle.until=elapsed+(stage.seconds||actions.get(stage.clip)?.getClip().duration||3);stage.start?.();record('action:'+stage.clip);activity(stage.label||activeCycle.name.replaceAll('_',' '));}
function runCycle(name,stages){activeCycle={name,stages,until:elapsed};cycleStage();}
function startCycle(name){
 const stage=(clip,extra={})=>({clip,...extra});
 const simple={hair_touch:'HairTouch',hair_tuck:'HairTuck',stretch:'Stretch',wind:'Wind',command:'Command',listen:'Listen',wave:'Wave',kiss:'Kiss',dry_hair:'DryHair'};
 if(simple[name]){runCycle(name,[stage(simple[name])]);return;}
 if(name==='sandals_off')runCycle(name,[stage('ReachAnkle'),stage('Unbuckle'),stage('SandalRemove',{end:()=>props.sandals(false)})]);
 else if(name==='sandals_on')runCycle(name,[stage('ReachAnkle'),stage('SandalWear',{end:()=>props.sandals(true)})]);
 else if(name==='exercise')runCycle(name,[stage('Stretch'),stage('Exercise',{seconds:9,start:()=>{actions.get('Exercise').setLoop(THREE.LoopRepeat,3);props.perspiration(.7);}}),stage('WipeSweat',{start:()=>props.hold('towel'),end:()=>props.hold(null)}),stage('DrinkWater',{start:()=>props.hold('bottle'),end:()=>props.hold(null)})]);
 else if(name==='wipe_sweat')runCycle(name,[stage('WipeSweat',{start:()=>props.hold('towel'),end:()=>{props.hold(null);props.perspiration(0);}})]);
 else if(name==='drink_water')runCycle(name,[stage('DrinkWater',{start:()=>props.hold('bottle'),end:()=>props.hold(null)})]);
 else if(['phone','read','smoke','brush_teeth'].includes(name)){const id={phone:'phone',read:'book',smoke:'cigarette',brush_teeth:'brush'}[name];runCycle(name,[stage({phone:'Phone',read:'Read',smoke:'Smoke',brush_teeth:'BrushTeeth'}[name],{start:()=>props.hold(id),end:()=>props.hold(null)})]);}
 else if(name==='wash_hands')runCycle(name,[stage('WashHands',{end:()=>props.perspiration(0)})]);
 else if(name==='covered_bath')runCycle(name,[stage('RobePrep'),stage('CoveredBath'),stage('Rinse'),stage('DryHair',{start:()=>props.hold('towel'),end:()=>{props.hold(null);props.perspiration(0);}})]);
 else if(name==='sleeves_off'||name==='sleeves_on')runCycle(name,[stage(name==='sleeves_off'?'SleevesOff':'SleevesOn',{end:()=>props.sleeves(name==='sleeves_on')})]);
 else if(name==='skirt_change')runCycle(name,[stage('WardrobeReach'),stage('SkirtChange',{end:()=>actor.traverse(o=>{if(o.name.startsWith('Pleated_skirt')&&o.material)o.material.color?.set('#76404b');})})]);
 else if(name==='whip')runCycle(name,[stage('Retrieve',{end:()=>{props.hold('whip');activeCycle=null;pendingCycle='whip_use';travel({type:'move',destination:'room'});}})]);
 else if(name==='whip_use')runCycle(name,[stage('WhipReady'),stage('WhipStroke'),stage('WhipReset')]);
 else if(name==='put_whip_back')runCycle(name,[stage('ReturnProp',{end:()=>props.hold(null)})]);
 else if(name==='tea_sip'){drinking=true;cup.visible=true;runCycle(name,[stage('Sip',{end:()=>{drinking=true;}})]);}
 else{activity('Ready');}
}
function perform(name){
 const maps={room:{type:'move',destination:'room'},sofa:{type:'move',destination:'sofa'},tea:{type:'move',destination:'sofa',activity:'tea'},sleep:{type:'move',destination:'bed'},wake:{type:'wake'},toilet:{type:'move',destination:'toilet'},bathroom:{type:'move',destination:'bathroom'},balcony:{type:'move',destination:'balcony'},wardrobe:{type:'move',destination:'wardrobe'},lights_on:{type:'lights',on:true},lights_off:{type:'lights',on:false},stop:{type:'stop'}};
 if(maps[name])return dispatch(maps[name]);
 if(['angry','sad','smile'].includes(name))return dispatch({type:'expression',name:name[0].toUpperCase()+name.slice(1)});
 const valid=['wave','command','listen','kiss','sandals_off','sandals_on','exercise','stretch','wipe_sweat','drink_water','whip','put_whip_back','brush_teeth','phone','read','hair_touch','hair_tuck','wind','sleeves_off','sleeves_on','skirt_change','covered_bath','dry_hair','smoke'];
 if(!valid.includes(name))return false;
 // Complete a posture transition before the next route; never teleport.
 const destination=['whip','put_whip_back','sleeves_off','sleeves_on','skirt_change'].includes(name)?'wardrobe':['covered_bath'].includes(name)?'shower':['brush_teeth'].includes(name)?'washbasin':['phone','read'].includes(name)?'sofa':'room';
 pendingCycle=name;if(transition||phase==='walking'){desired={type:'move',destination};return true;}
 activeCycle=null;if(posture!=='standing'||area!==destination)travel({type:'move',destination});else{pendingCycle=null;startCycle(name);}return true;
}

function command(text){const action=parseCommand(text);if(action.type==='action')return perform(action.name);return dispatch(action);}
$('composer').onsubmit=e=>{e.preventDefault();const text=$('message').value.trim();if(!text)return;command(text);$('message').value='';};
$('follow').onchange=e=>{follow=e.target.checked;cinematic.setEnabled(follow);};suite.controls.addEventListener('start',()=>{follow=false;cinematic.setEnabled(false);$('follow').checked=false;});
$('motion-lisa').onclick=()=>{running=!running;$('motion-lisa').textContent=running?'On':'Off';force=true;};

// A small real mesh prop follows the wrist position; it stays upright with gravity.
const cup=new THREE.Group(),porcelain=new THREE.MeshStandardMaterial({color:'#e9d7cd',roughness:.28});
cup.add(new THREE.Mesh(new THREE.CylinderGeometry(.035,.027,.055,24),porcelain));
const handle=new THREE.Mesh(new THREE.TorusGeometry(.018,.005,8,18),porcelain);handle.position.set(.038,0,0);cup.add(handle);
const tea=new THREE.Mesh(new THREE.CircleGeometry(.030,24),new THREE.MeshStandardMaterial({color:'#683c25',roughness:.3}));tea.rotation.x=-Math.PI/2;tea.position.y=.028;cup.add(tea);cup.visible=false;suite.scene.add(cup);
const hand=(actor.getObjectByName('Hand.L')||actor.getObjectByName('HandL')||actor.getObjectByName('Hand_L')),handPosition=new THREE.Vector3(),samples=new Uint8Array(256);
function stopAudio(){if(audio){audio.pause();audio.src='';audio=null;}if(audioContext){audioContext.close();audioContext=null;}analyser=null;if(audioUrl){URL.revokeObjectURL(audioUrl);audioUrl=null;}speechLevel=0;$('audio-lisa').textContent='Test local audio';force=true;}
$('audio-lisa').onclick=()=>{if(audio&&!audio.paused)stopAudio();else $('voice-file').click();};
$('voice-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;stopAudio();audioUrl=URL.createObjectURL(file);audio=new Audio(audioUrl);audioContext=new AudioContext();analyser=audioContext.createAnalyser();analyser.fftSize=256;audioContext.createMediaElementSource(audio).connect(analyser);analyser.connect(audioContext.destination);audio.onended=stopAudio;try{await audioContext.resume();await audio.play();$('audio-lisa').textContent='Stop audio';activity('Local audio · sound-driven mouth');}catch{stopAudio();reply('That audio file could not play. Try WAV or MP3.');}e.target.value='';};
function endListening(){listening=false;clearTimeout(restartTimer);recognition?.abort();$('mic').setAttribute('aria-pressed','false');$('mic').setAttribute('aria-label','Start voice commands');}
let restartTimer=0;
$('mic').onclick=()=>{if(listening){endListening();activity('Microphone off');return;}
 const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Recognition){reply('Voice commands are unavailable in this browser. You can still type here.');return;}
 recognition=new Recognition();recognition.lang='en-IN';recognition.continuous=true;recognition.interimResults=false;
 recognition.onresult=e=>{for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal){if(speechSynthesis?.speaking)continue;command(e.results[i][0].transcript);}};
 recognition.onerror=e=>{endListening();reply(e.error==='not-allowed'?'Microphone permission was denied. Enable it in your browser to use voice.':'Voice recognition stopped ('+e.error+'). Type a command or tap the mic to retry.');};
 recognition.onend=()=>{if(listening&&!document.hidden)restartTimer=setTimeout(()=>{try{recognition.start();}catch{endListening();}},350);};
 listening=true;$('mic').setAttribute('aria-pressed','true');$('mic').setAttribute('aria-label','Stop voice commands');activity('Listening · tap the mic to stop');try{recognition.start();}catch{endListening();reply('Microphone could not start. Try typing a command.');}
};
function update(now,delta){actor.visible=!suite.status.planMode;accumulator+=delta;if(accumulator<1/30&&!force)return false;const dt=Math.min(accumulator,.12);accumulator=0;let changed=force;force=false;
 if(running){elapsed+=dt;mixer.update(dt);changed=true;
  if(activeCycle&&elapsed>=activeCycle.until){const stage=activeCycle.stages.shift();stage.end?.();if(activeCycle?.stages.length)cycleStage();else if(activeCycle){activeCycle=null;phase=posture==='seated'?'seated':'idle';play(posture==='seated'?(drinking?'Tea':'Sit'):'Idle');record('action-complete');}}
  props.update(now);
  if(transition){const t=Math.min(1,(elapsed-transition.start)/transition.duration),s=t*t*(3-2*t);actor.position.lerpVectors(transition.from,new THREE.Vector3(...transition.to),s);actor.rotation.y=turnYaw(transition.yawFrom,transition.yaw,s);if(t===1){const end=transition.end;end?.();transition=null;if(phase!=='walking')nextStep();}}
  else if(route.length){const p=route[0],v=new THREE.Vector3().subVectors(p,actor.position),distance=v.length(),step=.76*dt;
   if(distance<=step){actor.position.copy(p);route.shift();if(!route.length&&pendingDestination){const d=pendingDestination;pendingDestination=null;arrive(d);}}
   else{actor.position.addScaledVector(v.normalize(),step);const yaw=Math.atan2(v.x,v.z);actor.rotation.y=turnYaw(actor.rotation.y,yaw,Math.min(1,dt*7));}
  }
  if(gestureEnd&&elapsed>=gestureEnd){gestureEnd=0;phase='idle';play('Idle');}
  if(elapsed>nextBlink){blinkStart=elapsed;nextBlink=elapsed+3.1+Math.random()*2.2;}
  const b=elapsed-blinkStart,blink=posture==='lying'?1:b>=0&&b<.2?Math.sin(b/.2*Math.PI):0;morph('Blink',blink);faceExpression(expression==='Smile'?.4:0,expression==='Angry'?.85:0,expression==='Sad'?.85:0,blink);
  morph('Smile',expression==='Smile'?.4:0);morph('Angry',expression==='Angry'?.85:0);morph('Sad',expression==='Sad'?.85:0);
  if((route.length||transition||phase==='gesture')&&now-lastShadow>200){suite.renderer.shadowMap.needsUpdate=true;lastShadow=now;}
 }
 painted.update(dt,{phase,posture,area,cycle:activeCycle?.name,elapsed,barefoot:props.status.barefoot,sleevesOff:props.status.sleevesOff},posture==='lying'?1:(elapsed-blinkStart)>=0&&(elapsed-blinkStart)<.2?Math.sin((elapsed-blinkStart)/.2*Math.PI):0,smoothedLevel,expression);
 if(running&&follow)cinematic.update(now,dt,{phase,area});
 suite.setDoors(actor.position.x<-.45&&actor.position.x>-1.5&&actor.position.z<-.85,actor.position.x>4.65&&actor.position.z<-.60);
 if(drinking&&hand){actor.updateMatrixWorld(true);hand.getWorldPosition(handPosition);cup.position.copy(handPosition).add(new THREE.Vector3(-.015,.005,.025));}
 if(analyser){analyser.getByteTimeDomainData(samples);let sum=0;for(const v of samples)sum+=((v-128)/128)**2;speechLevel=Math.min(1,Math.max(0,Math.sqrt(sum/samples.length)-.008)*6);changed=true;}
 smoothedLevel=THREE.MathUtils.damp(smoothedLevel,speechLevel,18,dt);morph('MouthOpen',smoothedLevel);if(smoothedLevel>.0001)changed=true;return changed;
}
actor.position.set(...nodes.room);play('Idle',true);suite.setDoors(false,false);suite.moveCamera([0,1.45,3.65],[0,1.05,.25],49,true);suite.frameHooks.add(update);
document.addEventListener('visibilitychange',()=>{if(document.hidden){endListening();speechSynthesis?.cancel();stopAudio();}});
addEventListener('pagehide',()=>{endListening();stopAudio();speechSynthesis?.cancel();suite.frameHooks.delete(update);});
addEventListener('lisa-action',e=>dispatch(e.detail));
window.lisaRoomCharacter={ready:true,actor,mixer,actions,command,dispatch,perform,update,play,stopAudio,stop,setSpeechLevel(level){speechLevel=THREE.MathUtils.clamp(level,0,1);if(!running){smoothedLevel=speechLevel;morph('MouthOpen',speechLevel);}force=true;},setRunning(value){running=!!value;force=true;},setEmotion(value){expression=['angry','commanding'].includes(value)?'Angry':['sad','crying'].includes(value)?'Sad':'Smile';force=true;},get status(){return {appearance:painted.status,props:props.status,cycle:activeCycle?.name||null,pendingCycle,clip,phase,posture,area,running,walking:route.length>0,transition:transition?.phase||null,position:actor.position.toArray(),speechLevel,smoothedLevel,elapsed,listening,drinking,trace:[...trace]};}};

loading('Preparing your room…',98);const native=await connectNative(window.lisaRoomCharacter);await opening(suite,actor,{onReady:()=>native?.ready()});cinematic.setEnabled(follow);native?.entered();
