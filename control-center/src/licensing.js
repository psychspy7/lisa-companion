import {response} from './response.js';
// Public customer activation is independent of private Google owner administration.
import {SignJWT,importJWK} from 'jose';
import {HttpError,jsonBody,sha256} from './security.js';
const enc=new TextEncoder();
const ISSUER='lisa-kittycorp',AUDIENCE='lisa-desktop',KID='lisa-license-2026-22';
const ERROR='This code cannot activate Lisa on this device. Check the code or contact Kitty Corp.';
const hex=/^[a-f0-9]{64}$/,base64=/^[A-Za-z0-9_-]{43}$/;
function b64(bytes){return btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');}
function unb64(text){return Uint8Array.from(atob(text.replaceAll('-','+').replaceAll('_','/')+'='.repeat((-text.length%4+4)%4)),c=>c.charCodeAt(0));}
function publicJwk(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||input.kty!=='EC'||input.crv!=='P-256'||!base64.test(input.x||'')||!base64.test(input.y||'')||'d' in input)throw new HttpError(400,ERROR);
 return {kty:'EC',crv:'P-256',x:input.x,y:input.y};
}
export async function deviceId(input){const k=publicJwk(input);return sha256(JSON.stringify({crv:k.crv,kty:k.kty,x:k.x,y:k.y}));}
export function proofMessage(id,nonce,device,hash){return ['LISA-ACTIVATE-V1',id,nonce,device,hash].join('\n');}
async function signing(env){
 if(typeof env.LICENSE_SIGNING_KEY!=='string'||env.LICENSE_SIGNING_KEY.length>2048)throw new HttpError(503,'Lisa activation is temporarily unavailable.');
 try{
  const k=JSON.parse(env.LICENSE_SIGNING_KEY);
  if(k.kty!=='EC'||k.crv!=='P-256'||!base64.test(k.x||'')||!base64.test(k.y||'')||!base64.test(k.d||'')||(k.kid&&k.kid!==KID))throw Error('Invalid signing configuration');
  const privateKey=await importJWK(k,'ES256');
  return {privateKey,publicKey:{kty:'EC',crv:'P-256',x:k.x,y:k.y,kid:KID,alg:'ES256',use:'sig'}};
 }catch{throw new HttpError(503,'Lisa activation is temporarily unavailable.');}
}
async function rate(req,env,scope,max,seconds=3600){
 const now=Math.floor(Date.now()/1000),ip=await sha256('lisa-license:'+String(req.headers.get('CF-Connecting-IP')||'unavailable').slice(0,128));
 const key=scope+':'+ip+':'+Math.floor(now/seconds);
 const row=await env.DB.prepare('INSERT INTO activation_limits(id,count,expires_at) VALUES(?,1,?) ON CONFLICT(id) DO UPDATE SET count=count+1 RETURNING count').bind(key,now+seconds*2).first();
 if(!row||row.count>max)throw new HttpError(429,'Too many activation attempts. Please wait before trying again.');
}
async function body(req){
 const value=await jsonBody(req,8192);
 if(!value||typeof value!=='object'||Array.isArray(value))throw new HttpError(400,ERROR);
 return value;
}
async function cleanup(env,now){
 await env.DB.prepare('DELETE FROM activation_challenges WHERE id IN (SELECT id FROM activation_challenges WHERE expires_at<? LIMIT 256)').bind(now).run();
 await env.DB.prepare('DELETE FROM activation_limits WHERE id IN (SELECT id FROM activation_limits WHERE expires_at<? LIMIT 256)').bind(now).run();
}
async function receipt(signer,row,device,machine,now){
 return new SignJWT({v:1,product:AUDIENCE,device,machine,lifetime:true}).setProtectedHeader({alg:'ES256',typ:'JWT',kid:KID})
  .setIssuer(ISSUER).setAudience(AUDIENCE).setSubject(row.id).setIssuedAt(now).sign(signer.privateKey);
}
async function proof(row,signature){
 try{
  if(typeof signature!=='string'||!/^[A-Za-z0-9_-]{86}$/.test(signature))return false;
  const key=await crypto.subtle.importKey('jwk',JSON.parse(row.public_jwk),{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
  return await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,unb64(signature),enc.encode(proofMessage(row.id,row.nonce,row.device_id,row.code_hash)));
 }catch{return false;}
}
/** Return null for unrelated routes. Root must set ownerAuthorized ONLY after verifyGoogle. */
export async function handleLicense(req,env,path,{ownerAuthorized=false}={}){
 if(!path.startsWith('/api/license/')&&path!=='/api/admin/licenses')return null;
 try{
  const origin=req.headers.get('Origin');
  if(origin&&origin!==new URL(req.url).origin)throw new HttpError(403,'Use the Lisa service directly.');
  if(!env.DB)throw new HttpError(503,'Lisa activation is temporarily unavailable.');
  const now=Math.floor(Date.now()/1000);
  if(path==='/api/license/config'&&req.method==='GET'){
   const signer=await signing(env);
   return response({issuer:ISSUER,audience:AUDIENCE,purchase_url:'https://kittycorp.vercel.app/',keys:[signer.publicKey]});
  }
  if(path==='/api/admin/licenses'){
   if(!ownerAuthorized)throw new HttpError(403,'Owner authentication is required.');
   if(req.method==='GET'){
    const rows=await env.DB.prepare('SELECT id,created_at,claimed_at,disabled FROM activation_codes ORDER BY created_at DESC LIMIT 500').bind().all();
    return response({licenses:rows.results||[]});
   }
   if(req.method==='POST'){
    const b=await body(req);
    if(typeof b.id!=='string'||b.id.length>100||typeof b.disabled!=='boolean')throw new HttpError(400,'Invalid license administration request.');
    const row=await env.DB.prepare('UPDATE activation_codes SET disabled=? WHERE id=? RETURNING id').bind(b.disabled?1:0,b.id).first();
    if(!row)throw new HttpError(404,'License was not found.');
    return response({ok:true,note:'This affects future online activation/recovery. A lifetime offline receipt remains usable while offline.'});
   }
   throw new HttpError(405,'Method not allowed.');
  }
  if(req.method!=='POST')throw new HttpError(405,'Method not allowed.');
  if(path==='/api/license/challenge'){
   await rate(req,env,'challenge',20);
   const b=await body(req),jwk=publicJwk(b.public_jwk);
   if(!['redeem','recover'].includes(b.operation)||!hex.test(b.machine||'')||(b.operation==='redeem'&&!hex.test(b.code_hash||'')))throw new HttpError(400,ERROR);
   // Validate the EC point, not merely its JSON shape.
   try{await crypto.subtle.importKey('jwk',jwk,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);}catch{throw new HttpError(400,ERROR);}
   const id=crypto.randomUUID(),nonce=b64(crypto.getRandomValues(new Uint8Array(32))),device=await deviceId(jwk),expiry=now+300;
   await cleanup(env,now);
   await env.DB.prepare('INSERT INTO activation_challenges(id,nonce,device_id,public_jwk,machine_binding,operation,code_hash,expires_at) VALUES(?,?,?,?,?,?,?,?)')
    .bind(id,nonce,device,JSON.stringify(jwk),b.machine,b.operation,b.operation==='redeem'?b.code_hash:'',expiry).run();
   return response({challenge_id:id,nonce,expires_at:expiry});
  }
  if(path==='/api/license/redeem'||path==='/api/license/recover'){
   await rate(req,env,'submit',60);
   const b=await body(req),operation=path.endsWith('recover')?'recover':'redeem';
   if(typeof b.challenge_id!=='string'||!/^[A-Za-z0-9-]{1,80}$/.test(b.challenge_id))throw new HttpError(400,ERROR);
   const row=await env.DB.prepare('SELECT * FROM activation_challenges WHERE id=?').bind(b.challenge_id).first();
   if(!row||row.operation!==operation||row.expires_at<=now||!await proof(row,b.proof))throw new HttpError(400,ERROR);
   // Validate signing readiness before consuming the challenge or code.
   const signer=await signing(env);
   const consumed=await env.DB.prepare('DELETE FROM activation_challenges WHERE id=? AND nonce=? AND operation=? AND expires_at>? RETURNING id')
    .bind(row.id,row.nonce,operation,now).first();
   if(!consumed)throw new HttpError(400,ERROR);
   let license;
   if(operation==='redeem'){
    try{
     license=await env.DB.prepare('UPDATE activation_codes SET device_id=?,machine_binding=?,claimed_at=COALESCE(claimed_at,?) WHERE code_hash=? AND disabled=0 AND (device_id IS NULL OR (device_id=? AND machine_binding=?)) RETURNING id')
      .bind(row.device_id,row.machine_binding,now,row.code_hash,row.device_id,row.machine_binding).first();
    }catch{throw new HttpError(400,ERROR);}
   }else{
    license=await env.DB.prepare('SELECT id FROM activation_codes WHERE device_id=? AND machine_binding=? AND disabled=0')
     .bind(row.device_id,row.machine_binding).first();
   }
   if(!license)throw new HttpError(400,ERROR);
   return response({token:await receipt(signer,license,row.device_id,row.machine_binding,now),offline_allowed:true});
  }
  throw new HttpError(404,'Route not found.');
 }catch(e){
  // No code, signing material, device proof or identifying body is logged.
  return response({error:e instanceof HttpError?e.message:'Lisa activation is temporarily unavailable.'},e instanceof HttpError?e.status:503);
 }
}
