import PLAN from './operator-plan.json' with {type:'json'};
import {boundedBody,digest,metrics} from './bank-pilot.mjs';
import {canonical,decodeCompact} from '../bank/compact-codec.mjs';
import {OPERATOR_LIMITS,PROVIDER_UNKNOWN,ACCOUNTING_BOUND,HISTORICAL_BOUND,assertOperatorBudget} from './operator-budget.mjs';
import {selectBankQuestions,POOL_SQL} from './compact-bank-selection.ts';
const enc=new TextEncoder(),bundle=PLAN.bundleId;
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export const operatorMessage=(time,hash)=>`calculus-ninja-operator-v1\n${PLAN.projectId}\nPOST\n/api/bank-import\n${time}\n${hash}`;
const receipt=i=>bundle+'/'+i;
const safeMeta=result=>{const m=metrics(result);if([m.rowsRead,m.rowsWritten,m.sizeAfter].some(n=>!Number.isSafeInteger(n)||n<0))throw Error('Missing consumption measurements');return m;};
const budgetView=l=>({mode:'operator-budget',limits:OPERATOR_LIMITS,measuredReads:l.measured_reads,measuredWrites:l.measured_writes,conservativeOverheadReads:l.overhead_reads,conservativeOverheadWrites:l.overhead_writes,chargedReads:l.measured_reads+l.overhead_reads,chargedWrites:l.measured_writes+l.overhead_writes,databaseBytes:l.database_bytes,provider:PROVIDER_UNKNOWN});
function estimate(input,l){
  if(input.op==='import'){const b=PLAN.batches[input.index];return {reads:b.rows*5+100,writes:b.estimatedRowIndexWrites+20};}
  if(input.op==='metadata'||input.op==='activate')return {reads:2000000,writes:20};
  if(input.op==='selection')return {reads:20000,writes:16};
  if(input.op==='problems'||input.op==='pilot')return {reads:1000,writes:16};
  if(input.op==='memberships')return {reads:1100,writes:16};
  return {reads:4000,writes:16};
}
export async function bankOperator(request,db,publicKey,expiresAt){
  const expiry=Number(expiresAt),now=Date.now();
  if(!db||!publicKey||!Number.isFinite(expiry)||now>=expiry)return json({error:'Unavailable'},404);
  if(request.method!=='POST'||new URL(request.url).pathname!=='/api/bank-import'||request.headers.has('origin'))return json({error:'Forbidden'},403);
  const time=request.headers.get('x-bank-time')||'',signature=request.headers.get('x-bank-signature')||'',hash=request.headers.get('x-bank-body-sha256')||'';
  if(!/^\d{13}$/.test(time)||Math.abs(now-Number(time))>60000||!/^[a-f0-9]{64}$/.test(hash)||!/^[A-Za-z0-9+/]{86}==$/.test(signature))return json({error:'Forbidden'},403);
  let input;
  try{
    const key=await crypto.subtle.importKey('spki',Uint8Array.from(atob(publicKey),c=>c.charCodeAt(0)),'Ed25519',false,['verify']);
    if(!await crypto.subtle.verify('Ed25519',key,Uint8Array.from(atob(signature),c=>c.charCodeAt(0)),enc.encode(operatorMessage(time,hash))))return json({error:'Forbidden'},403);
    const bytes=await boundedBody(request);if(await digest(bytes)!==hash)return json({error:'Body hash mismatch'},403);input=JSON.parse(new TextDecoder().decode(bytes));
  }catch{return json({error:'Invalid authentication or body'},403);}
  if(!input||!/^[a-f0-9-]{36}$/.test(input.id)||!['init','status','open','import','pilot','problems','memberships','metadata','selection','activate'].includes(input.op))return json({error:'Invalid operation'},400);
  if(Date.now()>=expiry)return json({error:'Credential expired'},403);
  // Reject malformed/out-of-range work before any database reads.
  if(input.op==='import'){
    if(!Number.isInteger(input.index)||!PLAN.batches[input.index]||typeof input.text!=='string')return json({error:'Invalid batch'},400);
    const b=PLAN.batches[input.index],bytes=enc.encode(input.text);
    if(bytes.length!==b.bytes||await digest(bytes)!==b.sha256)return json({error:'Batch checksum mismatch'},400);
  }
  const begun=performance.now(),observed=[];
  const all=async(sql,args=[])=>{const r=await db.prepare(sql).bind(...args).all();observed.push(safeMeta(r));return r.results;};
  const batch=async statements=>{const r=await db.batch(statements);observed.push(safeMeta(r));if(r.some(v=>!v.success))throw Error('Provider batch failed');return r;};
  let ledger,claimed=false;
  try{
    ledger=(await all('SELECT * FROM cbank_operator_ledger WHERE bundle_id=?',[bundle]))[0];
    if(!ledger){
      if(input.op!=='init')return json({error:'Initialize operator ledger first',measurements:observed},409);
      const receipts=await all('SELECT batch_id,sha256 FROM cbank_import_receipts ORDER BY batch_id LIMIT 5');
      if(receipts.length!==4||receipts.some((r,i)=>r.batch_id!==receipt(i)||r.sha256!==PLAN.batches[i].sha256))throw Error('Initial receipt integrity mismatch');
      await batch([db.prepare(`INSERT INTO cbank_operator_ledger(bundle_id,measured_reads,measured_writes,overhead_reads,overhead_writes,database_bytes,next_sequence,tranche_start,tranche_end,pilot_verified,problem_pages,membership_pages,metadata_verified,selection_cells,activated,pending_reads,pending_writes,updated_at)
        VALUES(?,7431,3860,?,?,?,4,4,8,0,0,0,0,0,0,0,0,?)`).bind(bundle,HISTORICAL_BOUND.reads,HISTORICAL_BOUND.writes,observed.at(-1).sizeAfter,new Date().toISOString())]);
      ledger=(await all('SELECT * FROM cbank_operator_ledger WHERE bundle_id=?',[bundle]))[0];
    }
    if(ledger.last_id===input.id){if(ledger.last_hash!==hash)return json({error:'Operation ID conflict'},409);return json({...JSON.parse(ledger.last_result),replayed:true,recoveryMeasurements:observed});}
    if(ledger.pending_id){
      const committedReceipt=input.op==='import'?(await all('SELECT batch_id,sha256 FROM cbank_import_receipts WHERE batch_id=?',[receipt(input.index)]))[0]??null:null;
      return json({error:'Unreconciled in-flight operation',pendingId:ledger.pending_id,pendingHash:ledger.pending_hash,nextSequence:ledger.next_sequence,committedReceipt,budget:budgetView(ledger),recoveryMeasurements:observed},409);
    }
    if(ledger.halted)return json({error:'Operator stopped',reason:ledger.halted,budget:budgetView(ledger),measurements:observed},409);
    ledger.database_bytes=Math.max(ledger.database_bytes,observed.at(-1).sizeAfter);
    if(input.op==='open'&&(!Number.isInteger(input.end)||ledger.next_sequence!==ledger.tranche_end||input.start!==ledger.next_sequence||input.end<=input.start||input.end-input.start>25||input.end>1850||(ledger.next_sequence===8&&ledger.pilot_verified!==1000)))return json({error:'Invalid tranche boundary or unverified operator pilot'},409);
    if(input.op==='import'&&(input.index!==ledger.next_sequence||input.index>=ledger.tranche_end||ledger.activated))return json({error:'Outside current tranche',nextSequence:ledger.next_sequence,trancheEnd:ledger.tranche_end},409);
    if(input.op==='pilot'&&(ledger.next_sequence!==8||input.page!==ledger.pilot_verified/100||!PLAN.pilot[input.page]))return json({error:'Invalid pilot verification checkpoint'},409);
    if(['problems','memberships','metadata','selection','activate'].includes(input.op)&&ledger.next_sequence!==1850)return json({error:'Full receipt checkpoint required'},409);
    if(input.op==='problems'&&(input.page!==ledger.problem_pages||!PLAN.problems[input.page]))return json({error:'Invalid problem verification checkpoint'},409);
    if(input.op==='memberships'&&(input.page!==ledger.membership_pages||!PLAN.memberships[input.page]))return json({error:'Invalid membership verification checkpoint'},409);
    if(input.op==='selection'&&(input.cell!==ledger.selection_cells||!PLAN.cells[input.cell]||!ledger.metadata_verified))return json({error:'Invalid selection checkpoint'},409);
    if(input.op==='activate'&&(ledger.problem_pages!==PLAN.problems.length||ledger.membership_pages!==PLAN.memberships.length||!ledger.metadata_verified||ledger.selection_cells!==24||ledger.activated))return json({error:'Complete verified bank required'},409);
    const planned=estimate(input,ledger);
    assertOperatorBudget(ledger,planned,{readReserve:input.op==='import'?2500000:0,writeReserve:input.op==='import'?40000:0,byteReserve:input.op==='import'?PLAN.batches[input.index].bytes*2+1000000:1000000});
    const lock=await batch([db.prepare(`UPDATE cbank_operator_ledger SET pending_id=?,pending_hash=?,pending_reads=?,pending_writes=?,overhead_reads=overhead_reads+?,overhead_writes=overhead_writes+?,updated_at=? WHERE bundle_id=? AND pending_id IS NULL AND halted IS NULL AND next_sequence=? RETURNING bundle_id`).bind(input.id,hash,planned.reads,planned.writes,ACCOUNTING_BOUND.reads,ACCOUNTING_BOUND.writes,new Date().toISOString(),bundle,ledger.next_sequence)]);
    if(lock[0].results.length!==1)return json({error:'Concurrent importer rejected',measurements:observed},423);
    claimed=true;ledger.overhead_reads+=ACCOUNTING_BOUND.reads;ledger.overhead_writes+=ACCOUNTING_BOUND.writes;
    if(Date.now()>=expiry)throw Error('Credential expired before operation');
    let result={op:input.op};
    if(input.op==='init'||input.op==='status'){
      const receipts=await all('SELECT batch_id,sha256 FROM cbank_import_receipts WHERE batch_id>=? AND batch_id<? ORDER BY batch_id',[bundle+'/',bundle+'0']);
      const sorted=receipts.sort((a,b)=>Number(a.batch_id.split('/').at(-1))-Number(b.batch_id.split('/').at(-1)));
      if(sorted.length!==ledger.next_sequence||sorted.some((r,i)=>r.batch_id!==receipt(i)||r.sha256!==PLAN.batches[i].sha256))throw Error('Receipt checkpoint integrity mismatch');
      result.receipts=sorted;
    }else if(input.op==='open'){ledger.tranche_start=input.start;ledger.tranche_end=input.end;
    }else if(input.op==='import'){
      const old=await all('SELECT sha256 FROM cbank_import_receipts WHERE batch_id=?',[receipt(input.index)]);if(old.length)throw Error('Receipt unexpectedly exists');
      const previous=await all('SELECT sha256 FROM cbank_import_receipts WHERE batch_id=?',[receipt(input.index-1)]);if(previous[0]?.sha256!==PLAN.batches[input.index-1].sha256)throw Error('Previous receipt integrity mismatch');
      const statements=JSON.parse(input.text);if(statements.length!==PLAN.batches[input.index].statements)throw Error('Statement count mismatch');
      await batch([...statements.map(sql=>db.prepare(sql)),db.prepare('INSERT INTO cbank_import_receipts VALUES (?,?)').bind(receipt(input.index),PLAN.batches[input.index].sha256)]);
      ledger.next_sequence++;result.index=input.index;result.sha256=PLAN.batches[input.index].sha256;
    }else if(input.op==='pilot'||input.op==='problems'){
      const p=(input.op==='pilot'?PLAN.pilot:PLAN.problems)[input.page];
      const rows=input.op==='pilot'?await all('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) WHERE problem_ref>? AND problem_ref<=? ORDER BY problem_ref',[p.cursor,p.cursor+100]):await all('SELECT b.*,s.metadata_json,u.state,u.retirement_reason FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE (b.problem_id,b.revision)>(?,?) ORDER BY b.problem_id,b.revision LIMIT 100',p.cursor);
      const tuples=[];for(const row of rows){const problem=await decodeCompact(row);tuples.push(input.op==='pilot'?[problem.problemId,problem.problemRevision,problem.contentHash]:[problem.problemId,problem.problemRevision,problem.contentHash,row.state,row.retirement_reason]);}
      if(rows.length!==p.count||await digest(enc.encode(canonical(tuples)))!==p.hash)throw Error('Canonical problem verification mismatch');
      if(input.op==='pilot')ledger.pilot_verified+=rows.length;else ledger.problem_pages++;result.verified=rows.length;result.page=input.page;result.hash=p.hash;
    }else if(input.op==='memberships'){
      const p=PLAN.memberships[input.page],rows=await all('SELECT pool_id,slot,problem_ref FROM cbank_slots WHERE (pool_id,slot)>(?,?) ORDER BY pool_id,slot LIMIT 1000',p.cursor);
      if(rows.length!==p.count||await digest(enc.encode(rows.map(r=>canonical(r)+'\n').join('')))!==p.hash)throw Error('Membership verification mismatch');
      ledger.membership_pages++;result.verified=rows.length;result.page=input.page;result.hash=p.hash;
    }else if(input.op==='metadata'){
      const pools=await all('SELECT * FROM cbank_pools ORDER BY pool_id'),releases=await all('SELECT release_id,manifest_json,expected_count FROM cbank_releases ORDER BY release_id');
      if(await digest(enc.encode(canonical(pools)))!==PLAN.expected.poolsSha256||canonical(releases)!==canonical(PLAN.releases))throw Error('Pool or release metadata mismatch');
      const counts=(await all(`SELECT (SELECT count(*) FROM cbank_problems) AS problems,(SELECT count(*) FROM cbank_slots) AS memberships,(SELECT count(*) FROM cbank_publication WHERE state='approved') AS approved,(SELECT count(*) FROM cbank_shared) AS shared,(SELECT count(*) FROM cbank_import_receipts WHERE batch_id>=? AND batch_id<?) AS receipts,(SELECT value FROM cbank_config WHERE key='active_release') AS active`,[bundle+'/',bundle+'0']))[0];
      if(counts.problems!==100800||counts.memberships!==260400||counts.approved!==100800||counts.shared!==72||counts.receipts!==1850||counts.active!==null)throw Error('Corpus totals or inactive-state mismatch');
      const bad=await all('PRAGMA foreign_key_check');if(bad.length)throw Error('Foreign-key integrity mismatch');
      ledger.metadata_verified=1;result.counts=counts;
    }else if(input.op==='selection'){
      const cell=PLAN.cells[input.cell],slash=cell.lastIndexOf('/'),category=cell.slice(0,slash),difficulty=cell.slice(slash+1);
      // Use the production sampler with a read-only staged-release pool lookup.
      const wrap=stmt=>({bind:(...args)=>wrap(stmt.bind(...args)),all:async()=>{const r=await stmt.all();observed.push(safeMeta(r));return r;},raw:stmt});
      const sampled={prepare(sql){return wrap(db.prepare(sql===POOL_SQL?sql.replace("p.release_id=(SELECT value FROM cbank_config WHERE key='active_release') AND r.state='published'","p.release_id='cn-2026-11-02-full-v2' AND r.state='staging'"):sql));},batch:async statements=>{const r=await db.batch(statements.map(s=>s.raw));observed.push(safeMeta(r));return r;}};
      const selection=await selectBankQuestions(sampled,{category,difficulty,count:20});if(new Set(selection.questions.map(q=>q.problemId)).size!==20)throw Error('Selection duplicates');
      ledger.selection_cells++;result.cell=cell;result.selected=20;
    }else if(input.op==='activate'){
      const release=PLAN.releases[0].release_id;
      const guard=`INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_releases r WHERE r.release_id=? AND r.state='staging' AND r.expected_count=(SELECT count(*) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_publication u USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*' AND u.state='approved') AND r.expected_count=(SELECT count(DISTINCT b.problem_id) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_problems b USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*'));`;
      await batch([db.prepare(guard).bind(release),db.prepare("UPDATE cbank_releases SET state='published' WHERE release_id=? AND state='staging'").bind(release),db.prepare("INSERT INTO cbank_config VALUES ('active_release',?)").bind(release)]);ledger.activated=1;result.activeRelease=release;
    }
    const totals=observed.reduce((a,m)=>({reads:a.reads+m.rowsRead,writes:a.writes+m.rowsWritten}),{reads:0,writes:0});
    ledger.measured_reads+=totals.reads;ledger.measured_writes+=totals.writes;ledger.database_bytes=Math.max(...observed.map(m=>m.sizeAfter));
    if(totals.reads>planned.reads||totals.writes>planned.writes)ledger.halted='Operation exceeded its conservative reservation; inspect actual usage';
    if(ledger.measured_reads+ledger.overhead_reads>OPERATOR_LIMITS.reads||ledger.measured_writes+ledger.overhead_writes>OPERATOR_LIMITS.writes||ledger.database_bytes>OPERATOR_LIMITS.bytes)ledger.halted='Operator cumulative limit reached';
    result={...result,id:input.id,bundleId:bundle,nextSequence:ledger.next_sequence,trancheStart:ledger.tranche_start,trancheEnd:ledger.tranche_end,pilotVerified:ledger.pilot_verified,problemPages:ledger.problem_pages,membershipPages:ledger.membership_pages,metadataVerified:ledger.metadata_verified,selectionCells:ledger.selection_cells,activated:ledger.activated,halted:ledger.halted,budget:budgetView(ledger),measurements:observed,serverMs:performance.now()-begun};
    // Final accounting write is covered by the separate fixed overhead bound.
    // Its actual counters are returned and durably recorded by the operator client.
    const settled=await db.prepare(`UPDATE cbank_operator_ledger SET measured_reads=?,measured_writes=?,database_bytes=?,next_sequence=?,tranche_start=?,tranche_end=?,pilot_verified=?,problem_pages=?,membership_pages=?,metadata_verified=?,selection_cells=?,activated=?,pending_id=NULL,pending_hash=NULL,pending_reads=0,pending_writes=0,last_id=?,last_hash=?,last_result=?,halted=?,updated_at=? WHERE bundle_id=? AND pending_id=?`).bind(ledger.measured_reads,ledger.measured_writes,ledger.database_bytes,ledger.next_sequence,ledger.tranche_start,ledger.tranche_end,ledger.pilot_verified,ledger.problem_pages,ledger.membership_pages,ledger.metadata_verified,ledger.selection_cells,ledger.activated,input.id,hash,JSON.stringify(result),ledger.halted,new Date().toISOString(),bundle,input.id).run();
    const settlement=safeMeta(settled);if(settlement.rowsWritten>ACCOUNTING_BOUND.writes||settlement.rowsRead>ACCOUNTING_BOUND.reads||settlement.sizeAfter>OPERATOR_LIMITS.bytes)throw Error('Accounting overhead or storage bound exceeded');
    return json({...result,settlement},ledger.halted?409:200);
  }catch(error){
    const raw=String(error),reason=/quota|limit.*exceed|exceed.*limit/i.test(raw)?'provider-quota-or-limit':/rate|throttl/i.test(raw)?'provider-rate-limit':/denied|unauthoriz|forbidden/i.test(raw)?'provider-access-denial':/Missing consumption/i.test(raw)?'missing-consumption-measurements':/Operator|Provider .* limit/i.test(raw)?raw.replace(/^Error: /,''):/mismatch|integrity|checkpoint|duplicates/i.test(raw)?'integrity-mismatch':'operation-failed';
    // Leave a claimed operation pending on uncertainty. Never clear its reservation
    // or retry a possibly committed write without recovering its measured receipt.
    return json({error:reason,pending:claimed,id:input.id,nextSequence:ledger?.next_sequence,measurements:observed,serverMs:performance.now()-begun},503);
  }
}
