import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {handleLicense,deviceId,proofMessage} from '../src/licensing.js';
import {generateKeyPair,exportJWK,jwtVerify} from 'jose';
const enc=new TextEncoder();
class DB {
 constructor(){this.db=new DatabaseSync(':memory:');this.db.exec(readFileSync(new URL('../migrations/0002_activation.sql',import.meta.url),'utf8'));}
 prepare(sql){const db=this.db;return {bind(...v){return {async first(){return db.prepare(sql).get(...v)||null;},async run(){const r=db.prepare(sql).run(...v);return {meta:{changes:r.changes}};},async all(){return {results:db.prepare(sql).all(...v)}}};}};}
}
const hash=async t=>Buffer.from(await crypto.subtle.digest('SHA-256',enc.encode(t))).toString('hex');
async function fixture(){
 const signer=await generateKeyPair('ES256',{extractable:true}),key=await exportJWK(signer.privateKey);
 key.kid='lisa-license-2026-22';const env={DB:new DB(),LICENSE_SIGNING_KEY:JSON.stringify(key)};
 const codeHash=await hash('LISA-ABCDE-FGHIJ-KLMNO-PQRST-UVWXY-Z2345');
 await env.DB.prepare('INSERT INTO activation_codes(id,code_hash,created_at) VALUES(?,?,?)').bind('license-one',codeHash,Math.floor(Date.now()/1000)).run();
 return {env,signer,codeHash};
}
async function device(){const key=await generateKeyPair('ES256',{extractable:true});return {...key,jwk:await exportJWK(key.publicKey)};}
async function request(env,path,body={},options={}){
 const r=await handleLicense(new Request('https://example.invalid'+path,{method:options.method||'POST',headers:{'Content-Type':'application/json','CF-Connecting-IP':options.ip||'192.0.2.1'},body:options.method==='GET'?undefined:JSON.stringify(body)}),env,path,options);
 return {status:r.status,data:await r.json()};
}
async function enroll(env,d,codeHash,operation='redeem'){
 const c=await request(env,'/api/license/challenge',{public_jwk:d.jwk,operation,code_hash:operation==='redeem'?codeHash:undefined,machine:'a'.repeat(64)});
 assert.equal(c.status,200);
 const message=proofMessage(c.data.challenge_id,c.data.nonce,await deviceId(d.jwk),operation==='redeem'?codeHash:'');
 const sig=await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},d.privateKey,enc.encode(message));
 return {challenge_id:c.data.challenge_id,proof:Buffer.from(sig).toString('base64url')};
}
test('atomic redemption has one device winner and same-device recovery preserves license',async()=>{
 const {env,signer,codeHash}=await fixture(),a=await device(),b=await device();
 const ca=await enroll(env,a,codeHash),cb=await enroll(env,b,codeHash);
 const r=await Promise.all([request(env,'/api/license/redeem',ca),request(env,'/api/license/redeem',cb)]);
 assert.deepEqual(r.map(r=>r.status).sort(),[200,400]);
 const winner=r[0].status===200?a:b,receipt=r.find(r=>r.status===200).data.token;
 const {payload}=await jwtVerify(receipt,signer.publicKey,{algorithms:['ES256'],issuer:'lisa-kittycorp',audience:'lisa-desktop'});
 assert.equal(payload.device,await deviceId(winner.jwk));assert.equal(payload.lifetime,true);
 const recovery=await request(env,'/api/license/recover',await enroll(env,winner,codeHash,'recover'));assert.equal(recovery.status,200);
 const {payload:again}=await jwtVerify(recovery.data.token,signer.publicKey,{algorithms:['ES256']});assert.equal(again.sub,payload.sub);
 assert.equal((await request(env,'/api/license/redeem',await enroll(env,winner,codeHash))).status,200);
});
test('proof, challenge replay, expiry and cross-device recovery fail uniformly',async()=>{
 const {env,codeHash}=await fixture(),a=await device(),b=await device(),c=await enroll(env,a,codeHash);
 const wrong=await request(env,'/api/license/redeem',{...c,proof:'x'.repeat(86)});assert.equal(wrong.status,400);
 assert.equal((await request(env,'/api/license/redeem',c)).status,200);
 const replay=await request(env,'/api/license/redeem',c);assert.equal(replay.status,400);
 const recovery=await request(env,'/api/license/recover',await enroll(env,b,codeHash,'recover'));assert.equal(recovery.status,400);
 const expired=await enroll(env,a,codeHash);
 await env.DB.prepare('UPDATE activation_challenges SET expires_at=0 WHERE id=?').bind(expired.challenge_id).run();
 assert.equal((await request(env,'/api/license/redeem',expired)).status,400);
 assert.equal(wrong.data.error,replay.data.error);assert.equal(replay.data.error,recovery.data.error);
});
test('unknown code is not bound; missing signing key cannot consume a valid code',async()=>{
 const {env,codeHash}=await fixture(),d=await device();
 assert.equal((await request(env,'/api/license/redeem',await enroll(env,d,'f'.repeat(64)))).status,400);
 const c=await enroll(env,d,codeHash);delete env.LICENSE_SIGNING_KEY;
 assert.equal((await request(env,'/api/license/redeem',c)).status,503);
 assert.equal((await env.DB.prepare('SELECT device_id FROM activation_codes WHERE id=?').bind('license-one').first()).device_id,null);
});
test('public config hides private key, body/rate bounds and admin guard',async()=>{
 const {env}=await fixture(),d=await device();
 const config=await request(env,'/api/license/config',{}, {method:'GET'});assert.equal(config.status,200);assert.equal(config.data.keys[0].d,undefined);
 assert.equal((await request(env,'/api/admin/licenses',{}, {method:'GET'})).status,403);
 assert.equal((await request(env,'/api/admin/licenses',{}, {method:'GET',ownerAuthorized:true})).status,200);
 assert.equal((await request(env,'/api/license/challenge',{padding:'a'.repeat(9000)})).status,413);
 let last;for(let n=0;n<22;n++)last=await request(env,'/api/license/challenge',{public_jwk:d.jwk,operation:'recover',machine:'a'.repeat(64)},{ip:'192.0.2.5'});
 assert.equal(last.status,429);
});
