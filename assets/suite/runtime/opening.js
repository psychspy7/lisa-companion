// Local-only cinematic entrance; real asset progress, explicit Enter gate.
const $=id=>document.getElementById(id);
export function loading(stage,progress){
 const p=Math.max(0,Math.min(100,Number(progress)||0));
 if($('load-note'))$('load-note').textContent=stage;
 if($('load-bar'))$('load-bar').style.width=p+'%';
 $('load-progress')?.setAttribute('aria-valuenow',String(Math.round(p)));
}
function dust(canvas){
 const ctx=canvas.getContext('2d');if(!ctx)return ()=>{};
 let id=0,last=0,w=1,h=1;const motes=Array.from({length:30},(_,i)=>({x:((i*73)%101)/101,y:((i*29)%97)/97,r:.6+(i%3)*.5,s:.006+(i%5)*.002}));
 const resize=()=>{w=canvas.clientWidth;h=canvas.clientHeight;canvas.width=Math.max(1,Math.round(w));canvas.height=Math.max(1,Math.round(h));};
 resize();addEventListener('resize',resize);
 function frame(now){
  id=requestAnimationFrame(frame);
  if(document.hidden||now-last<50)return;last=now;ctx.clearRect(0,0,w,h);
  const t=now/1000;
  for(const m of motes){const y=((m.y-t*m.s)%1+1)%1,x=(m.x+.012*Math.sin(t*.4+m.y*9))*w;
   ctx.beginPath();ctx.fillStyle='rgba(246,191,115,'+(.12+.20*Math.sin(m.x*21+t*.8)**2)+')';ctx.arc(x,y*h,m.r,0,Math.PI*2);ctx.fill();
  }
 }
 id=requestAnimationFrame(frame);
 return ()=>{cancelAnimationFrame(id);removeEventListener('resize',resize);ctx.clearRect(0,0,w,h);};
}
export async function opening(suite,actor,{onReady=()=>{}}={}){
 const loader=$('loader'),image=$('opening-art'),button=$('enter-lisa'),skip=$('skip-intro');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const character=window.lisaRoomCharacter;character?.setRunning(false);suite.controls.enabled=false;
 for(const el of document.querySelectorAll('header,#settings,#conversation'))el.inert=true;
 let phase='loading',timer=0,raf=0,stopDust=()=>{},finished=false,resolveEnter;
 const entered=new Promise(resolve=>{resolveEnter=resolve;});
 const state=value=>{phase=value;loader.dataset.stage=value;loader.setAttribute('aria-label',value==='ready'?'Lisa is ready. Enter your room.':'Lisa cinematic opening');};
 const ready=()=>{
  if(finished||phase==='ready'||phase==='entering'||phase==='entered')return;
  clearTimeout(timer);state('ready');button.disabled=false;skip.hidden=true;
  $('title-panel').hidden=false;button.focus({preventScroll:true});
 };
 const enter=()=>{
  if(phase!=='ready'||finished)return false;
  finished=true;state('entering');button.disabled=true;skip.hidden=true;clearTimeout(timer);stopDust();
  document.removeEventListener('keydown',key);
  const start=performance.now(),duration=reduced?0:1250;
  const frame=now=>{
   const t=duration?Math.min(1,(now-start)/duration):1,s=t*t*(3-2*t);
   loader.style.opacity=String(1-s);
   suite.moveCamera([2.3*(1-s),1.45,3.9-.25*s],[0,1.05,.25],54-5*s,true);
   if(t<1)raf=requestAnimationFrame(frame);
   else{
    loader.remove();character?.setRunning(true);suite.controls.enabled=true;
    for(const el of document.querySelectorAll('header,#settings,#conversation'))el.inert=false;
    phase='entered';window.lisaSessionEntered=true;resolveEnter();
   }
  };
  raf=requestAnimationFrame(frame);return true;
 };
 const key=e=>{
  if(e.key==='Escape'&&phase==='cinematic'){e.preventDefault();ready();}
  else if(e.key==='Enter'&&phase==='ready'){e.preventDefault();enter();}
 };
 const abandon=()=>{clearTimeout(timer);cancelAnimationFrame(raf);stopDust();document.removeEventListener('keydown',key);};
 window.addEventListener('pagehide',abandon,{once:true});
 window.lisaOpening={enter,skip:()=>{if(phase==="cinematic")ready();},get phase(){return phase;},get reducedMotion(){return reduced;}};
 button.onclick=enter;skip.onclick=ready;document.addEventListener('keydown',key);
 loading('Room ready',100);
 // Art failure leaves a usable black title screen, never blocks startup.
 try{if(image.decode)await image.decode();}catch{loader.classList.add('art-unavailable');}
 state(reduced?'ready':'cinematic');$('title-panel').hidden=false;
 if(reduced){button.disabled=false;skip.hidden=true;button.focus({preventScroll:true});}
 else{skip.hidden=false;stopDust=dust($('opening-embers'));timer=setTimeout(ready,8000);}
 // Update acknowledgment is independent of the human Enter gate.
 onReady();
 await entered;window.removeEventListener('pagehide',abandon);
}
