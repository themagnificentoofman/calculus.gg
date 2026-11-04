import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync,sign,createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { openCompact } from '../scripts/bank/compact.mjs';
import { contentRelease,message,steps } from '../lib/server/content-release.mjs';
import { canonical } from '../scripts/bank/admin.mjs';
const sha=s=>createHash('sha256').update(s).digest('hex');
function fixture(){
 const sql=openCompact(':memory:');sql.exec(readFileSync(new URL('../drizzle/0003_operator_ledger.sql',import.meta.url),'utf8'));
 sql.exec("INSERT INTO cbank_releases VALUES ('parent','{}',1,'published'); INSERT INTO cbank_config VALUES ('active_release','parent');");
 const columns=sql.prepare('PRAGMA table_info(cbank_operator_ledger)').all();const row=Object.fromEntries(columns.filter(c=>c.notnull||c.pk).map(c=>[c.name,c.type==='TEXT'?'prior':0]));row.activated=1;row.measured_reads=3734034;row.measured_writes=1030735;row.overhead_reads=121168;row.overhead_writes=28792;
 sql.prepare(`INSERT INTO cbank_operator_ledger (${Object.keys(row).join(',')}) VALUES (${Object.keys(row).map(()=>'?').join(',')})`).run(...Object.values(row));
 let calls=0;const prep=(text,values=[])=>({bind:(...v)=>prep(text,v),all:async()=>{calls++;const results=sql.prepare(text).all(...values);return {success:true,results,meta:{rows_read:results.length+1,rows_written:/^(UPDATE|INSERT|DELETE)/.test(text)?1:0,size_after:100000,duration:0}};}});
 const db={prepare:prep,batch:async stmts=>{sql.exec('BEGIN IMMEDIATE');try{const rs=[];for(const s of stmts)rs.push(await s.all());sql.exec('COMMIT');return rs;}catch(e){sql.exec('ROLLBACK');throw e;}}};
 const sample=JSON.parse(readFileSync(new URL('./fixtures/bank/review-samples.json',import.meta.url)))[0];
 const p={...sample,familyId:'qa',topic:'integration',difficulty:'easy'};delete p.contentHash;p.contentHash=sha(canonical(p));const {problemId,problemRevision,contentHash,semanticHash,...body}=p;
 const hex=v=>"X'"+Buffer.from(v).toString('hex')+"'";
 const text=JSON.stringify(["INSERT INTO cbank_releases VALUES ('delta','{}',1,'staging')","INSERT INTO cbank_release_sources VALUES ('delta','parent')",`INSERT INTO cbank_shared VALUES (1,${hex(Buffer.from('b'.repeat(64),'hex'))},'{}')`,`INSERT INTO cbank_problems VALUES (1,'${problemId}',${problemRevision},${hex(Buffer.from(contentHash,'hex'))},${hex(Buffer.from(semanticHash,'hex'))},1,${hex(gzipSync(canonical(body)))})`,"INSERT INTO cbank_publication VALUES (1,'approved',NULL)","INSERT INTO cbank_pools VALUES (1,'delta','integration','easy','*','qa',1)","INSERT INTO cbank_slots VALUES (1,0,1)"]);
 const plan={format:'content-delta-v1',projectId:'qa',bundleId:'a'.repeat(64),priorBundleId:'prior',release:'delta',parentRelease:'parent',newCount:1,before:{problemRef:null,sharedId:null,poolId:null,parentManifestSha256:sha('{}'),parentCount:1},batches:[{sha256:sha(text),bytes:Buffer.byteLength(text),statements:7,estimatedReads:100,estimatedWrites:20}],pages:[],tableHashes:[{table:'cbank_release_sources',where:'release_id=?',args:['delta'],order:'source_release_id',count:1,sha256:sha(canonical([{release_id:'delta',source_release_id:'parent'}]))}]};
 const smokeInput={category:'integration',difficulty:'easy',count:1};plan.cells=[{input:smokeInput,sha256:sha(canonical(smokeInput))}];
 const {publicKey,privateKey}=generateKeyPairSync('ed25519');const config={publicKey:publicKey.export({type:'spki',format:'der'}).toString('base64'),expiresAt:Date.now()+600000,allowance:JSON.stringify({bundleId:plan.bundleId,reads:100000,writes:10000,bytes:120000000})};
 const call=async(input,override={})=>{const body=JSON.stringify(input),hash=sha(body),time=String(Date.now());const request=new Request('https://test/api/content-release',{method:'POST',headers:{'x-bank-time':time,'x-bank-body-sha256':hash,'x-bank-signature':sign(null,Buffer.from(message(plan,time,hash)),privateKey).toString('base64')},body});const response=await contentRelease(request,db,plan,{...config,...override});return {status:response.status,body:await response.json()};};
 return {sql,db,plan,text,config,call,calls:()=>calls};
}
test('delta endpoint requires explicit new allowance and authentication before database access',async()=>{const f=fixture();try{assert.equal((await f.call({op:'init'},{allowance:undefined})).status,404);assert.equal(f.calls(),0);const bad=await contentRelease(new Request('https://test/api/content-release',{method:'POST',body:'{}'}),f.db,f.plan,f.config);assert.equal(bad.status,403);assert.equal(f.calls(),0);assert.equal((await f.call({op:'init'},{allowance:JSON.stringify({bundleId:f.plan.bundleId,reads:2000000,writes:10000,bytes:120000000})})).status,409);assert.equal(f.sql.prepare('SELECT count(*) n FROM cbank_delta_ledger').get().n,0);}finally{f.sql.close();}});
test('delta is staged, sequential, checksum locked, retry safe, verified before atomic activation and reversible',async()=>{const f=fixture();try{
 assert.equal((await f.call({op:'init'})).status,200);
 assert.equal((await f.call({op:'activate'})).status,409);
 assert.equal((await f.call({op:'step',step:1})).status,409);
 assert.equal((await f.call({op:'step',step:0,text:f.text+' '})).status,400);
 const first=await f.call({op:'step',step:0,text:f.text});assert.equal(first.status,200,JSON.stringify(first));assert.equal(first.body.nextSequence,1);
 const retry=await f.call({op:'step',step:0,text:f.text});assert.equal(retry.status,200);assert.equal(retry.body.replayed,true);assert.ok(retry.body.chargedReads>first.body.chargedReads);
 assert.equal(f.sql.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,'parent');
 assert.equal((await f.call({op:'activate'})).status,409);
 assert.equal((await f.call({op:'step',step:1})).status,200);
 assert.equal((await f.call({op:'activate'})).status,409);
 const smoke=await f.call({op:'step',step:2});assert.equal(smoke.status,200,JSON.stringify(smoke));assert.equal(smoke.body.selection.distinctFamilies,1);
 const activation=await f.call({op:'activate'});assert.equal(activation.status,200,JSON.stringify(activation));assert.equal(activation.body.activated,1);
 assert.equal(f.sql.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,'delta');
 assert.equal((await f.call({op:'activate'})).body.replayed,true);
 assert.equal((await f.call({op:'rollback'})).status,200);assert.equal(f.sql.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,'parent');
 assert.equal(f.sql.prepare("SELECT state FROM cbank_releases WHERE release_id='delta'").get().state,'published');
 assert.equal(steps(f.plan).length,3);
}finally{f.sql.close();}});

test('a composed delta carries prior charged usage and cannot reuse the old allowance',async()=>{
 const f=fixture();try{
  const cols=f.sql.prepare('PRAGMA table_info(cbank_delta_ledger)').all();
  const row=Object.fromEntries(cols.filter(c=>c.notnull||c.pk).map(c=>[c.name,c.type==='TEXT'?'settled-delta':0]));
  Object.assign(row,{bundle_id:'settled-delta',verified:1,activated:1,charged_reads:563084,charged_writes:51276,prior_reads:3855202,prior_writes:1059527,database_bytes:96092160});
  f.sql.prepare(`INSERT INTO cbank_delta_ledger (${Object.keys(row).join(',')}) VALUES (${Object.keys(row).map(()=>'?').join(',')})`).run(...Object.values(row));
  f.plan.priorOperation={kind:'delta',bundleId:'settled-delta'};
  const tooMuch=await f.call({op:'init'},{allowance:JSON.stringify({bundleId:f.plan.bundleId,reads:600000,writes:10000,bytes:120000000})});
  assert.equal(tooMuch.status,409);assert.match(tooMuch.body.error,/cumulative/);
  const ok=await f.call({op:'init'});assert.equal(ok.status,200,JSON.stringify(ok));
  assert.equal(ok.body.priorChargedReads,4418286);assert.equal(ok.body.priorChargedWrites,1110803);
 }finally{f.sql.close();}
});
