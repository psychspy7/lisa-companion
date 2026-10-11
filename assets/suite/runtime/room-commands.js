// Closed room-action vocabulary. No generated text is evaluated as code.
export function parseCommand(text){
 const t=String(text).normalize('NFKC').toLowerCase().replace(/[.,!?]/g,' ').replace(/\s+/g,' ').trim();
 if(!t)return {type:'empty'};
 if(/\b(stop|ruk|ruko|wait|cancel)\b/.test(t))return {type:'stop'};
 if(/\b(light|lights|lamp|lamps|batti|roshni)\b/.test(t)){
  if(/\b(off|band|bujha)\b/.test(t))return {type:'lights',on:false};
  if(/\b(on|chalu|jala)\b/.test(t))return {type:'lights',on:true};
 }
 const actions=[[/sandals? (off|remove)|remove.*sandals?|unbuckle/,'sandals_off'],[/sandals? on|wear.*sandals?/,'sandals_on'],[/put.*whip.*back|return.*whip/,'put_whip_back'],[/whip/,'whip'],[/exercise|workout|squat/,'exercise'],[/stretch/,'stretch'],[/wipe.*sweat/,'wipe_sweat'],[/drink.*water/,'drink_water'],[/wash.*hands/,'wash_hands'],[/brush.*teeth/,'brush_teeth'],[/read.*book/,'read'],[/phone/,'phone'],[/tuck.*hair/,'hair_tuck'],[/touch.*hair/,'hair_touch'],[/wind/,'wind'],[/sleeves?.*off/,'sleeves_off'],[/sleeves?.*on/,'sleeves_on'],[/change.*skirt/,'skirt_change'],[/shower|covered bath/,'covered_bath'],[/dry.*hair/,'dry_hair'],[/kiss/,'kiss']];
 for(const [pattern,name] of actions)if(pattern.test(t))return {type:'action',name};
 if(/\b(wake|utho|uth|jago)\b/.test(t))return {type:'wake'};
 if(/\b(sleep|bed|soja|sona|sone|so ja)\b/.test(t))return {type:'move',destination:'bed',activity:'sleep'};
 if(/\btoilet\b/.test(t))return {type:'move',destination:'toilet'};
 if(/\b(bathroom|washroom|bath)\b/.test(t))return {type:'move',destination:'bathroom'};
 if(/\b(basin|wash hands|sink)\b/.test(t))return {type:'move',destination:'washbasin'};
 if(/\b(wardrobe|closet|clothes|almari)\b/.test(t))return {type:'move',destination:'wardrobe'};
 if(/\b(balcony|outside|bahar)\b/.test(t))return {type:'move',destination:'balcony'};
 if(/\b(tea|chai|coffee)\b/.test(t))return {type:'move',destination:'sofa',activity:'tea'};
 if(/\b(sofa|couch|sit|baith|baitho)\b/.test(t))return {type:'move',destination:'sofa'};
 if(/\b(wave|hello|hi|hey)\b/.test(t))return {type:'gesture',name:'Wave'};
 if(/\b(angry|gussa)\b/.test(t))return {type:'expression',name:'Angry'};
 if(/\b(sad|dukhi)\b/.test(t))return {type:'expression',name:'Sad'};
 if(/\b(smile|happy|muskur[a-z]*)\b/.test(t))return {type:'expression',name:'Smile'};
 if(/\b(come back|come here|walk to me|idhar|yahan|room|stand up)\b/.test(t))return {type:'move',destination:'room'};
 if(/\b(go there|go over there|wahan|udhar|do that)\b/.test(t))return {type:'clarify'};
 return {type:'unknown'};
}

// Corridors are routed around the bed, sofa, tea table, vanity and glass walls.
// Bathroom access is ONLY through its right-hand front door.
export const nodes={
 room:[0,0,.25],front:[0,0,2.12],sofa:[3.90,0,2.18],bed:[2.03,0,-.92],
 bathFront:[-.94,0,-1.25],bathDoor:[-.94,.045,-1.92],bathroom:[-.94,.095,-2.44],bathInside:[-2.38,.095,-2.35],shower:[-2.38,.095,-3.6],toilet:[-1.06,.055,-3.35],toiletFront:[-1.06,.095,-2.82],
 leftAisle:[-4.45,0,-.8],wardrobe:[-4.45,0,-2.72],washbasin:[-3.35,0,-1.45],
 rightAisle:[3.96,0,-.72],balconyFront:[5.20,0,-1.43],balconyDoor:[6.13,0,-1.43],balcony:[7.08,0,-1.94]
};
export const edges=[['room','front'],['front','sofa'],['room','bed'],['room','bathFront'],['bathFront','bathDoor'],['bathDoor','bathroom'],['bathroom','bathInside'],['bathroom','toiletFront'],['toiletFront','toilet'],['bathInside','shower'],['room','leftAisle'],['leftAisle','wardrobe'],['leftAisle','washbasin'],['bed','rightAisle'],['rightAisle','balconyFront'],['balconyFront','balconyDoor'],['balconyDoor','balcony']];
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
function shortest(start,end){
 const costs={[start]:0},prev={},pending=new Set(Object.keys(nodes));
 while(pending.size){const u=[...pending].sort((a,b)=>(costs[a]??Infinity)-(costs[b]??Infinity))[0];pending.delete(u);if(u===end)break;
  for(const [a,b] of edges){const v=a===u?b:b===u?a:null;if(!v||!pending.has(v))continue;const c=costs[u]+distance(nodes[u],nodes[v]);if(c<(costs[v]??Infinity)){costs[v]=c;prev[v]=u;}}
 }
 const route=[end];while(route[0]!==start){if(!prev[route[0]])throw Error('No room route');route.unshift(prev[route[0]]);}return {cost:costs[end],route};
}
export function buildRoute(position,destination){
 if(!nodes[destination])throw Error('Unknown destination');
 // Attach to the nearest corridor, not a straight shortcut across furniture.
 let best=null;
 for(const [a,b] of edges){const p=nodes[a],q=nodes[b],dx=q[0]-p[0],dz=q[2]-p[2],den=dx*dx+dz*dz;
  const t=Math.max(0,Math.min(1,((position[0]-p[0])*dx+(position[2]-p[2])*dz)/den));
  const projection=p.map((v,i)=>v+(q[i]-v)*t),offset=distance(position,projection);
  for(const name of [a,b]){const path=shortest(name,destination),cost=offset+distance(projection,nodes[name])+path.cost;
   if(!best||cost<best.cost)best={cost,points:[projection,...path.route.map(n=>nodes[n])]};}
 }
 return best.points.filter((p,i,arr)=>distance(p,i?arr[i-1]:position)>.012).map(p=>[...p]);
}
