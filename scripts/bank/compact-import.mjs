#!/usr/bin/env node
// Provider-neutral batch format and executor. CLI supports LOCAL rehearsal only.
// A Sites application writer was proven by the four-batch pilot. Full hosted
// execution still requires an authenticated adapter and a fresh managed allowance.
import { createHash } from 'node:crypto';
import { readFileSync,writeFileSync,mkdirSync,existsSync,appendFileSync,statSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';
import { openCompact,verifyCompact } from './compact.mjs';
import { canonical,decodeCompact } from '../../lib/bank/compact-codec.mjs';
const sha = text=>createHash('sha256').update(text).digest('hex');
const quote = v=>v===null?'NULL':v instanceof Uint8Array?"X'"+Buffer.from(v).toString('hex')+"'":typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const keys={cbank_shared:['shared_id'],cbank_problems:['problem_ref'],cbank_publication:['problem_ref'],cbank_releases:['release_id'],cbank_pools:['pool_id'],cbank_slots:['pool_id','slot'],bank_legacy_ids:['source','legacy_id']};
export function exportCompact(db,directory,{rowsPerBatch=250}={}) {
  if (existsSync(directory)) throw Error('Use a fresh export directory to avoid stale batches');
  mkdirSync(directory,{recursive:true});
  const expected=verifyCompact(db),batches=[]; let statements=[],rows=0,writes=0,bytes=0,maxStatementBytes=0;
  function flush(){
    if (!statements.length) return;
    const file=`batch-${String(batches.length).padStart(5,'0')}.json`,text=JSON.stringify(statements)+'\n';
    writeFileSync(join(directory,file),text); batches.push({file,sha256:sha(text),bytes:Buffer.byteLength(text),rows,statements:statements.length,estimatedRowIndexWrites:writes});
    statements=[];rows=0;writes=0;bytes=0;
  }
  for (const [table,primary] of Object.entries(keys)) {
    const definition=db.prepare("SELECT sql FROM sqlite_schema WHERE type='table' AND name=?").get(table).sql;
    const indexes=db.prepare(`PRAGMA index_list(${table})`).all().filter(i=>!(definition.includes('WITHOUT ROWID')&&i.origin==='pk')).length;
    for (const record of db.prepare(`SELECT * FROM ${table} ORDER BY ${primary.join(',')}`).iterate()) {
      const row={...record}; if (table==='cbank_releases' && row.state!=='retired') row.state='staging';
      const columns=Object.keys(row),immutable=columns.filter(k=>!primary.includes(k) && !(table==='cbank_releases' && k==='state'));
      let conflict;const rowStatements=[];
      if (table==='cbank_publication') conflict="DO UPDATE SET state='retired',retirement_reason=excluded.retirement_reason WHERE excluded.state='retired' AND (state!='retired' OR retirement_reason IS NOT excluded.retirement_reason)";
      else if (table==='bank_legacy_ids') {
        // Explicit conflict guard: this pre-existing table has no immutable-update trigger.
        rowStatements.push(`INSERT INTO cbank_import_checks SELECT 0 WHERE EXISTS(SELECT 1 FROM bank_legacy_ids WHERE source=${quote(row.source)} AND legacy_id=${quote(row.legacy_id)} AND (problem_id IS NOT ${quote(row.problem_id)} OR revision IS NOT ${quote(row.revision)}));`);
        conflict='DO NOTHING';
      } else conflict=`DO UPDATE SET ${primary[0]}=excluded.${primary[0]} WHERE ${immutable.map(k=>`${k} IS NOT excluded.${k}`).join(' OR ')}`;
      const statement=`INSERT INTO ${table}(${columns.join(',')}) VALUES(${columns.map(k=>quote(row[k])).join(',')}) ON CONFLICT(${primary.join(',')}) ${conflict};`;
      rowStatements.push(statement);
      if(table==='cbank_releases' && row.state==='retired') rowStatements.push(`UPDATE cbank_releases SET state='retired' WHERE release_id=${quote(row.release_id)} AND state!='retired';`);
      const sizes=rowStatements.map(s=>Buffer.byteLength(s)),length=sizes.reduce((a,b)=>a+b,0); if(Math.max(...sizes)>90000) throw Error('Statement exceeds conservative D1 bound');
      if(rows>=rowsPerBatch || bytes+length>1_000_000) flush();
      statements.push(...rowStatements); rows++;writes+=1+indexes+(table==='cbank_releases'&&row.state==='retired'?1:0);bytes+=length;maxStatementBytes=Math.max(maxStatementBytes,...sizes);
    }
  }
  flush();
  const releases=db.prepare('SELECT release_id,manifest_json,expected_count FROM cbank_releases ORDER BY release_id').all();
  const contract={format:'compact-import-v1',expected,releases,batches},bundleId=sha(canonical(contract));
  const manifest={...contract,bundleId,maxStatementBytes,totalBatchBytes:batches.reduce((n,b)=>n+b.bytes,0),estimatedDataRowIndexWrites:batches.reduce((n,b)=>n+b.estimatedRowIndexWrites,0),estimatedReceiptWrites:batches.length,remoteStatus:'Not imported. Authenticated atomic-batch adapter and managed allowances remain unknown.'};
  writeFileSync(join(directory,'manifest.json'),JSON.stringify(manifest,null,2)+'\n'); return manifest;
}
export function loadPlan(directory) {
  const p=JSON.parse(readFileSync(join(directory,'manifest.json'),'utf8'));
  if(p.format!=='compact-import-v1' || sha(canonical({format:p.format,expected:p.expected,releases:p.releases,batches:p.batches}))!==p.bundleId) throw Error('Import plan hash mismatch');
  // Validate every local batch before any mutation. The runner never trusts an arbitrary file path.
  for(const batch of p.batches){if(!/^batch-\d{5}\.json$/.test(batch.file) || sha(readFileSync(join(directory,batch.file)))!==batch.sha256) throw Error('Batch checksum mismatch');}
  return p;
}
export function collectMeta(results) {
  const list=Array.isArray(results)?results:[results];
  const sum=key=>list.every(r=>Number.isFinite(r.meta?.[key]))?list.reduce((n,r)=>n+r.meta[key],0):null;
  return {rowsRead:sum('rows_read'),rowsWritten:sum('rows_written'),sizeAfter:list.at(-1)?.meta?.size_after??null,sqlDurationMs:sum('duration')};
}
export async function runImport(db,directory,{local=false,mode='provider-allowance',operator,approval,refreshAllowance,checkpointPath,onProgress=()=>{},startIndex=0,maxBatches}={}) {
  const plan=loadPlan(directory);
  if(!Number.isSafeInteger(startIndex) || startIndex<0 || startIndex>=plan.batches.length)throw Error('Invalid tranche start index');
  if(maxBatches===undefined && local)maxBatches=plan.batches.length-startIndex;
  if(!Number.isSafeInteger(maxBatches) || maxBatches<1)throw Error('Explicit positive tranche batch limit required');
  const endIndexExclusive=Math.min(plan.batches.length,startIndex+maxBatches),startedAt=new Date().toISOString();
  if(mode==='operator-budget'){
    if(local||typeof operator!=='function'||maxBatches>25)throw Error('Operator mode requires authenticated hosted execution and at most 25 batches');
    let state=await operator({op:'status'});
    if(state.budget?.mode!=='operator-budget'||state.bundleId!==plan.bundleId||state.nextSequence!==startIndex)throw Error('Operator checkpoint mismatch');
    if(state.receipts.length!==startIndex||state.receipts.some((r,i)=>r.batch_id!==plan.bundleId+'/'+i||r.sha256!==plan.batches[i].sha256))throw Error('Operator receipt integrity mismatch');
    if(state.nextSequence===state.trancheEnd)state=await operator({op:'open',start:startIndex,end:endIndexExclusive});
    if(state.trancheStart>startIndex||state.trancheEnd!==endIndexExclusive||state.trancheEnd-state.trancheStart>25)throw Error('Operator tranche boundary mismatch');
    let completed=0;
    for(let index=startIndex;index<endIndexExclusive;index++){
      state=await operator({op:'import',index,text:readFileSync(join(directory,plan.batches[index].file),'utf8')});
      if(state.sha256!==plan.batches[index].sha256||state.nextSequence!==index+1||state.halted)throw Error('Operator commit verification failed');
      completed++;if(checkpointPath)appendFileSync(checkpointPath,JSON.stringify({index,nextIndex:index+1,sha256:state.sha256,budget:state.budget,measurements:state.measurements,settlement:state.settlement})+'\n');
      await onProgress({completed,total:endIndexExclusive-startIndex,nextIndex:index+1,budget:state.budget});
    }
    return {mode,bundleId:plan.bundleId,completed,startIndex,endIndexExclusive,nextIndex:endIndexExclusive,hasMore:endIndexExclusive<plan.batches.length,budget:state.budget,provider:state.budget.provider};
  }
  if(mode!=='provider-allowance')throw Error('Unknown import policy');
  // Every invocation/resume needs a new provider usage reading/reservation, including lost responses.
  if(!local){if(typeof refreshAllowance!=='function')throw Error('Supported Sites method and fresh resource allowance required');approval=await refreshAllowance(approval);}
  if(!local && (!approval?.method || approval.projectId!=='appgprj_6ad91db3d4788191b3e73074e27447f5' || approval.binding!=='DB' || approval.bundleId!==plan.bundleId || !Number.isFinite(approval.remainingWrites) || !Number.isFinite(approval.writeReserve) || !Number.isFinite(approval.storageCeilingBytes) || !Number.isFinite(approval.storageHeadroomBytes) || !Number.isFinite(approval.currentSizeBytes) || !Number.isFinite(approval.estimatedImportBytes) || !Number.isFinite(Date.parse(approval.validUntil)) || Date.parse(approval.validUntil)<=Date.now() || !approval.sharedUsageReservation)) throw Error('Supported Sites method and current resource allowance required');
  if(!local && (!Number.isFinite(approval.remainingReads) || !Number.isFinite(approval.readReserve) || !Number.isFinite(Date.parse(approval.checkedAt)) || Math.abs(Date.now()-Date.parse(approval.checkedAt))>30000))throw Error('Fresh read/write usage reservation required');
  if(!local && (approval.startIndex!==startIndex || approval.endIndexExclusive!==endIndexExclusive))throw Error('Allowance must authorize this exact tranche boundary');
  if(!local && [approval.remainingReads,approval.readReserve,approval.remainingWrites,approval.writeReserve,approval.currentSizeBytes,approval.estimatedImportBytes,approval.storageHeadroomBytes,approval.storageCeilingBytes].some(n=>!Number.isSafeInteger(n)||n<0))throw Error('Invalid resource allowance');
  let written=0,read=0,completed=0,skipped=0; const measurements=[];
  let sizeAfter=local?null:approval.currentSizeBytes;
  if(!local && approval.currentSizeBytes+approval.estimatedImportBytes+approval.storageHeadroomBytes>approval.storageCeilingBytes) throw Error('Insufficient agreed storage headroom');
  // Reconcile all earlier receipts before entering the authorized range. A
  // missing earlier checkpoint is an integrity error, never permission to fill it.
  for (let index=0;index<endIndexExclusive;index++) {
    const batch=plan.batches[index],batchId=plan.bundleId+'/'+index;
    if(!local && Date.parse(approval.validUntil)<=Date.now()) throw Error('Allowance window expired; refresh managed usage before resuming');
    if(!local && read+1+approval.readReserve>approval.remainingReads)throw Error('Insufficient allowance for next indexed receipt lookup');
    const old=await db.prepare('SELECT sha256 FROM cbank_import_receipts WHERE batch_id=?').bind(batchId).all();
    const lookup=collectMeta(old);read+=lookup.rowsRead??0;
    if(!local && (lookup.rowsRead===null || read+approval.readReserve>approval.remainingReads))throw Error('Receipt-read allowance exhausted or unavailable; refresh usage before resuming');
    if(!local && (lookup.rowsWritten===null || lookup.sizeAfter===null))throw Error('Receipt lookup lacks required usage counters');
    written+=lookup.rowsWritten??0;sizeAfter=lookup.sizeAfter??sizeAfter;
    if(!local && Date.parse(approval.validUntil)<=Date.now())throw Error('Allowance expired during receipt lookup; no batch written');
    if(!local && (written+approval.writeReserve>approval.remainingWrites || sizeAfter+approval.storageHeadroomBytes>approval.storageCeilingBytes))throw Error('Resource headroom reached during receipt reconciliation');
    if(old.results[0]) {if(old.results[0].sha256!==batch.sha256) throw Error('Receipt conflict');skipped++;measurements.push({batchId,sha256:batch.sha256,skipped:true,receiptLookup:lookup});continue;}
    if(index<startIndex)throw Error('Missing earlier receipt at sequence '+index+'; reconcile checkpoint before resuming');
    if(!local && written+batch.estimatedRowIndexWrites+1+approval.writeReserve>approval.remainingWrites) throw Error('Write allowance reached; resume after a confirmed refresh');
    const statements=JSON.parse(readFileSync(join(directory,batch.file),'utf8')).map(s=>db.prepare(s));
    // A concurrent duplicate must roll back, not silently ignore a conflicting receipt.
    statements.push(db.prepare('INSERT INTO cbank_import_receipts VALUES (?,?)').bind(batchId,batch.sha256));
    if(!local && Date.parse(approval.validUntil)<=Date.now())throw Error('Allowance expired before commit; no batch written');
    // D1 batch contract is atomic. Receipt and data commit together; retry after lost response reads receipt.
    const result=await db.batch(statements); if(result.some(r=>r.success===false)) throw Error('Batch failed');
    const meta=collectMeta(result),entry={batchId,index,nextIndex:index+1,sha256:batch.sha256,committedAt:new Date().toISOString(),receiptLookup:lookup,...meta};measurements.push(entry);completed++;
    if(checkpointPath) appendFileSync(checkpointPath,JSON.stringify(entry)+'\n');onProgress({completed,skipped,total:plan.batches.length,meta});
    if(!local && (meta.rowsRead===null || meta.rowsWritten===null || meta.sizeAfter===null)) throw Error('Committed batch has no resource metadata; reconcile usage before resuming');
    written+=meta.rowsWritten??0;read+=meta.rowsRead??0;sizeAfter=meta.sizeAfter??sizeAfter;
    if(!local && (meta.sizeAfter+approval.storageHeadroomBytes>approval.storageCeilingBytes || written+approval.writeReserve>approval.remainingWrites || read+approval.readReserve>approval.remainingReads)) throw Error('Agreed resource headroom reached; refresh allowance before resuming');
  }
  const finishedAt=new Date().toISOString();
  return {bundleId:plan.bundleId,startIndex,endIndexExclusive,nextIndex:endIndexExclusive,hasMore:endIndexExclusive<plan.batches.length,startedAt,finishedAt,durationMs:Date.parse(finishedAt)-Date.parse(startedAt),completed,skipped,measuredD1Writes:local?null:written,measuredD1Reads:local?null:read,sizeAfter,
    remainingAllowance:local?null:{reads:approval.remainingReads-read,writes:approval.remainingWrites-written,storageBytes:approval.storageCeilingBytes-sizeAfter,readReserve:approval.readReserve,writeReserve:approval.writeReserve,storageReserveBytes:approval.storageHeadroomBytes,validUntil:approval.validUntil,sharedUsageReservation:approval.sharedUsageReservation},
    metadataAvailable:!local&&measurements.every(m=>m.skipped?m.receiptLookup.rowsRead!==null:m.rowsWritten!==null),measurements};
}
export function localImportAdapter(sql) {
  const prepare=(text,values=[])=>({text,values,bind:(...v)=>prepare(text,v),all:async()=>({success:true,results:sql.prepare(text).all(...values)}),run:async()=>({success:true,results:[],changes:sql.prepare(text).run(...values).changes})});
  return {prepare,batch:async statements=>{sql.exec('BEGIN IMMEDIATE');try {const results=[];for(const s of statements)results.push(await s.run());sql.exec('COMMIT');return results;}catch(e){sql.exec('ROLLBACK');throw e;}}};
}
// Paged full-corpus verification can use the supported D1 adapter once it is provided.
// collectMeta deliberately returns null when local SQLite/the provider omits actual D1 counters.
export async function verifyImported(db,plan,{onPage=()=>{}}={}) {
  const identity=createHash('sha256'),publication=createHash('sha256'),membership=createHash('sha256');
  let cursor=['',0],count=0,memberships=0;const coverage={},families={},states={},metadata=[];
  while(true){
    const result=await db.prepare(`SELECT b.*,s.metadata_json,u.state,u.retirement_reason FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE (b.problem_id,b.revision)>(?,?) ORDER BY b.problem_id,b.revision LIMIT 100`).bind(...cursor).all();
    const meta=collectMeta(result);metadata.push(meta);await onPage(meta);
    if(!result.results.length)break;
    for(const row of result.results){
      const p=await decodeCompact(row);identity.update(`${p.problemId}@${p.problemRevision}:${p.contentHash}\n`);publication.update(canonical([p.problemId,p.problemRevision,row.state,row.retirement_reason])+'\n');
      count++;const cell=p.topic+'/'+p.difficulty;coverage[cell]=(coverage[cell]||0)+1;families[p.familyId]=(families[p.familyId]||0)+1;states[row.state]=(states[row.state]||0)+1;cursor=[p.problemId,p.problemRevision];
    }
  }
  let slotCursor=[0,-1];
  while(true){
    const result=await db.prepare('SELECT pool_id,slot,problem_ref FROM cbank_slots WHERE (pool_id,slot)>(?,?) ORDER BY pool_id,slot LIMIT 1000').bind(...slotCursor).all();
    const meta=collectMeta(result);metadata.push(meta);await onPage(meta);if(!result.results.length)break;
    for(const row of result.results){membership.update(canonical(row)+'\n');memberships++;slotCursor=[row.pool_id,row.slot];}
  }
  const pools=await db.prepare('SELECT * FROM cbank_pools ORDER BY pool_id').all();metadata.push(collectMeta(pools));
  const releaseRows=await db.prepare('SELECT release_id,manifest_json,expected_count FROM cbank_releases ORDER BY release_id').all();metadata.push(collectMeta(releaseRows));
  const actual={verified:count,identitySha256:identity.digest('hex'),publicationSha256:publication.digest('hex'),membershipSha256:membership.digest('hex'),poolsSha256:sha(canonical(pools.results)),memberships,coverage,families,publication:states};
  for(const [k,v] of Object.entries(actual))if(canonical(v)!==canonical(plan.expected[k]))throw Error('Hosted verification mismatch: '+k);
  if(canonical(releaseRows.results)!==canonical(plan.releases))throw Error('Release manifest mismatch');
  return {passed:true,verifiedAt:new Date().toISOString(),bundleId:plan.bundleId,...actual,metadata};
}
export async function activateVerified(db,plan,verification,release) {
  if(!verification?.passed || verification.bundleId!==plan.bundleId || !Number.isFinite(Date.parse(verification.verifiedAt)) || Date.now()-Date.parse(verification.verifiedAt)>300000 || verification.identitySha256!==plan.expected.identitySha256 || verification.membershipSha256!==plan.expected.membershipSha256 || !plan.releases.some(r=>r.release_id===release)) throw Error('Fresh complete verification of this import is required');
  const guard=`INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_releases r WHERE r.release_id=? AND r.state!='retired' AND r.expected_count=(SELECT count(*) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_publication u USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*' AND u.state='approved') AND r.expected_count=(SELECT count(DISTINCT b.problem_id) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_problems b USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*'));`;
  const results=await db.batch([db.prepare(guard).bind(release),db.prepare("UPDATE cbank_releases SET state='published' WHERE release_id=?").bind(release),db.prepare("INSERT INTO cbank_config VALUES ('active_release',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(release)]);
  if(results.some(r=>r.success===false))throw Error('Activation failed');
  return {activeRelease:release,...collectMeta(results)};
}
async function main(){
  const [command,path,directory]=process.argv.slice(2);
  if(command==='export') {const db=new DatabaseSync(path,{readOnly:true});try{const p=exportCompact(db,directory);console.log(JSON.stringify({bundleId:p.bundleId,batches:p.batches.length,bytes:p.totalBatchBytes,estimatedDataRowIndexWrites:p.estimatedDataRowIndexWrites,estimatedReceiptWrites:p.estimatedReceiptWrites,maxStatementBytes:p.maxStatementBytes}));}finally{db.close();}}
  else if(command==='apply-local') {const sql=openCompact(path);try{const report=await runImport(localImportAdapter(sql),directory,{local:true,checkpointPath:join(directory,'local-checkpoints.jsonl')});writeFileSync(join(directory,'local-import-report.json'),JSON.stringify({...report,databaseBytes:statSync(path).size},null,2)+'\n');console.log(JSON.stringify({completed:report.completed,skipped:report.skipped,measuredD1Writes:report.measuredD1Writes}));}finally{sql.close();}}
  else if(command==='verify-local') {const sql=new DatabaseSync(path,{readOnly:true});try{const report=await verifyImported(localImportAdapter(sql),loadPlan(directory));writeFileSync(join(directory,'local-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,bundleId:report.bundleId,verified:report.verified}));}finally{sql.close();}}
  else throw Error('Usage: compact-import.mjs export|apply-local|verify-local DATABASE DIRECTORY. Hosted execution requires a Sites adapter, explicit tranche boundary, and fresh managed allowance.');
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(e=>{console.error(e);process.exitCode=1;});
