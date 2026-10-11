import {createRemoteJWKSet,jwtVerify} from 'jose';
const encoder=new TextEncoder(),decoder=new TextDecoder();
const jwks=createRemoteJWKSet(new URL('https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com'));
export class HttpError extends Error{constructor(status,message){super(message);this.status=status;}}
export const b64=bytes=>btoa(String.fromCharCode(...bytes));
export const unb64=text=>Uint8Array.from(atob(text),c=>c.charCodeAt(0));
export async function seal(value,secret,aad){
 const key=await crypto.subtle.importKey('raw',unb64(secret),'AES-GCM',false,['encrypt']),nonce=crypto.getRandomValues(new Uint8Array(12));
 const data=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:encoder.encode(aad)},key,encoder.encode(value));
 return JSON.stringify({v:1,nonce:b64(nonce),data:b64(new Uint8Array(data))});
}
export async function open(envelope,secret,aad){
 const e=JSON.parse(envelope);if(e.v!==1)throw Error('Unknown envelope version');
 const key=await crypto.subtle.importKey('raw',unb64(secret),'AES-GCM',false,['decrypt']);
 return decoder.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:unb64(e.nonce),additionalData:encoder.encode(aad)},key,unb64(e.data)));
}
export async function sha256(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(value)))].map(v=>v.toString(16).padStart(2,'0')).join('');}
export async function verifyGoogle(req,env,verifier=jwtVerify){
 const header=req.headers.get('Authorization')||'';if(!header.startsWith('Bearer '))throw new HttpError(401,'Sign in with Google first.');
 if(!env.FIREBASE_PROJECT_ID||!env.FIREBASE_API_KEY||!env.OWNER_EMAIL)throw new HttpError(503,'Google sign-in is not configured.');
 let payload;try{({payload}=await verifier(header.slice(7),jwks,{algorithms:['RS256'],audience:env.FIREBASE_PROJECT_ID,issuer:'https://securetoken.google.com/'+env.FIREBASE_PROJECT_ID}));}catch{throw new HttpError(401,'Your sign-in expired. Sign in again.');}
 if(!payload.sub||!payload.email_verified||payload.firebase?.sign_in_provider!=='google.com'||String(payload.email||'').toLowerCase()!==env.OWNER_EMAIL.toLowerCase())throw new HttpError(403,'This control center is private to its owner.');
 // Firebase lookup rejects revoked/disabled/deleted accounts, not just expired JWTs.
 const check=await fetch('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key='+encodeURIComponent(env.FIREBASE_API_KEY),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idToken:header.slice(7)}),signal:AbortSignal.timeout(12000)});
 if(!check.ok)throw new HttpError(401,'Your Google session is no longer valid.');
 const users=(await check.json()).users;if(!users?.some(u=>u.localId===payload.sub&&!u.disabled&&u.emailVerified&&Number(payload.auth_time||0)>=Number(u.validSince||0)))throw new HttpError(403,'This account cannot access Lisa.');
 await env.DB.prepare('INSERT OR IGNORE INTO owner(id,uid,email) VALUES(1,?,?)').bind(payload.sub,payload.email.toLowerCase()).run();
 const owner=await env.DB.prepare('SELECT uid,email FROM owner WHERE id=1').first();
 if(owner?.uid!==payload.sub||owner?.email!==payload.email.toLowerCase())throw new HttpError(403,'This account is not the pinned Lisa administrator.');
 return {uid:payload.sub,email:payload.email,token:header.slice(7)};
}
export async function bytes(req,max=262144){
 if(Number(req.headers.get('Content-Length')||0)>max)throw new HttpError(413,'Request is too large.');
 const reader=req.body?.getReader();if(!reader)return new Uint8Array();const parts=[];let length=0;
 try{while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>max){await reader.cancel();throw new HttpError(413,'Request is too large.');}parts.push(value);}}finally{reader.releaseLock();}
 const result=new Uint8Array(length);let at=0;for(const p of parts){result.set(p,at);at+=p.length;}return result;
}
export async function jsonBody(req,max){try{return JSON.parse(decoder.decode(await bytes(req,max)));}catch(e){if(e instanceof HttpError)throw e;throw new HttpError(400,'Send a valid JSON request.');}}
