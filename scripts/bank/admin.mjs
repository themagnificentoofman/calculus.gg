#!/usr/bin/env node
// Operator-only CLI: local private files or D1 SQL export; never included in Worker/client bundles.
import { spawnSync } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
import { createHash } from 'node:crypto';
import { createReadStream, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { questionMathIsRenderable } from '../../lib/render-math.mjs';
import { topics, difficulties, validQuestionResponse } from '../../lib/server/questions-policy.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
export const canonical=value=>value && typeof value==='object' ? Array.isArray(value) ? `[${value.map(canonical).join(',')}]` : `{${Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')}}` : JSON.stringify(value);
export const hash=value=>createHash('sha256').update(canonical(value)).digest('hex');
export const releaseContract=manifest=>Object.fromEntries(Object.entries(manifest).filter(([key])=>!['elapsedSeconds','generatedThisRun','rejectedThisRun','duplicatesThisRun'].includes(key)));
export function validateRecord(p) {
  const {contentHash,...body}=p;
  if (![1,2].includes(p.schemaVersion) || !/^cn_[a-f0-9]{20}$/.test(p.problemId) || !Number.isInteger(p.problemRevision)||p.problemRevision<1 || hash(body)!==contentHash) throw Error('Invalid immutable identity/hash');
  if (!topics.includes(p.topic)||!difficulties.includes(p.difficulty)||!Array.isArray(p.choices)||p.choices.length!==4||new Set(p.choices.map(c=>c.choiceId)).size!==4||p.choices.filter(c=>c.choiceId===p.answerChoiceId).length!==1) throw Error('Invalid classification/choices');
  if (!p.familyId || !p.templateVersion || !p.provenance?.license || !p.provenance?.attribution || !p.assumptions?.length || !p.techniqueTags?.length || !p.estimates?.basis || p.validation?.status!=='passed' || !p.validation.evidence?.solutionDerivationChecked || !p.validation.evidence?.assumptionsChecked) throw Error('Missing approval evidence');
  if(p.schemaVersion===2){
    const m=p.pedagogy, list=v=>Array.isArray(v)&&v.every(s=>typeof s==='string'&&s.length>0&&s.length<1000);
    if(!m||['constructionId','relatedIdeaGroupId','structuralSignature','primaryTechnique','answerForm','difficultyRationale'].some(k=>typeof m[k]!=='string'||!m[k].trim())||m.constructionId!==p.familyId||m.responseFormat!=='multiple-choice'||!list(m.alternativeTechniques)||!list(m.prerequisites)||!list(m.sourceRecordIds)||!list(m.reasoningDemand)||!m.reasoningDemand.length||m.reasoningDemand.some(v=>!['execution','recognition','method-selection','reframing','convergence','synthesis'].includes(v)))throw Error('Missing v2 pedagogy contract');
    if(!p.validation.methods?.length||p.validation.humanReviewed!==false||!p.validation.evidence.uniqueCorrectOption||!p.validation.evidence.verificationRoute||!p.validation.evidence.parameterDomain||p.choices.some(c=>typeof c.misconception!=='string'))throw Error('Missing v2 reproducible verification or distractor rationale');
  }
  if (!validQuestionResponse([{latexProblem:p.statement,options:p.choices.map(c=>c.math),correctIndex:p.choices.findIndex(c=>c.choiceId===p.answerChoiceId),explanation:p.solutionSteps,topic:p.topic,difficulty:p.difficulty}],{category:p.topic,difficulty:p.difficulty,count:1}))throw Error('Gameplay payload bounds rejected');
  if (!questionMathIsRenderable({latexProblem:p.statement,options:p.choices.map(c=>c.math),explanation:p.solutionSteps})) throw Error('KaTeX rejected mathematical content');
  return p;
}
export function openDatabase(path) {
  const db=new DatabaseSync(path);db.exec('PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;');
  if (!db.prepare("SELECT name FROM sqlite_master WHERE name='bank_problems'").get()) db.exec(readFileSync(resolve(root,'drizzle/0001_problem_bank.sql'),'utf8'));
  return db;
}
export function insertProblem(db,p) {
  validateRecord(p);
  const existing=db.prepare('SELECT content_hash FROM bank_problems WHERE problem_id=? AND revision=?').get(p.problemId,p.problemRevision);
  if(existing) { if(existing.content_hash!==p.contentHash) throw Error('Immutable revision conflict'); return false; }
  const duplicate=db.prepare('SELECT problem_id FROM bank_problems WHERE semantic_hash=? AND problem_id!=?').get(p.semanticHash,p.problemId);
  if(duplicate) throw Error('Duplicate normalized mathematical problem');
  const last=db.prepare('SELECT MAX(revision) AS revision FROM bank_problems WHERE problem_id=?').get(p.problemId).revision;
  if(p.problemRevision!==(last||0)+1) throw Error('Revisions must be consecutive');
  db.prepare('INSERT INTO bank_problems VALUES (?,?,?,?,?,?,?,?)').run(p.problemId,p.problemRevision,p.contentHash,p.semanticHash,p.topic,p.difficulty,p.familyId,canonical(p));
  db.prepare("INSERT INTO bank_publication VALUES (?,?,'approved',NULL)").run(p.problemId,p.problemRevision);
  return true;
}
export async function importRelease(db,manifestPath) {
  const manifest=JSON.parse(readFileSync(manifestPath,'utf8'));
  if (manifest.schemaVersion!==1 || !manifest.releaseId || manifest.approvedCount<1) throw Error('Invalid manifest');
  const artifact=resolve(dirname(manifestPath),manifest.artifact);
  // Verify the complete artifact before any mutation; a truncated file never publishes.
  const digest=createHash('sha256');for await (const chunk of createReadStream(artifact)) digest.update(chunk);
  if(digest.digest('hex')!==manifest.artifactSha256) throw Error('Artifact hash mismatch');
  const verification=spawnSync(process.env.BANK_PYTHON || (existsSync(resolve(root,'.bank-venv/bin/python')) ? resolve(root,'.bank-venv/bin/python') : 'python3'),[resolve(root,'scripts/bank/pipeline.py'),'--verify',artifact],{encoding:'utf8',maxBuffer:1024*1024});
  if(verification.status!==0)throw Error('Independent mathematical verification failed; quarantine this artifact. '+(verification.stderr||verification.error?.message||''));
  const old=db.prepare('SELECT manifest_json FROM bank_releases WHERE release_id=?').get(manifest.releaseId);
  if(old && canonical(releaseContract(JSON.parse(old.manifest_json)))!==canonical(releaseContract(manifest))) throw Error('Release manifest is immutable');
  if(!old) db.prepare('INSERT INTO bank_releases VALUES (?,?,?,?)').run(manifest.releaseId,canonical(releaseContract(manifest)),manifest.approvedCount,'staging');
  const slotCounts=new Map(),seen=new Set(),coverage={},families={};let imported=0,duplicates=0;
  for await(const line of createInterface({input:createReadStream(artifact),crlfDelay:Infinity})) {
    if(!line) continue;const p=JSON.parse(line);
    if(seen.has(p.problemId)) throw Error('Duplicate identity inside release');seen.add(p.problemId);
    db.exec('BEGIN IMMEDIATE');
    try {
      insertProblem(db,p)? imported++:duplicates++;
      if(db.prepare('SELECT state FROM bank_publication WHERE problem_id=? AND revision=?').get(p.problemId,p.problemRevision)?.state!=='approved') throw Error('Release contains a retired revision');
      for(const tag of ['*',...new Set(p.techniqueTags)]) {
        const key=JSON.stringify([p.topic,p.difficulty,tag,p.familyId]),slot=slotCounts.get(key)||0;
        const args=[manifest.releaseId,p.topic,p.difficulty,tag,p.familyId,slot,p.problemId,p.problemRevision];
        const existing=db.prepare('SELECT problem_id,revision FROM bank_slots WHERE release_id=? AND topic=? AND difficulty=? AND tag=? AND family_id=? AND slot=?').get(...args.slice(0,6));
        if(existing && (existing.problem_id!==p.problemId||existing.revision!==p.problemRevision)) throw Error('Release slot conflict');
        if(!existing)db.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run(...args);
        slotCounts.set(key,slot+1);
      }
      db.exec('COMMIT');
    } catch(error) {db.exec('ROLLBACK');throw error;}
    const key=p.topic+'/'+p.difficulty;coverage[key]=(coverage[key]||0)+1;families[p.familyId]=(families[p.familyId]||0)+1;
  }
  if(seen.size!==manifest.approvedCount || canonical(coverage)!==canonical(manifest.coverage)||canonical(families)!==canonical(manifest.families)) throw Error('Coverage/count gate failed');
  if(Object.keys(coverage).length!==24||Object.keys(families).length<72||Math.max(...Object.values(families))/seen.size>0.02) throw Error('Diversity gate failed');
  db.exec('BEGIN IMMEDIATE');
  try {
    for(const [key,count] of slotCounts)db.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?) ON CONFLICT DO NOTHING').run(manifest.releaseId,...JSON.parse(key),count);
    db.prepare("UPDATE bank_releases SET state='published' WHERE release_id=?").run(manifest.releaseId);
    db.exec('COMMIT');
  } catch(error) {db.exec('ROLLBACK');throw error;}
  return {releaseId:manifest.releaseId,imported,duplicateSafeExisting:duplicates,approved:seen.size,published:seen.size,renderValidated:seen.size};
}
function quote(value){return value===null?'NULL':typeof value==='number'?String(value):"'"+String(value).replaceAll("'","''")+"'";}
async function main(){
  const [command,path,...args]=process.argv.slice(2);if(!command||!path)throw Error('Usage: admin.mjs import|activate|inspect|retire|export|reports DATABASE [arguments]');
  const db=openDatabase(path);
  try {
    if(command==='import') console.log(JSON.stringify(await importRelease(db,resolve(args[0])),null,2));
    else if(command==='activate') {
      const r=db.prepare("SELECT expected_count FROM bank_releases WHERE release_id=? AND state='published'").get(args[0]);if(!r)throw Error('Release is not published');
      const count=db.prepare("SELECT count(*) AS n FROM bank_slots s JOIN bank_publication p USING(problem_id,revision) WHERE s.release_id=? AND s.tag='*' AND p.state='approved'").get(args[0]).n;
      if(count!==r.expected_count)throw Error('Published count differs: rebuild release after retirements');
      db.prepare("INSERT INTO bank_config VALUES ('active_release',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").run(args[0]);console.log(JSON.stringify({activeRelease:args[0],publishedCount:count}));
    } else if(command==='revise') {
      const [recordPath,reason]=args;if(!reason?.trim())throw Error('Correction reason required');
      const input=resolve(recordPath),verified=spawnSync(process.env.BANK_PYTHON || (existsSync(resolve(root,'.bank-venv/bin/python')) ? resolve(root,'.bank-venv/bin/python') : 'python3'),[resolve(root,'scripts/bank/pipeline.py'),'--verify',input],{encoding:'utf8'});
      if(verified.status!==0)throw Error('Correction failed independent verification');
      const records=readFileSync(input,'utf8').trim().split('\n').map(JSON.parse);if(records.length!==1||records[0].problemRevision<2)throw Error('Supply exactly one corrected revision');
      const p=records[0];db.exec('BEGIN IMMEDIATE');try {insertProblem(db,p);db.prepare("UPDATE bank_publication SET state='retired',retirement_reason=? WHERE problem_id=? AND revision<?").run(reason,p.problemId,p.problemRevision);db.exec('COMMIT');}catch(e){db.exec('ROLLBACK');throw e;}
      console.log(JSON.stringify({problemId:p.problemId,revision:p.problemRevision,state:'approved, awaiting membership in a new release'}));
    } else if(command==='inspect') {
      const [topic='all',difficulty='all',id='all']=args;
      console.log(JSON.stringify(db.prepare("SELECT b.*,p.state,p.retirement_reason FROM bank_problems b JOIN bank_publication p USING(problem_id,revision) WHERE (?='all' OR topic=?) AND (?='all' OR difficulty=?) AND (?='all' OR problem_id=?) ORDER BY problem_id,revision LIMIT 50").all(topic,topic,difficulty,difficulty,id,id).map(r=>({...r,payload_json:JSON.parse(r.payload_json)})),null,2));
    } else if(command==='retire') {
      const [id,revision,reason]=args;if(!reason?.trim())throw Error('Retirement reason required');
      const result=db.prepare("UPDATE bank_publication SET state='retired',retirement_reason=? WHERE problem_id=? AND revision=?").run(reason,id,Number(revision));if(!result.changes)throw Error('Revision not found');console.log('Retired from new selection; historical content retained.');
    } else if(command==='reports') console.log(JSON.stringify(db.prepare("SELECT * FROM bank_reports WHERE status='open' ORDER BY created_at LIMIT 100").all(),null,2));
    else if(command==='export') {
      // Original-layout export. Hosted execution requires the Sites-supported operator path.
      // Keep artifacts outside Git and public assets: they contain answer keys.
      const dir=resolve(args[0]);mkdirSync(dir,{recursive:true});let chunks=0,lines=[],bytes=0;
      const flush=()=>{if(lines.length){writeFileSync(resolve(dir,`bank-${String(chunks++).padStart(5,'0')}.sql`),lines.join('\n')+'\n');lines=[];bytes=0;}};
      for(const table of ['bank_releases','bank_problems','bank_publication','bank_slots','bank_pools','bank_legacy_ids']) {
        for(const row of db.prepare(`SELECT * FROM ${table}`).iterate()) {
          // Publication is deferred until the separately generated activation file.
          if(table==='bank_releases')row.state='staging';
          const identity=table==='bank_problems'?['problem_id','revision']:table==='bank_slots'?['release_id','topic','difficulty','tag','family_id','slot']:table==='bank_releases'?['release_id']:table==='bank_pools'?['release_id','topic','difficulty','tag','family_id']:null;
          if(identity){
            const compare=table==='bank_problems'?['content_hash','semantic_hash']:table==='bank_slots'?['problem_id','revision']:table==='bank_releases'?['manifest_json','expected_count']:['item_count'];
            const guard=`INSERT INTO bank_import_checks(ok) SELECT 0 WHERE EXISTS(SELECT 1 FROM ${table} WHERE ${identity.map(k=>k+'='+quote(row[k])).join(' AND ')} AND (${compare.map(k=>k+'!='+quote(row[k])).join(' OR ')}));`;
            lines.push(guard);bytes+=Buffer.byteLength(guard);
          }
          // Exported retirements propagate; importing an older approval never revives a retired row.
          const conflict=table==='bank_publication' && row.state==='retired'
            ? 'ON CONFLICT(problem_id,revision) DO UPDATE SET state=excluded.state,retirement_reason=excluded.retirement_reason'
            : 'ON CONFLICT DO NOTHING';
          const line=`INSERT INTO ${table} (${Object.keys(row).join(',')}) VALUES (${Object.values(row).map(quote).join(',')}) ${conflict};`;
          if(bytes+Buffer.byteLength(line)>2_000_000)flush();lines.push(line);bytes+=Buffer.byteLength(line);
        }
      }flush();
      const release=db.prepare("SELECT value FROM bank_config WHERE key='active_release'").get()?.value;if(!release)throw Error('Activate the verified release locally first');
      // Count guard prevents activation after partial/failed uploads.
      const countGuard=`SELECT 1 FROM bank_releases WHERE release_id=${quote(release)} AND expected_count=(SELECT count(*) FROM bank_slots s JOIN bank_publication p USING(problem_id,revision) WHERE s.release_id=${quote(release)} AND s.tag='*' AND p.state='approved')`;
      const sql=`INSERT INTO bank_import_checks(ok) SELECT 0 WHERE NOT EXISTS(${countGuard});\nUPDATE bank_releases SET state='published' WHERE release_id=${quote(release)};\nINSERT INTO bank_config SELECT 'active_release',release_id FROM bank_releases WHERE release_id=${quote(release)} AND state='published' ON CONFLICT(key) DO UPDATE SET value=excluded.value;\n`;
      writeFileSync(resolve(dir,'activate-after-verification.sql'),sql);console.log(JSON.stringify({chunks,activation:'activate-after-verification.sql'}));
    } else throw Error('Unknown command');
  }finally{db.close();}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(e=>{console.error(e.message);process.exitCode=1;});
