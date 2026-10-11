import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {RoundedBoxGeometry} from './vendor/RoundedBoxGeometry.js';
import {RoomEnvironment} from './vendor/RoomEnvironment.js';

// Metres, Y up. The design and future character anchors share this coordinate system.
const scene=new THREE.Scene();scene.background=new THREE.Color('#171821');
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.outputColorSpace=THREE.SRGBColorSpace;
let quality='auto',dirty=true,renderedFrames=0,shadowRefreshes=0;
function resizeRenderer(){const cap=quality==='crisp'?2:quality==='balanced'?1.25:1.75;const pixels=quality==='crisp'?4200000:quality==='balanced'?1800000:2600000;renderer.setPixelRatio(Math.min(devicePixelRatio,cap,Math.sqrt(pixels/(innerWidth*innerHeight))));renderer.setSize(innerWidth,innerHeight);dirty=true;}
resizeRenderer();
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.08;
document.body.prepend(renderer.domElement);
const camera=new THREE.PerspectiveCamera(65,innerWidth/innerHeight,.08,80);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.065;controls.minDistance=.7;controls.maxDistance=9;controls.maxPolarAngle=Math.PI*.56;controls.enablePan=false;
const pmrem=new THREE.PMREMGenerator(renderer);const environment=new RoomEnvironment();scene.environment=pmrem.fromScene(environment,.04).texture;scene.environmentIntensity=.34;environment.dispose();pmrem.dispose();
const room=new THREE.Group();room.name='Lisa_Private_Suite';scene.add(room);
let seed=2763;function rand(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}
function tex(type){const c=document.createElement('canvas');c.width=c.height=512;const ctx=c.getContext('2d');const img=ctx.createImageData(512,512);for(let y=0;y<512;y++)for(let x=0;x<512;x++){let v=0;if(type==='wood')v=174+5*Math.sin(x*.024+Math.sin(y*.01)*.3)+2*Math.sin(x*.18+y*.001)+(rand()-.5)*3;else if(type==='stone')v=166+9*Math.sin(x*.018+y*.024)+3*Math.sin(x*.11-y*.1)+(rand()-.5)*6;else v=198+(rand()-.5)*7+2*Math.sin(x*2.1)*Math.sin(y*2.1);const i=(y*512+x)*4;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=255;}ctx.putImageData(img,0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;}
const woodTex=tex('wood'),stoneTex=tex('stone'),fabricTex=tex('fabric');
const materialCache=new Map();function mat(color,opts={}){const key=color+'/'+Object.entries(opts).map(([k,v])=>k+':'+(v?.uuid??v)).join('/');if(!materialCache.has(key))materialCache.set(key,new THREE.MeshStandardMaterial({color,roughness:.75,...opts}));return materialCache.get(key);}
const walnut=mat('#775237',{map:woodTex,roughness:.56}),darkwood=mat('#49362b',{map:woodTex}),plaster=mat('#342d2a'),stone=mat('#5e5550',{map:stoneTex,roughness:.5}),brass=mat('#b89358',{metalness:.82,roughness:.32}),velvet=mat('#632231',{map:fabricTex,roughness:.97}),cream=mat('#e8d2b9',{map:fabricTex}),black=mat('#1d1a1d',{map:fabricTex}),rugMat=mat('#a58d75',{map:fabricTex,roughness:1}),white=mat('#e7e2d9',{roughness:.23}),glow=new THREE.MeshBasicMaterial({color:'#ffca7a'}),glass=new THREE.MeshPhysicalMaterial({color:'#c6d7d4',transparent:true,opacity:.055,roughness:.06,metalness:.1,depthWrite:false,side:THREE.DoubleSide});
const shells=[],ceilingObjects=[],fixtures=[],interactionTargets=[];
function mesh(geo,m,pos=[0,0,0],parent=room,name=''){const o=new THREE.Mesh(geo,m);o.position.set(...pos);o.name=name;o.castShadow=!m.transparent&&!m.isMeshBasicMaterial;o.receiveShadow=!m.isMeshBasicMaterial;parent.add(o);return o;}
function box(size,pos,m=walnut,parent=room,name=''){return mesh(new THREE.BoxGeometry(...size),m,pos,parent,name);}
const roundedCache=new Map();function round(size,pos,m=velvet,r=.08,parent=room,name=''){const key=size.join('/')+'/'+r;let g=roundedCache.get(key);if(!g){g=new RoundedBoxGeometry(...size,3,r);roundedCache.set(key,g);}return mesh(g,m,pos,parent,name);}
function cyl(r1,r2,h,pos,m=brass,parent=room,n=24){return mesh(new THREE.CylinderGeometry(r1,r2,h,n),m,pos,parent);}
function ball(size,pos,m,parent=room){const o=mesh(new THREE.SphereGeometry(1,20,12),m,pos,parent);o.scale.set(...size);return o;}
function tube(points,r,m=brass,parent=room,closed=false){return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)),closed),Math.max(points.length*5,20),r,6,closed),m,[0,0,0],parent);}
function torus(r,t,pos,m=brass,parent=room){return mesh(new THREE.TorusGeometry(r,t,8,32),m,pos,parent);}
function group(name,pos=[0,0,0],rotation=0){const g=new THREE.Group();g.name=name;g.position.set(...pos);g.rotation.y=rotation;room.add(g);return g;}
function contact(x,z,w,d){const c=document.createElement('canvas');c.width=c.height=64;const p=c.getContext('2d'),g=p.createRadialGradient(32,32,0,32,32,31);g.addColorStop(0,'rgba(0,0,0,.36)');g.addColorStop(1,'rgba(0,0,0,0)');p.fillStyle=g;p.fillRect(0,0,64,64);const o=mesh(new THREE.PlaneGeometry(w,d),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthWrite:false}),[x,.009,z]);o.rotation.x=-Math.PI/2;o.castShadow=false;}
// Structural shell, 18 cm thick. Right balcony opening is cut into the extruded wall shape.
box([12.36,.18,9.36],[0,-.09,0],darkwood,room,'floor_substrate').castShadow=false;
for(let i=0;i<24;i++){box([.488,.012,9],[i*.5-5.75,.006,0],walnut).castShadow=false;}
shells.push(box([12.36,3.6,.18],[0,1.8,-4.59],plaster));shells.push(box([.18,3.6,9.18],[-6.09,1.8,0],plaster));
const wallShape=new THREE.Shape();wallShape.moveTo(-4.5,0);wallShape.lineTo(4.5,0);wallShape.lineTo(4.5,3.6);wallShape.lineTo(-4.5,3.6);wallShape.closePath();const aperture=new THREE.Path();aperture.moveTo(-2.2,.08);aperture.lineTo(-2.2,2.85);aperture.lineTo(.7,2.85);aperture.lineTo(.7,.08);aperture.closePath();wallShape.holes.push(aperture);const right=mesh(new THREE.ExtrudeGeometry(wallShape,{depth:.18,bevelEnabled:false}),plaster,[6,0,0],room,'right_wall_balcony_aperture');right.rotation.y=-Math.PI/2;shells.push(right);
// Front boundary with a real 1.1 metre entrance, retained for in-room camera navigation.
shells.push(box([8.0,3.6,.18],[-2,1.8,4.59],plaster));shells.push(box([2.7,3.6,.18],[4.65,1.8,4.59],plaster));shells.push(box([1.3,1.2,.18],[2.65,3,4.59],plaster));
box([1.1,2.4,.045],[2.65,1.2,4.54],walnut,room,'entrance_door');box([.03,.22,.05],[3.05,1.08,4.50],brass);
const ceiling=box([12.36,.18,9.36],[0,3.69,0],darkwood,room,'ceiling');ceilingObjects.push(ceiling);
for(const x of [-5.86,5.86]){ceilingObjects.push(box([.025,.02,8.8],[x,3.48,0],glow));box([.06,.17,9],[x,3.54,0],walnut);}
ceilingObjects.push(box([11.75,.025,.025],[0,3.48,-4.37],glow));box([12,.14,.10],[0,3.55,-4.45],walnut);
for(const z of [-4.38,4.38])box([12,.10,.04],[0,.06,z],walnut);for(const x of [-5.88,5.88])box([.04,.1,9],[x,.06,0],walnut);
for(let i=0;i<28;i++)box([.065,2.65,.10],[.3+i*.13,1.6,-4.39],darkwood);
round([4.7,.055,3.6],[.6,.043,.3],rugMat,.06);contact(.6,.3,5.2,4);
// Warm, shared lighting manifest. Two shadowed area-like spot sources; other fixtures stay cheap.
const ambient=new THREE.HemisphereLight('#d8c9bb','#493226',1.0);scene.add(ambient);
function spot(id,pos,target,intensity=40,angle=1.15,shadow=false,color='#ffcf9b'){const l=new THREE.SpotLight(color,intensity,16,angle,.85,1.5);l.position.set(...pos);l.target.position.set(...target);scene.add(l,l.target);l.castShadow=shadow;if(shadow){l.shadow.mapSize.set(2048,2048);l.shadow.bias=-.00015;l.shadow.normalBias=.025;}fixtures.push({id,position:pos,target,intensity,color,light:l});return l;}
spot('main-ceiling',[0,3.38,.1],[0,0,-2],58,1.25,true);spot('bed-ceiling',[2.2,3.35,-2.7],[2.2,.5,-2.7],20,1.15,false);spot('wardrobe-ceiling',[-4.8,3.2,-2],[-5,.7,-2],20,1.25,false);spot('bathroom',[-1.8,3,-3],[-1.8,.5,-3],16,1,false);spot('balcony-blue',[6.7,3,-.5],[1,1,0],24,1.15,true,'#a7bada');
spot('balcony-fill',[7.35,2.85,-.75],[7.6,.4,-.75],10,1.2,false,'#b4c6df');
fixtures.forEach(f=>{if(f.light.castShadow){f.light.shadow.camera.near=.15;f.light.shadow.camera.far=16;f.light.shadow.bias=-.0004;f.light.shadow.normalBias=.035;f.light.shadow.radius=3;}});
function lamp(parent,x,z,y=1.2){cyl(.16,.18,.055,[x,.15,z],brass,parent);cyl(.017,.017,y-.2,[x,y/2+.1,z],brass,parent);cyl(.21,.26,.30,[x,y,z],mat('#d7b792',{side:THREE.DoubleSide}),parent);ball([.085,.085,.085],[x,y-.06,z],glow,parent);const light=new THREE.PointLight('#ffba6b',2.8,2.9,1.7);light.position.set(x,y-.1,z);parent.add(light);}
// Built-in wardrobe on the left rear wall. Clothing has volume, tailored silhouettes and hangers.
const wardrobe=group('wardrobe',[-4.65,0,-3.95]);box([2.4,2.92,.58],[0,1.46,0],darkwood,wardrobe);box([2.26,2.8,.035],[0,1.5,.31],walnut,wardrobe);
for(const x of [-1.2,-.12,.60,1.2])box([.055,2.96,.69],[x,1.48,.13],walnut,wardrobe);
for(const y of [.1,.47,.81,2.58,2.96])box([2.4,.06,.69],[0,y,.13],walnut,wardrobe);
box([2.3,.025,.018],[0,2.55,.47],glow,wardrobe);box([.98,.018,.018],[-.65,.76,.47],glow,wardrobe);
const pole=cyl(.012,.012,.98,[-.65,2.38,.3],brass,wardrobe);pole.rotation.z=Math.PI/2;
function garment(x,color,kind){const g=new THREE.Group();g.position.set(x,2.1,.25+(x+.96)*.28);wardrobe.add(g);tube([[-.12,.08,0],[0,.18,0],[.12,.08,0],[-.12,.08,0]],.007,brass,g);torus(.035,.005,[0,.23,0],brass,g);const sh=new THREE.Shape();if(kind==='top'){sh.moveTo(-.08,0);sh.lineTo(-.24,-.08);sh.lineTo(-.26,-.42);sh.lineTo(-.17,-.44);sh.lineTo(-.13,-.21);sh.lineTo(-.13,-.57);sh.lineTo(.13,-.57);sh.lineTo(.13,-.21);sh.lineTo(.17,-.44);sh.lineTo(.26,-.42);sh.lineTo(.24,-.08);sh.lineTo(.08,0);sh.quadraticCurveTo(0,-.07,-.08,0);}else{sh.moveTo(-.10,0);sh.lineTo(-.15,-.25);sh.lineTo(-.26,-.90);sh.quadraticCurveTo(0,-.96,.26,-.90);sh.lineTo(.15,-.25);sh.lineTo(.10,0);sh.quadraticCurveTo(0,-.12,-.10,0);}sh.closePath();mesh(new THREE.ExtrudeGeometry(sh,{depth:.023,bevelEnabled:true,bevelThickness:.018,bevelSize:.014,bevelSegments:2,steps:1}),mat(color,{map:fabricTex}),[0,0,0],g);}
garment(-.96,'#17171c','top');garment(-.76,'#2b2427','top');garment(-.53,'#2e151c','dress');garment(-.30,'#7d283b','dress');
for(let i=0;i<5;i++)round([.52,.09,.36],[.92,1.5+i*.1,.32],i%2?velvet:cream,.02,wardrobe);
for(const y of [.9,1.4,2.0])box([.56,.04,.60],[.92,y,.13],walnut,wardrobe);
for(let y=1;y<1.35;y+=.12)round([.5,.085,.36],[.92,y,.32],cream,.02,wardrobe);
for(let i=0;i<2;i++){round([.42,.3,.18],[.22,1.1+i*.65,.37],mat(i?'#683138':'#272323'),.035,wardrobe);const h=torus(.105,.014,[.22,1.28+i*.65,.37],brass,wardrobe);h.scale.x=1.2;}
for(const y of [.27,.61]){box([2.2,.24,.06],[0,y,.505],walnut,wardrobe);for(const x of [-.6,.6])box([.21,.012,.045],[x,y,.55],brass,wardrobe);}
function sandal(x,z,color){const g=new THREE.Group();g.position.set(x,.85,z);wardrobe.add(g);for(const sx of [-.09,.09]){round([.13,.025,.30],[sx,.025,0],mat(color),.024,g);cyl(.022,.018,.11,[sx,.04,-.09],black,g);tube([[sx-.06,.1,-.06],[sx-.06,.16,-.10],[sx+.06,.16,-.1],[sx+.06,.1,-.06]],.015,mat(color),g);tube([[sx-.055,.04,.07],[sx,.085,.10],[sx+.055,.04,.07]],.014,mat(color),g);}}
sandal(-.88,.35,'#181619');sandal(-.38,.35,'#78283a');sandal(.19,.35,'#d7c2a3');
const mirror=box([.43,2.4,.025],[.30,1.52,.53],mat('#b5b1aa',{metalness:.95,roughness:.12}),wardrobe,'wardrobe_mirror');for(const x of [.066,.533])box([.014,2.45,.028],[x,1.52,.55],glow,wardrobe);
// Whip stored on a brass hook beside the footwear. Decorative prop only.
const hook=cyl(.018,.018,.06,[1.14,1.3,.56],brass,wardrobe);hook.rotation.x=Math.PI/2;for(let i=0;i<4;i++)torus(.12+i*.017,.008,[1.13,1.07,.58+i*.012],black,wardrobe);tube([[1.25,1.08,.58],[1.29,.82,.58],[1.25,.62,.58]],.009,black,wardrobe);round([.025,.2,.025],[1.23,.69,.59],black,.008,wardrobe);
contact(-4.65,-3.7,2.6,1.2);
// Glass bathroom, clear entry and separate dry toilet/shower positions.
const bath=group('bathroom',[-1.7,0,-3.12]);box([2.56,.09,2.56],[0,.045,0],stone,bath);
box([2.55,2.95,.08],[0,1.52,-1.21],stone,bath);box([.08,2.95,2.5],[-1.25,1.52,0],stone,bath);
for(let y=.4;y<3;y+=.45)box([2.48,.012,.007],[0,y,-1.162],mat('#342e2b'),bath);for(let x=-.82;x<1.2;x+=.6)box([.008,2.84,.009],[x,1.48,-1.16],mat('#342e2b'),bath);
box([2.52,.025,.025],[0,2.98,1.23],brass,bath);box([.025,2.95,.025],[-1.25,1.51,1.23],brass,bath);box([.025,2.95,.025],[1.25,1.51,1.23],brass,bath);
box([1.5,2.88,.012],[-.5,1.51,1.23],glass,bath);box([.012,2.88,2.42],[1.25,1.51,0],glass,bath);
const bathDoor=new THREE.Group();bathDoor.name='bathroom_door';bathDoor.position.set(1.25,.07,1.25);bath.add(bathDoor);box([.93,2.86,.012],[-.465,1.43,0],glass,bathDoor);for(const x of [-.93,0])box([.015,2.86,.015],[x,1.43,0],brass,bathDoor);box([.02,.3,.055],[-.79,1.22,.02],brass,bathDoor);
const partition=box([.012,2.62,1.64],[-.15,1.40,-.37],glass,bath);partition.name='shower_partition';
tube([[-.7,.25,-1.08],[-.7,2.6,-1.08],[-.7,2.6,-.53]],.024,brass,bath);cyl(.19,.19,.035,[-.7,2.57,-.50],brass,bath);for(let i=0;i<8;i++)ball([.01,.006,.01],[-.7+Math.cos(i)*.12,2.548,-.5+Math.sin(i)*.12],black,bath);
const mixer=cyl(.06,.06,.035,[-.7,1.08,-1.075],brass,bath);mixer.rotation.x=Math.PI/2;tube([[-.65,1.08,-1.02],[-.45,.5,-1.02],[-.26,1.32,-1.02]],.008,brass,bath);round([.045,.16,.025],[-.27,1.4,-1.05],brass,.02,bath);
box([.55,.36,.10],[-.68,1.75,-1.1],darkwood,bath);for(let i=0;i<3;i++)cyl(.03,.03,.14,[-.86+i*.14,1.66,-1],mat(i?'#b09b7e':'#242123'),bath);box([.27,.005,.04],[-.7,.094,-.77],brass,bath);
// Ceramic toilet: hollow bowl profile, elliptical seat, tank and flush plate.
const toilet=new THREE.Group();toilet.name='toilet';toilet.position.set(.64,.095,-.45);bath.add(toilet);
const bowlProfile=[[.08,0],[.13,.03],[.14,.18],[.23,.25],[.24,.41],[.21,.43],[.18,.40],[.16,.31],[.06,.28]].map(p=>new THREE.Vector2(...p));const bowl=mesh(new THREE.LatheGeometry(bowlProfile,32),white,[0,0,0],toilet);bowl.scale.z=1.3;
const seat=torus(.215,.026,[0,.435,.01],white,toilet);seat.rotation.x=Math.PI/2;seat.scale.y=1.32;round([.41,.56,.15],[0,.39,-.25],white,.035,toilet);box([.09,.016,.045],[0,.686,-.25],brass,toilet);cyl(.033,.033,.15,[.97,.75,-.9],white,bath).rotation.z=Math.PI/2;
// Vanity outside the shower enclosure, with basin and practical supplies.
const vanity=group('washbasin',[-3.35,0,-2.30]);box([.95,.72,.58],[0,.39,0],walnut,vanity);box([1.03,.075,.66],[0,.80,0],stone,vanity);
const basinProfile=[[.08,0],[.19,.03],[.25,.15],[.24,.18],[.22,.17],[.18,.055],[.04,.03]].map(p=>new THREE.Vector2(...p));mesh(new THREE.LatheGeometry(basinProfile,32),white,[0,.845,.04],vanity);tube([[0,.84,-.20],[0,1.12,-.20],[0,1.17,-.12],[0,1.17,.015]],.018,brass,vanity);
round([.65,.83,.04],[0,1.70,-.275],mat('#aaa69c',{metalness:1,roughness:.12}),.08,vanity);for(const x of [-.345,.345])box([.012,.84,.018],[x,1.70,-.24],glow,vanity);
for(let i=0;i<2;i++)round([.36,.075,.30],[0,.20+i*.08,.08],cream,.02,vanity);cyl(.035,.035,.15,[.38,.92,.03],mat('#786544'),vanity);tube([[.38,1,.03],[.38,1.07,.03],[.43,1.07,.03]],.006,brass,vanity);box([.20,.20,.015],[-.2,.5,.3],walnut,vanity);contact(-3.35,-2.30,1.3,.9);
// Compact bed, sculpted duvet, rounded pillows and stitched trim.
const bed=group('bed',[2.03,0,-2.72]);round([2.30,.29,2.43],[0,.28,0],darkwood,.10,bed);round([2.15,.24,2.28],[0,.52,0],cream,.08,bed);round([2.43,1.18,.16],[0,.79,-1.13],velvet,.10,bed);
for(let x=-.9;x<=.9;x+=.3){tube([[x,.3,-1.026],[x,1.25,-1.026]],.004,mat('#53242e'),bed);}
function cloth(w,d,pos,m,parent,amp=.04){const g=new THREE.PlaneGeometry(w,d,48,40);g.rotateX(-Math.PI/2);const p=g.attributes.position;for(let i=0;i<p.count;i++){const x=p.getX(i),z=p.getZ(i);let y=Math.sin(x*12+z*2)*amp+Math.sin(z*15+x)*amp*.25;const edge=Math.max(Math.abs(x)/ (w/2),Math.abs(z)/(d/2));if(edge>.96)y-=Math.pow((edge-.96)/.04,2)*.12;p.setY(i,y);}g.computeVertexNormals();return mesh(g,m,pos,parent);}
cloth(2.24,1.92,[0,.80,.23],velvet,bed,.018);cloth(2.26,.48,[0,.82,-.50],mat('#903c4c',{map:fabricTex}),bed,.012);
for(const x of [-.55,.55]){const p=round([.89,.17,.50],[x,.76,-.81],cream,.10,bed);p.rotation.x=.15;const accent=round([.46,.16,.38],[x,.79,-.53],velvet,.065,bed);accent.rotation.y=x*.15;}
for(const x of [-1.55,1.55]){round([.55,.52,.58],[x,.29,-.82],walnut,.025,bed);box([.16,.012,.025],[x,.34,-.49],brass,bed);lamp(bed,x,-.90,1.1);box([.23,.045,.16],[x,.584,-.58],mat('#d1b087'),bed);box([.20,.022,.14],[x,.617,-.58],mat('#8a563e'),bed);}
contact(2.03,-2.72,2.65,2.65);
// Burgundy sofa: separate cushions, piping, pillows and brass feet.
const sofa=group('sofa',[4.28,0,1.18],-.30);round([2.42,.29,1.1],[0,.29,0],velvet,.10,sofa);round([2.35,.76,.28],[0,.84,-.47],velvet,.12,sofa);
for(const x of [-1.14,1.14]){round([.24,.58,1.10],[x,.70,0],velvet,.095,sofa);for(const z of [-.35,.35])cyl(.026,.032,.19,[x,.12,z],brass,sofa);}
for(const x of [-.55,.55]){round([1.02,.17,.83],[x,.50,.06],velvet,.07,sofa);tube([[x-.46,.576,-.30],[x+.46,.576,-.30],[x+.46,.576,.40],[x-.46,.576,.40],[x-.46,.576,-.30]],.005,mat('#b4606d'),sofa);const p=round([.53,.52,.15],[x,.85,-.29],x<0?cream:mat('#582332',{map:fabricTex}),.09,sofa);p.rotation.z=x*.12;}
round([.40,.06,.48],[-.68,.625,.07],cream,.025,sofa);round([.40,.06,.45],[-.68,.683,.07],cream,.025,sofa);contact(4.28,1.18,2.7,1.6);
const table=group('tea-table',[2.67,0,1.26]);cyl(.44,.44,.055,[0,.57,0],stone,table);cyl(.018,.018,.5,[0,.28,0],brass,table);cyl(.30,.30,.04,[0,.035,0],brass,table);
function cup(parent,x,z,y){cyl(.09,.07,.12,[x,y+.06,z],white,parent);cyl(.076,.076,.003,[x,y+.12,z],mat('#573222'),parent);cyl(.125,.125,.014,[x,y,z],white,parent);torus(.039,.012,[x+.097,y+.067,z],white,parent);}
cup(table,-.13,.1,.607);const teapot=ball([.13,.11,.13],[.1,.72,-.05],brass,table);cyl(.065,.065,.025,[.1,.826,-.05],brass,table);ball([.02,.02,.02],[.1,.854,-.05],brass,table);tube([[.21,.7,-.05],[.3,.75,-.05],[.33,.80,-.05]],.025,brass,table);torus(.085,.012,[-.03,.73,-.05],brass,table);contact(2.67,1.26,.85,.85);
// Bookshelves along right front wall, botanical dressing and softly lit wall art.
const shelves=group('bookshelf',[5.68,0,2.7],-Math.PI/2);box([2.4,2.6,.28],[0,1.3,0],darkwood,shelves);for(let y=.45;y<2.6;y+=.52){box([2.4,.045,.40],[0,y,.06],walnut,shelves);for(let i=0;i<8;i++){box([.045+rand()*.055,.18+rand()*.16,.16],[-1.07+i*.105,y+.14,.16],mat(['#743742','#b39165','#333538','#c0b092'][i%4]),shelves);}box([2.2,.014,.012],[0,y+.03,.255],glow,shelves);}
box([1.2,.90,.055],[2.06,2.30,-4.34],brass);box([1.13,.83,.06],[2.06,2.30,-4.30],mat('#42242b'));for(let i=0;i<8;i++){const o=box([.07,.5+rand()*.24,.013],[1.65+i*.11,2.25,-4.258],mat(i%2?'#99443b':'#6a3932'));o.rotation.z=-.3+rand()*.5;}
const leafGeo=new THREE.SphereGeometry(1,8,5);function plant(x,z,h=1.2,parent=room){cyl(.17,.12,.28,[x,.14,z],mat('#625345'),parent);const green=mat('#3d5943',{roughness:.9});for(let j=0;j<4;j++){const a=j*2.4,bx=x+Math.sin(a)*.12,bz=z+Math.cos(a)*.12;tube([[x,.24,z],[bx,h*.65,bz],[bx+.07,h,bz]],.008,mat('#4e4330'),parent);for(let i=0;i<7;i++){const y=.38+i*h*.083;const ax=bx+Math.sin(i*2.4+j)*.12,az=bz+Math.cos(i*2.4+j)*.12;const l=mesh(leafGeo,green,[ax,y,az],parent);l.scale.set(.12,.026,.23);l.rotation.set(.3,i*2.4+j,.5);}}}
plant(-5.42,.5,1.7);plant(5.45,-3.8,1.6);
// Real balcony opening and destination geometry. Curtains are pleated surfaces, not flat billboards.
const balcony=group('balcony',[6.16,0,-.75]);box([2.5,.18,3.0],[1.25,-.09,0],walnut,balcony);for(let i=0;i<14;i++)box([.17,.015,2.96],[.12+i*.18,.009,0],darkwood,balcony);box([.065,.065,3],[2.47,1.08,0],brass,balcony);for(let z=-1.4;z<=1.4;z+=.2)box([.035,1.1,.035],[2.47,.55,z],darkwood,balcony);for(const z of [-1.49,1.49])box([2.5,1.1,.04],[1.25,.55,z],darkwood,balcony);
for(const z of [-2.24,.74])box([.18,2.90,.06],[5.99,1.48,z],walnut);box([.18,.06,3.05],[5.99,2.88,-.75],walnut);box([.30,.08,3.1],[6.02,.04,-.75],stone);
const balconyDoor=group('balcony_door',[6.02,.08,-2.17]);box([.018,2.72,1.43],[0,1.36,.715],glass,balconyDoor);for(const z of [0,1.43])box([.035,2.72,.035],[0,1.36,z],darkwood,balconyDoor);for(const y of [0,2.72])box([.035,.035,1.43],[0,y,.715],darkwood,balconyDoor);box([.05,.24,.04],[-.03,1.15,1.24],brass,balconyDoor);box([.018,2.72,1.43],[6.02,1.44,.03],glass);
function curtain(z,width){const g=new THREE.PlaneGeometry(width,2.86,36,1);const p=g.attributes.position;for(let i=0;i<p.count;i++)p.setZ(i,Math.sin(p.getX(i)*38)*.055);g.computeVertexNormals();const o=mesh(g,mat('#5c2833',{map:fabricTex,side:THREE.DoubleSide}),[5.80,1.53,z]);o.rotation.y=-Math.PI/2;}
curtain(-2.54,.58);curtain(1.08,.63);const rod=cyl(.013,.013,4.2,[5.76,3.03,-.74]);rod.rotation.x=Math.PI/2;
plant(7.95,-1.8,1.75);plant(8.12,.2,1.65);plant(7.05,.56,1.25);
const outdoor=group('balcony-chair',[7.35,0,-1.05],Math.PI/2);round([.82,.18,.8],[0,.46,0],cream,.06,outdoor);round([.82,.6,.12],[0,.82,-.38],cream,.06,outdoor);for(const x of [-.4,.4])for(const z of [-.3,.3])cyl(.022,.022,.44,[x,.22,z],brass,outdoor);cyl(.32,.32,.04,[7.2,.47,.13],darkwood);cyl(.022,.022,.45,[7.2,.225,.13],brass);
// Privacy hedge and distant dusk gradient, no panoramic city background.
box([.15,2.5,3.4],[8.8,1.25,-.75],mat('#273c36'));for(let i=0;i<8;i++)plant(8.62,-2.16+i*.39,2.1);
const lanterns=[];for(const pos of [[6.55,.17,-2.02],[7.8,.17,.57]]){box([.18,.25,.18],pos,brass);ball([.07,.09,.07],[pos[0],pos[1]+.01,pos[2]],glow);}

// Semantic anchors ready for Lisa's rig. No avatar, voice, microphone or cloud calls in this preview.
const anchors={standing:{position:[0,0,.25],facing:0},sofa:{position:[4.1,.58,1.35],facing:-.30},bed:{position:[2.03,.73,-2.65],facing:0},wardrobe:{position:[-4.45,0,-2.55],facing:Math.PI},washbasin:{position:[-3.35,0,-1.6],facing:Math.PI},bathroom:{position:[-1.7,.095,-2.6],facing:Math.PI},balcony:{position:[7.1,0,-.7],facing:Math.PI/2}};
const views={room:{pos:[.05,1.85,4.18],target:[0,1.32,-2.20],fov:68,title:'Make yourself comfortable.',description:'A private suite, with room for Lisa.'},sofa:{pos:[1.45,1.38,3.52],target:[4.20,.85,1.1],fov:54,title:'Stay a little longer.',description:'The sofa · a place to sit and talk'},bed:{pos:[.45,1.62,-.10],target:[2.1,.83,-2.73],fov:61,title:'A softer end to the day.',description:'The bed · ready for lying-down and resting poses'},wardrobe:{pos:[-4.62,1.50,-1.20],target:[-4.64,1.42,-3.89],fov:62,title:'Her own little collection.',description:'Wardrobe · clothes, sandals and accessories'},bathroom:{pos:[-1.05,1.60,.50],target:[-1.65,1.35,-3.12],fov:58,title:'A moment to refresh.',description:'Glass bathroom · shower, toilet and washbasin'},balcony:{pos:[5.17,1.68,.45],target:[7.50,1.06,-.87],fov:63,title:'Step outside. Breathe.',description:'The balcony · quiet plants and evening air'}};
// Thin glass doors and trim do not need shadow-map redraws during opening.
for(const door of [bathDoor,balconyDoor])door.traverse(o=>{if(o.isMesh)o.castShadow=false;});
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;let move=null,current='room',tour=false,tourTimer=0,day=false,planMode=false,openBath=0,openBalcony=0,last=performance.now(),lightMove=null;
const lighting={exposure:1.08,environment:.34,ambient:1,window:24,balcony:10,power:1};
let lightsOn=true,doorOverride=null;
const lampLevels=[];room.traverse(o=>{if(o.isPointLight)lampLevels.push([o,o.intensity]);});
function lightTarget(){return lightsOn?(day?{exposure:1.22,environment:.46,ambient:1.3,window:55,balcony:19,power:1}:{exposure:1.08,environment:.34,ambient:1,window:24,balcony:10,power:1}):{exposure:1.05,environment:.06,ambient:.16,window:5,balcony:2,power:0};}
function setLighting(morning){day=morning;document.getElementById('lighting').textContent=day?'Morning':'Evening';lightMove={start:performance.now(),from:{...lighting},to:lightTarget()};dirty=true;}
function setLights(on){lightsOn=!!on;const b=document.getElementById('lights');if(b){b.textContent=lightsOn?'On':'Off';b.setAttribute('aria-pressed',String(lightsOn));}lightMove={start:performance.now(),from:{...lighting},to:lightTarget()};renderer.shadowMap.needsUpdate=true;dirty=true;}
function setDoors(bathroom,balcony){if(doorOverride&&doorOverride.bathroom===!!bathroom&&doorOverride.balcony===!!balcony)return;doorOverride={bathroom:!!bathroom,balcony:!!balcony};dirty=true;}
function moveCamera(position,target,fov=48,instant=false){move=null;tour=false;if(instant){camera.position.set(...position);controls.target.set(...target);camera.fov=fov;camera.updateProjectionMatrix();controls.update();}else move={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(...position),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(...target),fovFrom:camera.fov,fovTo:fov};dirty=true;}
function trackCamera(position,target,fov,dt){move=null;tour=false;const alpha=1-Math.exp(-3.2*dt);camera.position.lerp(new THREE.Vector3(...position),alpha);controls.target.lerp(new THREE.Vector3(...target),alpha);camera.fov=THREE.MathUtils.lerp(camera.fov,fov,alpha);camera.updateProjectionMatrix();dirty=true;}
function setQuality(value){if(!['auto','crisp','balanced'].includes(value))return;quality=value;document.getElementById('quality').value=value;resizeRenderer();}
function setView(id,instant=false){if(!views[id])return;if(planMode)renderer.shadowMap.needsUpdate=true;dirty=true;planMode=false;ceilingObjects.forEach(o=>o.visible=true);shells.forEach(o=>o.visible=true);current=id;const v=views[id];if(instant||reduced){camera.position.set(...v.pos);controls.target.set(...v.target);camera.fov=v.fov;camera.updateProjectionMatrix();controls.update();move=null;}else move={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(...v.pos),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(...v.target),fovFrom:camera.fov,fovTo:v.fov};document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===id));document.getElementById('place').textContent=v.title;document.getElementById('description').textContent=v.description;}
controls.addEventListener('start',()=>{move=null;tour=false;document.getElementById('tour').classList.remove('active');});
controls.addEventListener('change',()=>{dirty=true;});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
document.getElementById('lighting').onclick=()=>setLighting(!day);
document.getElementById('quality').onchange=e=>setQuality(e.target.value);
document.getElementById('fullscreen').onclick=async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen();}catch{document.getElementById('description').textContent='Use F11 for fullscreen in your browser.';}};
document.getElementById('tour').onclick=()=>{tour=!tour;tourTimer=performance.now()+5000;document.getElementById('tour').classList.toggle('active',tour);};
function showPlan(){tour=false;document.getElementById('tour').classList.remove('active');move=null;planMode=true;dirty=true;renderer.shadowMap.needsUpdate=true;ceilingObjects.forEach(o=>o.visible=false);shells.forEach(o=>o.visible=false);camera.position.set(0,12,.01);controls.target.set(0,0,0);camera.fov=58;camera.updateProjectionMatrix();controls.update();document.getElementById('place').textContent='The room layout';document.getElementById('description').textContent='Wardrobe · bathroom · bed · sofa · balcony';}
document.getElementById('plan').onclick=()=>planMode?setView('room'):showPlan();
addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select'))return;if(e.key.toLowerCase()==='h')document.body.classList.toggle('clean');if(e.key>='1'&&e.key<='6')setView(Object.keys(views)[Number(e.key)-1]);if(e.key==='Escape'&&planMode)setView('room');});
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();resizeRenderer();});
document.addEventListener('visibilitychange',()=>{last=performance.now();dirty=true;});
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();const box=document.getElementById('error');box.style.display='block';box.textContent='The graphics connection paused. Waiting to recover…';});
renderer.domElement.addEventListener('webglcontextrestored',()=>{document.getElementById('error').style.display='none';renderer.shadowMap.needsUpdate=true;dirty=true;});
renderer.domElement.addEventListener('dblclick',e=>{const pointer=new THREE.Vector2(e.clientX/innerWidth*2-1,-e.clientY/innerHeight*2+1),ray=new THREE.Raycaster();ray.setFromCamera(pointer,camera);const hits=ray.intersectObjects(room.children,true);if(!hits.length)return;let o=hits[0].object;while(o&&o!==room){if(views[o.name]){setView(o.name);break;}o=o.parent;}});
const frameHooks=new Set();
function frame(now){
 requestAnimationFrame(frame);const dt=Math.min((now-last)/1000,.1);last=now;if(document.hidden)return;
 if(move){const t=Math.min((now-move.start)/1700,1),s=t*t*t*(t*(t*6-15)+10);camera.position.lerpVectors(move.from,move.to,s);controls.target.lerpVectors(move.targetFrom,move.targetTo,s);camera.fov=THREE.MathUtils.lerp(move.fovFrom,move.fovTo,s);camera.updateProjectionMatrix();dirty=true;if(t===1)move=null;}
 if(tour&&now>tourTimer){const keys=Object.keys(views);setView(keys[(keys.indexOf(current)+1)%keys.length]);tourTimer=now+6000;}
 if(lightMove){const t=reduced?1:Math.min((now-lightMove.start)/850,1),s=t*t*(3-2*t);for(const k of Object.keys(lighting))lighting[k]=THREE.MathUtils.lerp(lightMove.from[k],lightMove.to[k],s);renderer.toneMappingExposure=lighting.exposure;scene.environmentIntensity=lighting.environment;ambient.intensity=lighting.ambient;fixtures.forEach(f=>{f.light.intensity=f.id==='balcony-blue'?lighting.window:f.id==='balcony-fill'?lighting.balcony:f.intensity*lighting.power;});lampLevels.forEach(([l,v])=>l.intensity=v*lighting.power);glow.color.set(lightsOn?'#ffca7a':'#292127');dirty=true;if(t===1)lightMove=null;}
 const bathTarget=doorOverride?(doorOverride.bathroom?1:0):(current==='bathroom'?1:0),balconyTarget=doorOverride?(doorOverride.balcony?1:0):(current==='balcony'?1:0);
 if(Math.abs(openBath-bathTarget)>.0001||Math.abs(openBalcony-balconyTarget)>.0001){openBath=reduced?bathTarget:THREE.MathUtils.damp(openBath,bathTarget,5,dt);openBalcony=reduced?balconyTarget:THREE.MathUtils.damp(openBalcony,balconyTarget,5,dt);if(Math.abs(openBath-bathTarget)<.0001)openBath=bathTarget;if(Math.abs(openBalcony-balconyTarget)<.0001)openBalcony=balconyTarget;bathDoor.rotation.y=-openBath*1.05;balconyDoor.rotation.y=-openBalcony*1.20;dirty=true;}
 for(const hook of frameHooks){if(hook(now,dt))dirty=true;}
 controls.update();if(dirty){if(renderer.shadowMap.needsUpdate)shadowRefreshes++;renderer.render(scene,camera);renderedFrames++;dirty=false;}
}
// Batch fixed opaque props by material and interaction area. Moving doors and glass stay separate.
function batchStatic(){room.updateMatrixWorld(true);const buckets=new Map(),removed=[];room.traverse(o=>{if(!o.isMesh||o.material.transparent||shells.includes(o)||ceilingObjects.includes(o))return;let p=o,area='room',dynamic=false;while(p&&p!==room){if(p===bathDoor||p===balconyDoor){dynamic=true;break;}if(views[p.name])area=p.name;p=p.parent;}if(dynamic)return;const key=area+'/'+o.material.uuid+'/'+o.castShadow+'/'+o.receiveShadow;let b=buckets.get(key);if(!b){b={area,material:o.material,shadow:o.castShadow,receive:o.receiveShadow,parts:[]};buckets.set(key,b);}b.parts.push(o);});let saved=0;for(const b of buckets.values()){if(b.parts.length<2)continue;const parts=b.parts.map(o=>{const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);return g;});const merged=new THREE.BufferGeometry();for(const attr of ['position','normal','uv']){if(parts.some(g=>!g.attributes[attr]))continue;const size=parts[0].attributes[attr].itemSize,total=parts.reduce((n,g)=>n+g.attributes[attr].array.length,0),array=new Float32Array(total);let at=0;for(const g of parts){array.set(g.attributes[attr].array,at);at+=g.attributes[attr].array.length;}merged.setAttribute(attr,new THREE.BufferAttribute(array,size));}const m=mesh(merged,b.material,[0,0,0],room,b.area);m.castShadow=b.shadow;m.receiveShadow=b.receive;m.userData.batch=true;for(const o of b.parts){o.removeFromParent();removed.push(o.geometry);}parts.forEach(g=>g.dispose());saved+=b.parts.length-1;}const remaining=new Set();room.traverse(o=>{if(o.isMesh)remaining.add(o.geometry);});new Set(removed).forEach(g=>{if(!remaining.has(g))g.dispose();});return {savedDrawObjects:saved,buckets:buckets.size};}
const optimization=batchStatic();setView('room',true);requestAnimationFrame(frame);
window.lisaRoom={ready:true,frameHooks,setView,showPlan,setLighting,setLights,setDoors,moveCamera,trackCamera,setQuality,anchors,views,scene,room,camera,controls,renderer,fixtures,ceilingObjects,shells,optimization,get status(){return {current,moving:!!move,lightingMoving:!!lightMove,lightsOn,doorOpenness:{bathroom:openBath,balcony:openBalcony},planMode,quality,pixelRatio:renderer.getPixelRatio(),renderedFrames,shadowRefreshes,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,geometries:renderer.info.memory.geometries,textures:renderer.info.memory.textures};}};
