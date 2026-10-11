import test from 'node:test';import assert from 'node:assert/strict';import {generateKeyPair,SignJWT,exportJWK,createLocalJWKSet,jwtVerify} from 'jose';import {verifyGoogle} from '../src/security.js';import {pcmWav} from '../src/worker.js';
test('signed Google identity validates issuer, audience, revocation and pinned owner',async()=>{
 const {privateKey,publicKey}=await generateKeyPair('RS256');const jwk=await exportJWK(publicKey);jwk.kid='test';const local=createLocalJWKSet({keys:[jwk]});
 let pinned=null,validSince=100;
 const env={OWNER_EMAIL:'owner@example.com',FIREBASE_PROJECT_ID:'lisa-test',FIREBASE_API_KEY:'public-test',DB:{prepare(sql){return {bind(...args){return {async run(){if(sql.startsWith('INSERT')&&!pinned)pinned={uid:args[0],email:args[1]};},async first(){return pinned;}};},async first(){return pinned;}};}}};
 const verifier=(token,ignored,opts)=>jwtVerify(token,local,opts);
 const token=async(audience='lisa-test',issuer='https://securetoken.google.com/lisa-test',sub='owner-uid')=>await new SignJWT({email:'owner@example.com',email_verified:true,auth_time:101,firebase:{sign_in_provider:'google.com'}}).setProtectedHeader({alg:'RS256',kid:'test'}).setSubject(sub).setIssuer(issuer).setAudience(audience).setExpirationTime('5m').sign(privateKey);
 const old=global.fetch;global.fetch=async()=>new Response(JSON.stringify({users:[{localId:'owner-uid',emailVerified:true,validSince}]}));
 try{
  const req=async (...args)=>new Request('https://lisa.test',{headers:{Authorization:'Bearer '+await token(...args)}});
  assert.equal((await verifyGoogle(await req(),env,verifier)).uid,'owner-uid');assert.equal(pinned.uid,'owner-uid');
  await assert.rejects(()=>verifyGoogle(new Request('https://lisa.test',{headers:{Authorization:'Bearer forged'}}),env,verifier),e=>e.status===401);
  await assert.rejects(async()=>verifyGoogle(await req('wrong-project'),env,verifier),e=>e.status===401);
  await assert.rejects(async()=>verifyGoogle(await req('lisa-test','https://wrong.test'),env,verifier),e=>e.status===401);
  validSince=200;await assert.rejects(async()=>verifyGoogle(await req(),env,verifier),e=>e.status===403);
 }finally{global.fetch=old;}
});
test('ElevenLabs PCM is normalized to a valid mono 24k WAV container',()=>{const sound=new Uint8Array([1,2,3,4]);const wav=pcmWav(sound),v=new DataView(wav.buffer);assert.equal(new TextDecoder().decode(wav.slice(0,4)),'RIFF');assert.equal(v.getUint32(24,true),24000);assert.equal(v.getUint16(22,true),1);assert.equal(v.getUint16(34,true),16);assert.equal(v.getUint32(40,true),sound.length);assert.deepEqual(wav.slice(44),sound);});
