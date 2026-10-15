import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPair,exportJWK} from 'jose';
import worker from '../src/worker.js';
test('real dispatcher exposes public activation without Google and protects owner license controls',async()=>{
 const {privateKey}=await generateKeyPair('ES256',{extractable:true});
 const key=await exportJWK(privateKey);key.kid='lisa-license-2026-22';
 const env={DB:{},VAULT_KEY:'fixture-only',LICENSE_SIGNING_KEY:JSON.stringify(key)};
 const config=await worker.fetch(new Request('https://example.test/api/license/config'),env);
 assert.equal(config.status,200);
 const body=await config.json();assert.equal(body.keys[0].kid,key.kid);assert.equal(body.keys[0].d,undefined);
 for(const method of ['GET','POST']){
  const result=await worker.fetch(new Request('https://example.test/api/admin/licenses',{method}),env);
  assert.equal(result.status,401);
 }
});
