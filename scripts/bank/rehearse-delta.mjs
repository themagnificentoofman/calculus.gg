#!/usr/bin/env node
// Replay the exact export through the signed operator on local workerd/D1.
// Local D1 counters are measured engine work, not production quota telemetry.
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,copyFileSync,mkdtempSync,readdirSync,rmSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { generateKeyPairSync,sign,createHash } from 'node:crypto';
import { Miniflare } from 'miniflare';
import { build } from 'esbuild';
import { message,steps } from '../../lib/server/content-release.mjs';
const [directory,baselinePath,outputPath]=process.argv.slice(2);
if(!outputPath)throw Error('Usage: rehearse-delta.mjs PLAN_DIRECTORY BASELINE.sqlite REPORT.json');
const dir=resolve(directory),persist=mkdtempSync(join(dir,'rehearsal-workerd-'));
const plan=JSON.parse(readFileSync(join(dir,'plan.json'))),program=steps(plan);
const {publicKey,privateKey}=generateKeyPairSync('ed25519');
const allowance={bundleId:plan.bundleId,reads:1100000,writes:230000,bytes:150000000};
const bundle=await build({stdin:{contents:`import {contentRelease} from './lib/server/content-release.mjs'; const plan=${JSON.stringify(plan)}; export default {fetch(request,env){return contentRelease(request,env.DB,plan,{publicKey:env.KEY,expiresAt:env.EXPIRES,allowance:env.ALLOWANCE});}};`,resolveDir:process.cwd()},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const create=()=>new Miniflare({modules:[{type:'ESModule',path:'index.mjs',contents:bundle.outputFiles[0].text}],modulesRoot:process.cwd(),compatibilityDate:'2026-04-01',d1Databases:{DB:'milestone3-rehearsal'},d1Persist:persist,bindings:{KEY:publicKey.export({type:'spki',format:'der'}).toString('base64'),EXPIRES:String(Date.now()+3600000),ALLOWANCE:JSON.stringify(allowance)}});
let mf=create(),db=await mf.getD1Database('DB');
await db.prepare('SELECT 1').all();await mf.dispose();
const sqliteFiles=readdirSync(persist,{recursive:true}).filter(f=>/(^|\/)[a-f0-9]{64}\.sqlite$/.test(f));assert.equal(sqliteFiles.length,1);
const databaseFile=join(persist,sqliteFiles[0]);
for(const suffix of ['-wal','-shm'])rmSync(databaseFile+suffix,{force:true});
copyFileSync(baselinePath,databaseFile);mf=create();db=await mf.getD1Database('DB');
const get=async(sql,args=[])=> (await db.prepare(sql).bind(...args).all()).results[0];
const originalCount=(await get('SELECT count(*) n FROM cbank_problems')).n;
for(const name of ['0003_operator_ledger','0004_flimsy_carlie_cooper','0005_brief_skaar'])await db.exec(readFileSync('drizzle/'+name+'.sql','utf8').replace(/--[^\n]*/g,'').replaceAll('\n',' '));
const prior=JSON.parse(readFileSync('docs/bank/milestone3/baseline.json')).operatorLedger;
await db.prepare(`INSERT INTO cbank_operator_ledger (${Object.keys(prior).join(',')}) VALUES (${Object.keys(prior).map(()=>'?').join(',')})`).bind(...Object.values(prior)).run();
let calls=0;
const call=async input=>{calls++;const body=JSON.stringify(input),hash=createHash('sha256').update(body).digest('hex'),time=String(Date.now());const response=await mf.dispatchFetch('http://local.invalid/api/content-release',{method:'POST',body,headers:{'x-bank-time':time,'x-bank-body-sha256':hash,'x-bank-signature':sign(null,Buffer.from(message(plan,time,hash)),privateKey).toString('base64')}});const result=await response.json();assert.equal(response.status,200,JSON.stringify(result));assert.equal(result.halted,null);return result;};
const start=performance.now(),selections=[];let retries=0,result;
try{
 await call({op:'init'});
 for(let i=0;i<program.length;i++){
  const step=program[i],input={op:'step',step:i};if(step.kind==='import')input.text=readFileSync(join(dir,step.file),'utf8');
  result=await call(input);assert.equal(result.nextSequence,i+1);if(result.selection)selections.push({...result.selection,measurements:result.measurements});
  if(i%25===0){const repeated=await call(input);assert.equal(repeated.replayed,true);assert.equal(repeated.nextSequence,i+1);retries++;}
  if(i%25===0){assert.equal((await get("SELECT value FROM cbank_config WHERE key='active_release'")).value,plan.parentRelease);console.log(JSON.stringify({step:i+1,total:program.length,kind:step.kind,chargedReads:result.chargedReads,chargedWrites:result.chargedWrites}));}
 }
 assert.equal(result.verified,1);const activation=await call({op:'activate'});assert.equal(activation.activated,1);
 assert.equal((await get("SELECT value FROM cbank_config WHERE key='active_release'")).value,plan.release);
 assert.equal((await get('SELECT count(*) n FROM cbank_problems')).n,originalCount+plan.newCount);
 assert.equal((await call({op:'activate'})).replayed,true);
 const rollback=await call({op:'rollback'});assert.equal(rollback.activated,2);
 assert.equal((await get("SELECT value FROM cbank_config WHERE key='active_release'")).value,plan.parentRelease);
 assert.equal((await get('SELECT count(*) n FROM cbank_problems WHERE problem_ref<=?',[plan.before.problemRef])).n,originalCount);
 assert.equal((await get('SELECT state FROM cbank_releases WHERE release_id=?',[plan.release])).state,'published');
 const report={bundleId:plan.bundleId,runtime:'local workerd and D1',steps:program.length,retriedReceipts:retries,stagedCells:selections,activationPassed:true,rollbackPassed:true,historicalRowsRetained:originalCount,newRowsRetained:plan.newCount,requests:calls,elapsedMs:performance.now()-start,chargedReadsIncludingRehearsalRetries:rollback.chargedReads,chargedWritesIncludingRehearsalRetries:rollback.chargedWrites,measuredReads:rollback.measuredReads,measuredWrites:rollback.measuredWrites,databaseBytes:rollback.databaseBytes,measurementScope:'Local D1 engine counters, not provider remaining quota or production traffic. Includes exact export, decoding, staged selection, idempotent replay, activation and rollback.'};
 writeFileSync(outputPath,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,stagedCells:selections.length}));
}finally{await mf.dispose();}
