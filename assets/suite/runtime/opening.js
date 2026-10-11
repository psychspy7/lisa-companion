export function loading(stage,progress){const note=document.getElementById('load-note'),bar=document.getElementById('load-bar');if(note)note.textContent=stage;if(bar)bar.style.width=Math.max(0,Math.min(100,progress))+'%';}
export async function opening(suite,actor){
 loading('Ready',100);const loader=document.getElementById('loader');loader.classList.add('ready');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(reduced){loader.remove();return;}
 const skip=document.getElementById('skip-intro');skip.hidden=false;let end=false;skip.onclick=()=>{end=true;};
 // Asset readiness precedes this deliberate two-shot reveal.
 await new Promise(resolve=>{const start=performance.now();const frame=now=>{const t=Math.min(1,(now-start)/2400);loader.style.opacity=String(Math.max(0,1-t*2));suite.moveCamera([2.3*(1-t),1.7-.25*t,4.10-.45*t],[0,1.14,.25],54-5*t,true);if(t===1||end){loader.remove();resolve();}else requestAnimationFrame(frame);};requestAnimationFrame(frame);});
}
