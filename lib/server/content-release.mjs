// Temporary signed release operator. No public activation and no arbitrary SQL.
// Authorization is scoped to one compiled plan; disabled unless an expiring key
// and an explicit new allowance are installed. Previous allowance is not reused.
import { boundedBody,digest,metrics } from './bank-pilot.mjs';
import { canonical,decodeCompact } from '../bank/compact-codec.mjs';
import { selectBankQuestions,POOL_SQL } from './compact-bank-selection.ts';
const enc=new TextEncoder(),json=(b,status=200)=>Response.json(b,{status,headers:{'Cache-Control':'no-store'}});
export const message=(plan,time,hash)=>`calculus-ninja-content-delta-v1\n${plan.projectId}\n${plan.bundleId}\nPOST\n/api/content-release\n${time}\n${hash}`;
const safe=m=>{if([m.rowsRead,m.rowsWritten,m.sizeAfter].some(n=>!Number.isSafeInteger(n)||n<0))throw Error('Missing provider consumption measurements');return m;};
const encode=row=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k,v instanceof Uint8Array||Array.isArray(v)?Array.from(v).map(b=>b.toString(16).padStart(2,'0')).join(''):v]));
export function steps(plan){return [...plan.batches.map((b,index)=>({kind:'import',index,...b})),...plan.pages.map((p,index)=>({kind:'problem-page',index,...p})),...plan.tableHashes.map((t,index)=>({kind:'table',index,...t})),...(plan.cells||[]).map((c,index)=>({kind:'selection',index,...c}))];}
export async function contentRelease(request,db,plan,{publicKey,expiresAt,allowance}={}){
 let permit;try{permit=JSON.parse(allowance||'null');}catch{}
 if(!db||!plan?.bundleId||!publicKey||Date.now()>=Number(expiresAt)||!Number.isFinite(Number(expiresAt))||!permit||permit.bundleId!==plan.bundleId||![permit.reads,permit.writes,permit.bytes].every(n=>Number.isSafeInteger(n)&&n>0))return json({error:'Unavailable'},404);
 if(request.method!=='POST'||new URL(request.url).pathname!=='/api/content-release'||request.headers.has('origin'))return json({error:'Forbidden'},403);
 const time=request.headers.get('x-bank-time')||'',hash=request.headers.get('x-bank-body-sha256')||'',signature=request.headers.get('x-bank-signature')||'';let input;
 try{
  if(!/^\d{13}$/.test(time)||Math.abs(Date.now()-Number(time))>60000||!/^[a-f0-9]{64}$/.test(hash)||!/^[A-Za-z0-9+/]{86}==$/.test(signature))throw Error();
  const key=await crypto.subtle.importKey('spki',Uint8Array.from(atob(publicKey),c=>c.charCodeAt(0)),'Ed25519',false,['verify']);
  if(!await crypto.subtle.verify('Ed25519',key,Uint8Array.from(atob(signature),c=>c.charCodeAt(0)),enc.encode(message(plan,time,hash))))throw Error();
  const bytes=await boundedBody(request);if(await digest(bytes)!==hash)throw Error();input=JSON.parse(new TextDecoder().decode(bytes));
 }catch{return json({error:'Invalid authentication or body'},403);}
 const program=steps(plan),step=program[input?.step];
 if(!input||!['init','status','step','activate','rollback'].includes(input.op)||input.op==='step'&&(!Number.isInteger(input.step)||!step))return json({error:'Invalid operation'},400);
 if(input.op==='step'&&step.kind==='import'&&(typeof input.text!=='string'||enc.encode(input.text).length!==step.bytes||await digest(enc.encode(input.text))!==step.sha256))return json({error:'Batch checksum mismatch'},400);
 const observed=[],started=performance.now();let nonce,ledger;
 const all=async(sql,args=[])=>{const r=await db.prepare(sql).bind(...args).all();observed.push(safe(metrics(r)));return r.results;};
 const batch=async(stmts)=>{const rs=await db.batch(stmts);observed.push(safe(metrics(rs)));if(rs.some(r=>!r.success))throw Error('Atomic batch failed');return rs;};
 const active=async()=> (await all("SELECT value FROM cbank_config WHERE key='active_release'"))[0]?.value;
 const receiptId=plan.bundleId+'/'+(input.op==='step'?input.step:input.op);
 const view=()=>({bundleId:plan.bundleId,nextSequence:ledger.next_sequence,totalSteps:program.length,activated:ledger.activated,verified:ledger.verified,halted:ledger.halted,
  allowance:permit,chargedReads:ledger.charged_reads,chargedWrites:ledger.charged_writes,measuredReads:ledger.measured_reads,measuredWrites:ledger.measured_writes,priorChargedReads:ledger.prior_reads,priorChargedWrites:ledger.prior_writes,databaseBytes:ledger.database_bytes,providerRemainingReads:null,providerRemainingWrites:null});
 try{
  ledger=(await all('SELECT * FROM cbank_delta_ledger WHERE bundle_id=?',[plan.bundleId]))[0];
  if(ledger){
   const charged=await batch([db.prepare('UPDATE cbank_delta_ledger SET charged_reads=charged_reads+32,charged_writes=charged_writes+8 WHERE bundle_id=? AND charged_reads+32<=? AND charged_writes+8<=? RETURNING *').bind(plan.bundleId,permit.reads,permit.writes)]);
   if(!charged[0].results.length)throw Error('Request accounting allowance exhausted');ledger=charged[0].results[0];
  }
  if(!ledger){
   if(input.op!=='init')return json({error:'Initialize first',measurements:observed},409);
   const prior=(await all('SELECT measured_reads,measured_writes,overhead_reads,overhead_writes,pending_id,halted,activated FROM cbank_operator_ledger WHERE bundle_id=?',[plan.priorBundleId]))[0];
   if(!prior||prior.pending_id||prior.halted||prior.activated!==1)throw Error('Prior operation is not settled');
   const totals={reads:prior.measured_reads+prior.overhead_reads,writes:prior.measured_writes+prior.overhead_writes};
   if(totals.reads+permit.reads>5000000||totals.writes+permit.writes>1300000||permit.bytes>150000000)throw Error('New allowance exceeds cumulative operating ceiling');
   const parent=(await all('SELECT manifest_json,expected_count,state FROM cbank_releases WHERE release_id=?',[plan.parentRelease]))[0];
   if(await active()!==plan.parentRelease||!parent||parent.state!=='published'||parent.expected_count!==plan.before.parentCount||await digest(enc.encode(parent.manifest_json))!==plan.before.parentManifestSha256)throw Error('Parent identity or active release changed');
   const sizes=(await all('SELECT (SELECT max(problem_ref) FROM cbank_problems) AS problemRef,(SELECT max(shared_id) FROM cbank_shared) AS sharedId,(SELECT max(pool_id) FROM cbank_pools) AS poolId'))[0];
   if(['problemRef','sharedId','poolId'].some(k=>sizes[k]!==plan.before[k]))throw Error('Baseline changed; prepare a new delta');
   // Conservatively cover schema deployment and bounded read-only preflight
   // work whose individual provider counters are not exposed by Sites.
   if(permit.reads<10000||permit.writes<1000)throw Error('Allowance cannot cover preflight overhead');
   await batch([db.prepare(`INSERT INTO cbank_delta_ledger(bundle_id,measured_reads,measured_writes,charged_reads,charged_writes,prior_reads,prior_writes,database_bytes,next_sequence,verified,activated,updated_at) VALUES(?,0,0,10000,1000,?,?,?,0,0,0,?)`).bind(plan.bundleId,totals.reads,totals.writes,observed.at(-1).sizeAfter,new Date().toISOString())]);
   ledger=(await all('SELECT * FROM cbank_delta_ledger WHERE bundle_id=?',[plan.bundleId]))[0];
  }
  const old=(await all('SELECT sha256 FROM cbank_import_receipts WHERE batch_id=?',[receiptId]))[0];
  // Every operation receipt has a deterministic plan identity, independent of
  // request timestamps and lost responses. Replays never rerun corpus writes.
  const receiptHash=input.op==='step'?step.sha256:await digest(enc.encode(plan.bundleId+':'+input.op));
  if(old){if(old.sha256!==receiptHash)throw Error('Receipt conflict');return json({...view(),replayed:true,measurements:observed});}
  if(ledger.halted)throw Error('Operator halted: '+ledger.halted);
  if(ledger.pending_id&&Date.now()-Date.parse(ledger.updated_at)<120000)return json({error:'Operation in flight; retain request and retry',...view(),measurements:observed},409);
  if(input.op==='step'&&(input.step!==ledger.next_sequence||ledger.activated))throw Error('Wrong import/verification checkpoint');
  if(input.op==='activate'&&(ledger.next_sequence!==program.length||!ledger.verified||ledger.activated))throw Error('Complete verification required');
  if(input.op==='rollback'&&!ledger.activated)throw Error('Release not active');
  const reservation=input.op==='step'&&step.kind==='import'?{reads:step.estimatedReads,writes:step.estimatedWrites}:input.op==='step'?{reads:step.kind==='table'?Math.max(100,step.count*8):step.kind==='selection'?5000:500,writes:20}:input.op==='activate'?{reads:plan.newCount*12+1000,writes:30}:{reads:100,writes:20};
  // Charge conservative reservations durably before work, including failed or
  // ambiguous work. Actual counters are tracked separately; no refund on retry.
  reservation.reads+=100;reservation.writes+=20;
  if(ledger.charged_reads+reservation.reads>permit.reads||ledger.charged_writes+reservation.writes>permit.writes||Math.max(ledger.database_bytes,observed.at(-1).sizeAfter)+2000000>permit.bytes)throw Error('Bounded allowance exhausted');
  nonce=crypto.randomUUID();const stamp=new Date().toISOString();
  const lock=await batch([db.prepare(`UPDATE cbank_delta_ledger SET pending_id=?,pending_hash=?,charged_reads=charged_reads+?,charged_writes=charged_writes+?,updated_at=? WHERE bundle_id=? AND next_sequence=? AND (pending_id IS NULL OR updated_at<=?) AND halted IS NULL AND charged_reads+?<=? AND charged_writes+?<=? RETURNING bundle_id`).bind(nonce,hash,reservation.reads,reservation.writes,stamp,plan.bundleId,ledger.next_sequence,new Date(Date.now()-120000).toISOString(),reservation.reads,permit.reads,reservation.writes,permit.writes)]);
  if(lock[0].results.length!==1)return json({error:'Concurrent operator rejected',measurements:observed},423);
  const guard=()=>db.prepare('INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_delta_ledger WHERE bundle_id=? AND pending_id=? AND pending_hash=?)').bind(plan.bundleId,nonce,hash);
  let mutations=[],newSequence=ledger.next_sequence,verified=ledger.verified,activated=ledger.activated,selection;
  if(input.op==='step'){
   if(step.kind==='import'){const sql=JSON.parse(input.text);if(sql.length!==step.statements||sql.some(s=>typeof s!=='string'))throw Error('Invalid compiled batch');mutations=sql.map(s=>db.prepare(s));}
   else if(step.kind==='problem-page'){
    const rows=await all('SELECT b.*,m.metadata_json,u.state FROM cbank_problems b JOIN cbank_shared m USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE problem_ref>? ORDER BY problem_ref LIMIT 40',[step.cursor]);const tuples=[];
    for(const row of rows){const p=await decodeCompact(row);tuples.push([p.problemId,p.problemRevision,p.contentHash,row.state]);}
    if(rows.length!==step.count||await digest(enc.encode(canonical(tuples)))!==step.sha256)throw Error('Decoded payload verification failed');
   }else if(step.kind==='selection'){
    // Only the compiled release pointer/state changes for this read-only smoke
    // check. Every candidate/ordering/decode query is the production sampler.
    if(!/^[a-z0-9-]+$/.test(plan.release))throw Error('Invalid compiled release identifier');
    const poolSql=POOL_SQL.replace('cbank_config c',`(SELECT 'active_release' AS key,'${plan.release}' AS value) c`).replace("active.state='published' AND r.state='published'","active.state='staging' AND (r.state='published' OR r.release_id=c.value AND r.state='staging')");
    const wrap=statement=>({bind:(...args)=>wrap(statement.bind(...args)),all:async()=>{const r=await statement.all();observed.push(safe(metrics(r)));return r;},raw:statement});
    const staged={prepare:sql=>wrap(db.prepare(sql===POOL_SQL?poolSql:sql)),batch:async statements=>{const rs=await db.batch(statements.map(s=>s.raw));observed.push(safe(metrics(rs)));return rs;}};
    const r=await selectBankQuestions(staged,step.input),counts={};for(const q of r.questions)counts[q.familyId]=(counts[q.familyId]||0)+1;
    if(new Set(r.questions.map(q=>q.problemId)).size!==step.input.count||r.questions.some((q,i)=>i&&q.familyId===r.questions[i-1].familyId)||Math.max(...Object.values(counts))>2||r.relaxation!=='none')throw Error('Hosted broad-pool acceptance failed');
    selection={input:step.input,distinctFamilies:Object.keys(counts).length,diagnostics:r.diagnostics};
   }else{
    const rows=await all(`SELECT * FROM ${step.table} WHERE ${step.where} ORDER BY ${step.order}`,step.args);
    if(rows.length!==step.count||await digest(enc.encode(canonical(rows.map(encode))))!==step.sha256)throw Error('Delta metadata/membership verification failed: '+step.table);
   }
   newSequence++;if(newSequence===program.length)verified=1;
  }else if(input.op==='activate'){
   if(await active()!==plan.parentRelease)throw Error('Active release changed');
   mutations=[db.prepare("INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_config c JOIN cbank_releases r ON r.release_id=c.value WHERE c.key='active_release' AND c.value=? AND r.state='published')").bind(plan.parentRelease),db.prepare(`INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_releases r WHERE r.release_id=? AND r.state='staging' AND r.expected_count=? AND r.expected_count=(SELECT count(*) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_publication u USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*' AND u.state='approved') AND r.expected_count=(SELECT count(DISTINCT b.problem_id) FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_problems b USING(problem_ref) WHERE p.release_id=r.release_id AND p.tag='*'))`).bind(plan.release,plan.newCount),db.prepare("UPDATE cbank_releases SET state='published' WHERE release_id=?").bind(plan.release),db.prepare("UPDATE cbank_config SET value=? WHERE key='active_release' AND value=?").bind(plan.release,plan.parentRelease)];activated=1;
  }else if(input.op==='rollback'){
   if(await active()!==plan.release)throw Error('Do not overwrite a newer release');mutations=[db.prepare("INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_config WHERE key='active_release' AND value=?)").bind(plan.release),db.prepare("UPDATE cbank_config SET value=? WHERE key='active_release' AND value=?").bind(plan.parentRelease,plan.release)];activated=2;
  }
  if(Date.now()>=Number(expiresAt))throw Error('Credential expired before commit');
  await batch([guard(),...mutations,db.prepare('INSERT INTO cbank_import_receipts VALUES (?,?)').bind(receiptId,receiptHash),db.prepare('UPDATE cbank_delta_ledger SET next_sequence=?,verified=?,activated=?,pending_id=NULL,pending_hash=NULL,updated_at=? WHERE bundle_id=? AND pending_id=?').bind(newSequence,verified,activated,new Date().toISOString(),plan.bundleId,nonce)]);
  const actual=observed.reduce((v,m)=>({reads:v.reads+m.rowsRead,writes:v.writes+m.rowsWritten}),{reads:0,writes:0});
  const size=Math.max(...observed.map(m=>m.sizeAfter)),halted=actual.reads>reservation.reads||actual.writes>reservation.writes||size>permit.bytes?'Measured operation exceeded reservation; inspect before continuing':null;
  await batch([db.prepare('UPDATE cbank_delta_ledger SET measured_reads=measured_reads+?,measured_writes=measured_writes+?,charged_reads=charged_reads+?,charged_writes=charged_writes+?,database_bytes=?,halted=?,updated_at=? WHERE bundle_id=?').bind(actual.reads,actual.writes,Math.max(0,actual.reads-reservation.reads),Math.max(0,actual.writes-reservation.writes),size,halted,new Date().toISOString(),plan.bundleId)]);
  ledger=(await all('SELECT * FROM cbank_delta_ledger WHERE bundle_id=?',[plan.bundleId]))[0];
  return json({...view(),...(selection?{selection}:{}),measurements:observed,serverMs:performance.now()-started});
 }catch(e){return json({error:e.message,...(ledger?view():{}),measurements:observed},409);}
}
