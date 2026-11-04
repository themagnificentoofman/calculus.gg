#!/usr/bin/env node
// Immutable, reviewed delta with flattened composition and explicit withdrawal policy.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,statSync } from 'node:fs';
import { resolve,dirname,join } from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { openDatabase,insertProblem,canonical } from './admin.mjs';
import { openCompact,syncCompact } from './compact.mjs';
import { decodeCompact } from '../../lib/bank/compact-codec.mjs';
import {topics,difficulties} from '../../lib/server/questions-policy.mjs';
import {applyReleasePolicy,flattenSources} from './quality/release-policy.mjs';
import {verifyLegacyEligibility} from './quality/verify-legacy-eligibility.mjs';
import {verifySelectionVocabulary} from './quality/verify-selection-vocabulary.mjs';
const root=resolve(dirname(new URL(import.meta.url).pathname),'../..');
const sha=v=>createHash('sha256').update(v).digest('hex');
const quote=v=>v===null?'NULL':v instanceof Uint8Array?"X'"+Buffer.from(v).toString('hex')+"'":typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
export function servingManifest(manifest){
 // Detailed finite dispositions live in the immutable exported policy rows and
 // full audit artifact. Repeating them in one SQL literal exceeds D1's statement
 // bound. Bind the complete manifest without weakening any policy verification.
 return {schemaVersion:manifest.schemaVersion,format:'content-release-manifest-reference-v1',
  releaseId:manifest.releaseId,parentRelease:manifest.parentRelease,approvedCount:manifest.approvedCount,
  artifactSha256:manifest.artifactSha256,coverage:manifest.coverage,
  fullManifestSha256:sha(canonical(manifest)),
  policy:Object.fromEntries(['exclusions','withdrawals','lineage','familyLineage'].map(key=>[key,{count:(manifest[key]||[]).length,sha256:sha(canonical(manifest[key]||[]))}]))};
}
export async function prepareDelta(manifestPath,baselinePath,directory){
 verifyLegacyEligibility();
 verifySelectionVocabulary();
 if(existsSync(directory))throw Error('Use a fresh output directory');
 const manifest=JSON.parse(readFileSync(manifestPath,'utf8')),artifact=resolve(dirname(manifestPath),manifest.artifact),text=readFileSync(artifact,'utf8');
 if(manifest.schemaVersion!==2||sha(text)!==manifest.artifactSha256||manifest.approvedCount<1)throw Error('Invalid delta manifest');
 const verified=spawnSync(resolve(root,'.bank-venv/bin/python'),[resolve(root,'scripts/bank/pipeline.py'),'--verify',artifact],{encoding:'utf8',maxBuffer:1024*1024});
 if(verified.status!==0)throw Error('Mathematical verification failed: '+verified.stderr);
 mkdirSync(directory,{recursive:true});
 writeFileSync(join(directory,'release-manifest.json'),canonical(manifest)+'\n');
 const source=openDatabase(join(directory,'delta-authoring.sqlite'));
 const records=text.trim().split('\n').map(JSON.parse);
 const baseline=new DatabaseSync(baselinePath,{readOnly:true});
 try{for(const p of records)if(p.problemRevision>1){
  const prior=baseline.prepare('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) WHERE problem_id=? AND revision<? ORDER BY revision').all(p.problemId,p.problemRevision);
  if(prior.length!==p.problemRevision-1)throw Error('Missing immutable prior revisions');
  for(const row of prior)insertProblem(source,await decodeCompact(row));
 }}finally{baseline.close();}
 const counts={},families={},slots=new Map();
 try{
 source.exec('BEGIN IMMEDIATE');
 source.prepare("INSERT INTO bank_releases VALUES (?,?,?,'staging')").run(manifest.releaseId,canonical(servingManifest(manifest)),manifest.approvedCount);
 for(const p of records){if(p.schemaVersion!==2)throw Error('Only reviewed schema-2 additions in this release');insertProblem(source,p);
  const cell=p.topic+'/'+p.difficulty;counts[cell]=(counts[cell]||0)+1;families[p.familyId]=(families[p.familyId]||0)+1;
  for(const tag of ['*',...new Set(p.techniqueTags)]){const key=canonical([p.topic,p.difficulty,tag,p.familyId]),slot=slots.get(key)||0;
   source.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run(manifest.releaseId,p.topic,p.difficulty,tag,p.familyId,slot,p.problemId,p.problemRevision);slots.set(key,slot+1);}
 }
 if(canonical(counts)!==canonical(manifest.coverage)||canonical(families)!==canonical(manifest.families)||Object.values(counts).reduce((a,b)=>a+b,0)!==manifest.approvedCount)throw Error('Coverage mismatch');
 for(const [key,n]of slots)source.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?)').run(manifest.releaseId,...JSON.parse(key),n);
 source.prepare("UPDATE bank_releases SET state='published' WHERE release_id=?").run(manifest.releaseId);source.exec('COMMIT');
 }catch(e){source.exec('ROLLBACK');source.close();throw e;}
 const serving=join(directory,'serving.sqlite');copyFileSync(baselinePath,serving);const db=openCompact(serving);
 try{
 const parent=db.prepare("SELECT release_id,manifest_json,expected_count,state FROM cbank_releases WHERE release_id=?").get(manifest.parentRelease);
 if(!parent||parent.state!=='published'||db.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get()?.value!==manifest.parentRelease)throw Error('Baseline parent differs');
 const parentSources=flattenSources(db,manifest.parentRelease);
 const before={problemRef:db.prepare('SELECT max(problem_ref) n FROM cbank_problems').get().n,sharedId:db.prepare('SELECT max(shared_id) n FROM cbank_shared').get().n,poolId:db.prepare('SELECT max(pool_id) n FROM cbank_pools').get().n,parentManifestSha256:sha(parent.manifest_json),parentCount:parent.expected_count};
 const compression=syncCompact(source,db,manifest.releaseId);
 const policy=applyReleasePolicy(db,manifest,records);
 const tables=[['cbank_shared','shared_id>?',[before.sharedId],['shared_id']],['cbank_problems','problem_ref>?',[before.problemRef],['problem_ref']],['cbank_publication','problem_ref>?',[before.problemRef],['problem_ref']],['cbank_selection_features','problem_ref>?',[before.problemRef],['problem_ref']],['cbank_releases','release_id=?',[manifest.releaseId],['release_id']],['cbank_pools','release_id=?',[manifest.releaseId],['pool_id']],['cbank_slots','pool_id>?',[before.poolId],['pool_id','slot']],['cbank_release_sources','release_id=?',[manifest.releaseId],['release_id','source_release_id']],['cbank_release_exclusions','release_id=?',[manifest.releaseId],['release_id','problem_ref']],['cbank_withdrawn_families','introduced_by=?',[manifest.releaseId],['source_release_id','family_id','introduced_by']],['cbank_problem_lineage','problem_id IN (SELECT value FROM json_each(?))',[JSON.stringify((manifest.lineage||[]).map(x=>x.problemId))],['problem_id']],['cbank_family_lineage','family_id IN (SELECT value FROM json_each(?))',[JSON.stringify((manifest.familyLineage||[]).map(x=>x.familyId))],['family_id']]];
 const batches=[];let stmts=[],bytes=0,writes=0,rows=0;const flush=()=>{if(!stmts.length)return;const file='batch-'+String(batches.length).padStart(5,'0')+'.json',text=JSON.stringify(stmts);writeFileSync(join(directory,file),text);batches.push({file,sha256:sha(text),bytes:Buffer.byteLength(text),statements:stmts.length,rows,estimatedWrites:writes+10,estimatedReads:rows*10+100});stmts=[];bytes=0;writes=0;rows=0;};
 const tableHashes=[];
 for(const [table,where,args,pk] of tables){const records=db.prepare(`SELECT * FROM ${table} WHERE ${where} ORDER BY ${pk.join(',')}`).all(...args),indexCount=db.prepare(`PRAGMA index_list(${table})`).all().length;
  const encode=r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v instanceof Uint8Array?Buffer.from(v).toString('hex'):v]));
  tableHashes.push({table,where,args,order:pk.join(','),count:records.length,sha256:sha(canonical(records.map(encode)))});
  for(const row of records){const cols=Object.keys(row),immutable=cols.filter(k=>!pk.includes(k)&&!(table==='cbank_releases'&&k==='state'));
   const conflict=immutable.length?`DO UPDATE SET ${pk[0]}=excluded.${pk[0]} WHERE ${immutable.map(k=>`${k} IS NOT excluded.${k}`).join(' OR ')}`:'DO NOTHING';
   const sql=`INSERT INTO ${table}(${cols.join(',')}) VALUES(${cols.map(k=>quote(row[k])).join(',')}) ON CONFLICT(${pk.join(',')}) ${conflict}`;
   if(Buffer.byteLength(sql)>90000)throw Error('Statement too large');if(stmts.length>=80||bytes+Buffer.byteLength(sql)>200000)flush();stmts.push(sql);bytes+=Buffer.byteLength(sql);rows++;writes+=1+indexCount;
  }
 }flush();
 const pages=[];let cursor=before.problemRef;
 while(true){const page=db.prepare('SELECT b.*,s.metadata_json,u.state FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE problem_ref>? ORDER BY problem_ref LIMIT 40').all(cursor);if(!page.length)break;
  const tuples=[];for(const row of page){const p=await decodeCompact(row);tuples.push([p.problemId,p.problemRevision,p.contentHash,row.state]);}
  pages.push({cursor,count:page.length,sha256:sha(canonical(tuples))});cursor=page.at(-1).problem_ref;
 }
 const cells=[...topics,'all'].flatMap(category=>difficulties.map(difficulty=>{const input={category,difficulty,count:20};return {input,sha256:sha(canonical(input))};}));
 if(parentSources.length>1&&manifest.priorOperation?.kind!=='delta')throw Error('Composed release requires settled cumulative delta ledger');
 const planBody={format:'content-delta-v2',projectId:'appgprj_6ad91db3d4788191b3e73074e27447f5',priorBundleId:'ed08a3de9381d715d50f5a122a3eb23034d2b92dff2192be4aac198272e56f32',priorOperation:manifest.priorOperation||null,operationAllowance:manifest.operationAllowance||null,release:manifest.releaseId,parentRelease:manifest.parentRelease,parentSources,policy,newCount:manifest.approvedCount,before,batches,pages,tableHashes,cells,coverage:counts,families};
 const plan={...planBody,bundleId:sha(canonical(planBody)),status:'prepared, not imported or activated',localDatabaseBytes:statSync(serving).size,compression};
 writeFileSync(join(directory,'plan.json'),JSON.stringify(plan,null,2)+'\n');
 // Local-only activation for offline sampling; exported release remains staging.
 db.prepare("UPDATE cbank_releases SET state='published' WHERE release_id=?").run(manifest.releaseId);db.prepare("UPDATE cbank_config SET value=? WHERE key='active_release'").run(manifest.releaseId);
 return {bundleId:plan.bundleId,batches:batches.length,newCount:manifest.approvedCount,estimatedWrites:batches.reduce((n,b)=>n+b.estimatedWrites,0),estimatedReads:batches.reduce((n,b)=>n+b.estimatedReads,0),databaseBytes:plan.localDatabaseBytes};
 }finally{source.close();db.close();}
}
if(process.argv[1]&&resolve(process.argv[1])===new URL(import.meta.url).pathname){const [manifest,baseline,out]=process.argv.slice(2);prepareDelta(resolve(manifest),resolve(baseline),resolve(out)).then(console.log).catch(e=>{console.error(e);process.exitCode=1;});}
