import {HttpError,verifyGoogle,seal,open,sha256,jsonBody,bytes} from './security.js';
import {PROVIDERS,DEFAULTS,safeSettings,settings,providerKey,chat,fallback,modelList,speech,transcribe,upstream} from './providers.js';
const enc=new TextEncoder();
export function pcmWav(pcm){const wav=new Uint8Array(44+pcm.length),v=new DataView(wav.buffer);const text=(at,s)=>wav.set(enc.encode(s),at);text(0,'RIFF');v.setUint32(4,36+pcm.length,true);text(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);text(36,'data');v.setUint32(40,pcm.length,true);wav.set(pcm,44);return wav;}
function response(value,status=200,extra={}){return new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...extra}});}
async function rate(env,id,max,seconds=86400){
 const now=Math.floor(Date.now()/1000),window=Math.floor(now/seconds),key=id+':'+window;
 const row=await env.DB.prepare('INSERT INTO counters(id,count,expires_at) VALUES(?,1,?) ON CONFLICT(id) DO UPDATE SET count=count+1 RETURNING count').bind(key,now+seconds*2).first();
 if(row.count>max)throw new HttpError(429,'Lisa usage limit reached. Try again later or adjust the owner limit.');
}
async function paired(req,env,path){
 if(path==='/api/device/start'&&req.method==='POST'){
  const ip=await sha256(req.headers.get('CF-Connecting-IP')||'local');await rate(env,'pair:'+ip,10,600);
  const body=await jsonBody(req);if(!/^[a-f0-9]{64}$/.test(body.challenge||''))throw new HttpError(400,'Invalid device challenge.');
  const id=crypto.randomUUID(),code=String(crypto.getRandomValues(new Uint32Array(1))[0]%1000000).padStart(6,'0'),expires=Math.floor(Date.now()/1000)+300;
  await env.DB.prepare('DELETE FROM devices WHERE expires_at<?').bind(Math.floor(Date.now()/1000)).run();
  await env.DB.prepare('INSERT INTO devices(id,challenge,user_code,expires_at) VALUES(?,?,?,?)').bind(id,body.challenge,code,expires).run();
  return response({device_id:id,user_code:code,expires_at:expires,login_url:new URL('/?device='+id,req.url).toString()});
 }
 if(path==='/api/device/poll'&&req.method==='POST'){
  const body=await jsonBody(req);if(typeof body.verifier!=='string'||body.verifier.length<32||body.verifier.length>128)throw new HttpError(400,'Invalid device verifier.');
  const d=await env.DB.prepare('SELECT * FROM devices WHERE id=?').bind(String(body.device_id||'')).first();
  if(!d||d.expires_at<Math.floor(Date.now()/1000))throw new HttpError(410,'Pairing expired. Start sign-in again.');
  if(await sha256(body.verifier)!==d.challenge)throw new HttpError(403,'This device cannot receive that login.');
  if(!d.envelope)return response({pending:true},202);
  const credential=JSON.parse(await open(d.envelope,env.VAULT_KEY,'device:'+d.id));
  // Single-use handoff is atomic, including concurrent polling attempts.
  const result=await env.DB.prepare('DELETE FROM devices WHERE id=? AND envelope=? RETURNING id').bind(d.id,d.envelope).first();
  if(!result)throw new HttpError(410,'Pairing has already been completed.');
  return response(credential);
 }
 return null;
}
export default {async fetch(req,env){
 try{
  const url=new URL(req.url),path=url.pathname;
  if(req.headers.get('Origin')&&req.headers.get('Origin')!==url.origin)throw new HttpError(403,'Use the Lisa control center directly.');
  if(path==='/health')return response({application:'LISA',version:'2.1.0',configured:!!(env.FIREBASE_PROJECT_ID&&env.FIREBASE_API_KEY&&env.VAULT_KEY&&env.DB&&env.OWNER_EMAIL)});
  if(path==='/api/login-config')return response({projectId:env.FIREBASE_PROJECT_ID,apiKey:env.FIREBASE_API_KEY,authDomain:env.FIREBASE_PROJECT_ID+'.firebaseapp.com'});
  if(!path.startsWith('/api/')){
   const r=await env.ASSETS.fetch(req),headers=new Headers(r.headers);
   headers.set('X-Frame-Options','DENY');headers.set('Referrer-Policy','no-referrer');headers.set('X-Content-Type-Options','nosniff');headers.set('Cross-Origin-Opener-Policy','same-origin-allow-popups');
   headers.set('Content-Security-Policy',"default-src 'self'; script-src 'self' https://apis.google.com; connect-src 'self' https://*.googleapis.com https://*.firebaseapp.com; frame-src https://*.firebaseapp.com https://accounts.google.com; img-src 'self' data: https://*.googleusercontent.com; style-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'");
   return new Response(r.body,{status:r.status,headers});
  }
  if(!env.DB||!env.VAULT_KEY)throw new HttpError(503,'Lisa backend setup is incomplete.');
  const pair=await paired(req,env,path);if(pair)return pair;
  const user=await verifyGoogle(req,env);const cfg=await settings(env);
  if(path==='/api/config'&&req.method==='GET'){
   const rows=(await env.DB.prepare('SELECT provider,updated_at FROM vault').all()).results;
   return response({owner:{email:user.email},settings:cfg,providers:PROVIDERS.map(p=>({id:p,configured:rows.some(v=>v.provider===p)}))});
  }
  if(path==='/api/admin/settings'&&req.method==='POST'){
   const changes=safeSettings(await jsonBody(req));await env.DB.prepare("INSERT INTO settings(id,value) VALUES('main',?) ON CONFLICT(id) DO UPDATE SET value=excluded.value").bind(JSON.stringify({...cfg,...changes})).run();
   return response({ok:true,settings:{...cfg,...changes}});
  }
  const match=path.match(/^\/api\/admin\/providers\/([a-z]+)(?:\/(models|test))?$/);
  if(match){
   const [,p,operation]=match;if(!PROVIDERS.includes(p))throw new HttpError(400,'Unsupported provider.');
   if(!operation&&req.method==='PUT'){
    const body=await jsonBody(req);
    if(typeof body.key!=='string'||body.key.length<10||body.key.length>1000||/\s/.test(body.key))throw new HttpError(400,'Paste the complete provider key without spaces.');
    const envelope=await seal(body.key,env.VAULT_KEY,'provider:'+p);
    await env.DB.prepare('INSERT INTO vault(provider,envelope,updated_at) VALUES(?,?,?) ON CONFLICT(provider) DO UPDATE SET envelope=excluded.envelope,updated_at=excluded.updated_at').bind(p,envelope,Math.floor(Date.now()/1000)).run();
    return response({ok:true,provider:p,configured:true});
   }
   if(!operation&&req.method==='DELETE'){await env.DB.prepare('DELETE FROM vault WHERE provider=?').bind(p).run();return response({ok:true});}
   if(operation==='models'&&req.method==='GET')return response({models:await modelList(env,p)});
   if(operation==='test'&&req.method==='POST'){
    await rate(env,'test:'+user.uid,20,3600);
    if(['groq','gemini','openrouter','meta'].includes(p))return response({ok:true,reply:(await chat(env,cfg,p,{message:'Say hello in one short sentence.',history:[],memories:[]})).reply});
    if(p==='elevenlabs')return response({ok:true,voices:await modelList(env,p)});
    return response({ok:!!(await providerKey(env,p)),note:'Key saved. Run an explicit voice or animation request to verify feature access.'});
   }
  }
  if(path==='/api/device/approve'&&req.method==='POST'){
   const body=await jsonBody(req),d=await env.DB.prepare('SELECT * FROM devices WHERE id=?').bind(String(body.device_id||'')).first();
   if(!d||d.expires_at<Math.floor(Date.now()/1000)||d.user_code!==body.user_code)throw new HttpError(400,'Device code is incorrect or expired.');
   if(typeof body.refresh_token!=='string'||body.refresh_token.length<20||body.refresh_token.length>4096)throw new HttpError(400,'A valid Google session is required.');
   const result=await fetch('https://securetoken.googleapis.com/v1/token?key='+encodeURIComponent(env.FIREBASE_API_KEY),{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'refresh_token',refresh_token:body.refresh_token}),signal:AbortSignal.timeout(12000)});
   if(!result.ok)throw new HttpError(401,'Google session could not be linked. Sign in again.');
   const token=await result.json();if(token.user_id!==user.uid)throw new HttpError(403,'The device session belongs to a different account.');
   const envelope=await seal(JSON.stringify({id_token:token.id_token,refresh_token:token.refresh_token,expires_in:token.expires_in,api_key:env.FIREBASE_API_KEY,project_id:env.FIREBASE_PROJECT_ID}),env.VAULT_KEY,'device:'+d.id);
   await env.DB.prepare('UPDATE devices SET envelope=? WHERE id=? AND envelope IS NULL').bind(envelope,d.id).run();
   return response({ok:true});
  }
  if(path==='/api/chat'&&req.method==='POST'){
   const body=await jsonBody(req);if(typeof body.message!=='string'||!body.message.trim()||body.message.length>4000||!Array.isArray(body.history||[])||!Array.isArray(body.memories||[]))throw new HttpError(400,'Invalid message.');
   await rate(env,'chat:'+user.uid,cfg.daily_limit);
   const ordered=[cfg.chat_provider,...(cfg.chat_fallback?['groq','gemini','openrouter','meta'].filter(p=>p!==cfg.chat_provider):[])],available=[];
   for(const p of ordered)if(await providerKey(env,p))available.push(p);
   const result=await fallback(available,p=>chat(env,cfg,p,body));return response({...result.value,provider:result.provider,failures:result.failures});
  }
  if(path==='/api/tts'&&req.method==='POST'){
   const body=await jsonBody(req);if(typeof body.text!=='string'||body.text.length>3000)throw new HttpError(400,'Invalid voice text.');
   await rate(env,'voice:'+user.uid,cfg.daily_limit);
   const ordered=[cfg.voice_provider,...(cfg.voice_fallback?['elevenlabs','fish'].filter(p=>p!==cfg.voice_provider):[])].filter(p=>p!=='windows');
   const result=await fallback(ordered,p=>speech(env,cfg,p,body)),r=result.value;
   const sound=new Uint8Array(await r.arrayBuffer());if(sound.length>12000000)throw new HttpError(502,'Voice response is too large.');
   const wav=result.provider==='elevenlabs'?pcmWav(sound):sound;return new Response(wav,{headers:{'Content-Type':'audio/wav','Cache-Control':'no-store','X-Lisa-Voice':result.provider}});
  }
  if(path==='/api/transcribe'&&req.method==='POST'){
   const wav=await bytes(req,4194304);if(wav.length<44||new TextDecoder().decode(wav.slice(0,4))!=='RIFF')throw new HttpError(400,'Send WAV microphone audio.');
   await rate(env,'stt:'+user.uid,cfg.daily_limit*2);
   const ordered=[cfg.stt_provider,...(cfg.stt_fallback?['groq','gemini','elevenlabs'].filter(p=>p!==cfg.stt_provider):[])];
   const result=await fallback(ordered,p=>transcribe(env,cfg,p,wav));return response({text:result.value,provider:result.provider});
  }
  throw new HttpError(404,'Route not found.');
 }catch(e){return response({error:e instanceof HttpError?e.message:'Lisa service could not finish that request.'},e instanceof HttpError?e.status:500);}
}};
