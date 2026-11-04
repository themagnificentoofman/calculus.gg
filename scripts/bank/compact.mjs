#!/usr/bin/env node
// Private serving conversion. Input is the already verified authoring database, never regenerated math.
import { DatabaseSync } from 'node:sqlite';
import { createHash } from 'node:crypto';
import { gzipSync,gunzipSync } from 'node:zlib';
import { readFileSync,writeFileSync,existsSync,statSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonical,reconstruct } from '../../lib/bank/compact-codec.mjs';
const root = fileURLToPath(new URL('../../',import.meta.url));
const digest = text => createHash('sha256').update(text).digest();
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const metadataKeys = ['schemaVersion','topic','difficulty','subtopic','techniqueTags','familyId','templateVersion','provenance','validation','estimates','assumptions'];
function intersection(a,b) {
  const out = {};
  for (const [k,v] of Object.entries(a)) {
    if (!Object.hasOwn(b,k)) continue;
    if (canonical(v) === canonical(b[k])) out[k] = v;
    else if (plain(v) && plain(b[k])) { const sub = intersection(v,b[k]); if (Object.keys(sub).length) out[k] = sub; }
  }
  return out;
}
function difference(p,shared) {
  const out = {};
  for (const [k,v] of Object.entries(p)) {
    if (!Object.hasOwn(shared,k)) out[k] = v;
    else if (canonical(v) !== canonical(shared[k])) {
      if (!plain(v) || !plain(shared[k])) throw Error('Metadata factoring conflict');
      out[k] = difference(v,shared[k]);
    }
  }
  return out;
}
export function openCompact(path) {
  const db = new DatabaseSync(path); db.exec('PRAGMA foreign_keys=ON;');
  if (!db.prepare("SELECT name FROM sqlite_schema WHERE name='bank_reports'").get()) db.exec(readFileSync(resolve(root,'drizzle/0001_problem_bank.sql'),'utf8'));
  if (!db.prepare("SELECT name FROM sqlite_schema WHERE name='cbank_problems'").get()) db.exec(readFileSync(resolve(root,'drizzle/0002_compact_bank.sql'),'utf8'));
  if (!db.prepare("SELECT name FROM sqlite_schema WHERE name='cbank_selection_features'").get()) db.exec(readFileSync(resolve(root,'drizzle/0004_flimsy_carlie_cooper.sql'),'utf8'));
  if (!db.prepare('PRAGMA table_info(cbank_delta_ledger)').all().some(c=>c.name==='charged_reads')) db.exec(readFileSync(resolve(root,'drizzle/0005_brief_skaar.sql'),'utf8'));
  if (!db.prepare("SELECT name FROM sqlite_schema WHERE name='cbank_release_exclusions'").get()) db.exec(readFileSync(resolve(root,'drizzle/0006_quality_membership.sql'),'utf8'));
  if (!db.prepare("SELECT name FROM sqlite_schema WHERE name='cbank_exclusion_lookup'").get()) db.exec(readFileSync(resolve(root,'drizzle/0007_quality_lookup.sql'),'utf8'));
  return db;
}
export function verifyCompact(db,source) {
  const count = db.prepare('SELECT count(*) AS n FROM cbank_problems').get().n;
  const sourceCount = source?.prepare('SELECT count(*) AS n FROM bank_problems').get().n;
  if (source && count !== sourceCount) throw Error('Reconstruction count mismatch');
  let verified = 0,canonicalBytes = 0; const coverage = {},families = {},publication = {};
  const original = source?.prepare('SELECT payload_json FROM bank_problems WHERE problem_id=? AND revision=?');
  const originalState = source?.prepare('SELECT state,retirement_reason FROM bank_publication WHERE problem_id=? AND revision=?');
  const identityDigest = createHash('sha256'),publicationDigest=createHash('sha256'),membershipDigest=createHash('sha256');
  for (const row of db.prepare(`SELECT b.*,s.metadata_json,p.state,p.retirement_reason FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication p USING(problem_ref) ORDER BY b.problem_id,b.revision`).iterate()) {
    const p = reconstruct(row,JSON.parse(gunzipSync(row.payload_gzip,{maxOutputLength:65536}).toString('utf8')));
    const {contentHash,...body} = p, text = canonical(p);
    if (digest(canonical(body)).toString('hex') !== contentHash) throw Error('Reconstruction hash mismatch');
    if (original && text !== original.get(p.problemId,p.problemRevision)?.payload_json) throw Error('Canonical source mismatch');
    if (originalState && canonical(originalState.get(p.problemId,p.problemRevision)) !== canonical({state:row.state,retirement_reason:row.retirement_reason})) throw Error('Publication source mismatch');
    identityDigest.update(`${p.problemId}@${p.problemRevision}:${p.contentHash}\n`);
    publicationDigest.update(canonical([p.problemId,p.problemRevision,row.state,row.retirement_reason])+'\n');
    canonicalBytes += Buffer.byteLength(text); verified++;
    const key = p.topic+'/'+p.difficulty; coverage[key] = (coverage[key]||0)+1; families[p.familyId] = (families[p.familyId]||0)+1; publication[row.state] = (publication[row.state]||0)+1;
  }
  if (verified !== count) throw Error('Missing shared/publication data');
  const integrity = db.prepare('PRAGMA integrity_check').all();
  if (integrity.length !== 1 || integrity[0].integrity_check !== 'ok' || db.prepare('PRAGMA foreign_key_check').all().length) throw Error('SQLite integrity failure');
  for (const pool of db.prepare('SELECT * FROM cbank_pools').iterate()) {
    const r = db.prepare('SELECT count(*) AS n,min(slot) AS first,max(slot) AS last FROM cbank_slots WHERE pool_id=?').get(pool.pool_id);
    if (r.n !== pool.item_count || r.first !== 0 || r.last !== r.n-1) throw Error('Non-contiguous pool');
    if (source) {
      const rows = source.prepare('SELECT problem_id,revision FROM bank_slots WHERE release_id=? AND topic=? AND difficulty=? AND tag=? AND family_id=? ORDER BY slot').all(pool.release_id,pool.topic,pool.difficulty,pool.tag,pool.family_id);
      const actual = db.prepare('SELECT problem_id,revision FROM cbank_slots JOIN cbank_problems USING(problem_ref) WHERE pool_id=? ORDER BY slot').all(pool.pool_id);
      if (canonical(rows)!==canonical(actual)) throw Error('Release membership source mismatch');
    }
  }
  for (const row of db.prepare('SELECT pool_id,slot,problem_ref FROM cbank_slots ORDER BY pool_id,slot').iterate()) membershipDigest.update(canonical(row)+'\n');
  const pools=db.prepare('SELECT * FROM cbank_pools ORDER BY pool_id').all();
  return {verified,canonicalBytes,identitySha256:identityDigest.digest('hex'),publicationSha256:publicationDigest.digest('hex'),membershipSha256:membershipDigest.digest('hex'),poolsSha256:digest(canonical(pools)).toString('hex'),memberships:db.prepare('SELECT count(*) AS n FROM cbank_slots').get().n,coverage,families,publication,integrity:'ok',foreignKeyViolations:0};
}
export function syncCompact(source,target,release,{measureCompression=false}={}) {
  const manifest = source.prepare("SELECT * FROM bank_releases WHERE release_id=? AND state='published'").get(release);
  if (!manifest) throw Error('Source release is not verified/published');
  const shared = new Map(),familyCounts = new Map();
  for (const row of source.prepare('SELECT family_id,payload_json FROM bank_problems ORDER BY rowid').iterate()) {
    const p = JSON.parse(row.payload_json), meta = Object.fromEntries(metadataKeys.map(k=>[k,p[k]]));
    shared.set(row.family_id,shared.has(row.family_id)?intersection(shared.get(row.family_id),meta):meta);
    familyCounts.set(row.family_id,(familyCounts.get(row.family_id)||0)+1);
  }
  const measures = {canonicalPayloadBytes:0,wholeRecordGzipBytes:0,residualJsonBytes:0,residualGzipBytes:0,sharedJsonBytes:0,repeatedSharedJsonBytes:0,provenanceJsonBytes:0,validationJsonBytes:0,maxCanonicalBytes:0,maxResidualBytes:0};
  const sharedIds = new Map(); target.exec('BEGIN IMMEDIATE');
  try {
    for (const [family,meta] of shared) {
      const json = canonical(meta), hash = digest(json);
      target.prepare('INSERT INTO cbank_shared(content_hash,metadata_json) VALUES (?,?) ON CONFLICT(content_hash) DO NOTHING').run(hash,json);
      const row = target.prepare('SELECT shared_id,metadata_json FROM cbank_shared WHERE content_hash=?').get(hash);
      if (row.metadata_json!==json) throw Error('Shared metadata conflict'); sharedIds.set(family,row.shared_id);
      measures.sharedJsonBytes += Buffer.byteLength(json); measures.repeatedSharedJsonBytes += Buffer.byteLength(json)*familyCounts.get(family);
    }
    for (const row of source.prepare('SELECT b.*,p.state,p.retirement_reason FROM bank_problems b JOIN bank_publication p USING(problem_id,revision) ORDER BY b.rowid').iterate()) {
      const p = JSON.parse(row.payload_json), {contentHash,problemId,problemRevision,semanticHash,...body} = p;
      if (canonical(p)!==row.payload_json || digest(canonical({problemId,problemRevision,semanticHash,...body})).toString('hex')!==contentHash || contentHash!==row.content_hash || semanticHash!==row.semantic_hash) throw Error('Invalid verified source hash');
      const old = target.prepare('SELECT problem_ref,content_hash FROM cbank_problems WHERE problem_id=? AND revision=?').get(problemId,problemRevision);
      let ref = old?.problem_ref;
      if (old) { if (Buffer.from(old.content_hash).toString('hex')!==contentHash) throw Error('Immutable revision conflict'); }
      else {
        const last = target.prepare('SELECT MAX(revision) AS n FROM cbank_problems WHERE problem_id=?').get(problemId).n;
        if (problemRevision!==(last||0)+1) throw Error('Revisions must be consecutive');
        if (target.prepare('SELECT 1 FROM cbank_problems WHERE semantic_hash=? AND problem_id!=?').get(Buffer.from(semanticHash,'hex'),problemId)) throw Error('Duplicate normalized mathematical problem');
        const residual = canonical(difference(body,shared.get(p.familyId))), compressed = gzipSync(residual,{level:9});
        if (Buffer.byteLength(row.payload_json)>65536 || Buffer.byteLength(residual)>65536 || compressed.length>65536) throw Error('Payload exceeds serving bounds');
        const result = target.prepare('INSERT INTO cbank_problems(problem_id,revision,content_hash,semantic_hash,shared_id,payload_gzip) VALUES (?,?,?,?,?,?)').run(problemId,problemRevision,Buffer.from(contentHash,'hex'),Buffer.from(semanticHash,'hex'),sharedIds.get(p.familyId),compressed);
        ref = Number(result.lastInsertRowid);
        measures.residualJsonBytes += Buffer.byteLength(residual); measures.residualGzipBytes += compressed.length;
        measures.maxResidualBytes = Math.max(measures.maxResidualBytes,Buffer.byteLength(residual));
      }
      target.prepare('INSERT INTO cbank_publication VALUES (?,?,?) ON CONFLICT DO NOTHING').run(ref,row.state,row.retirement_reason);
      if(p.schemaVersion===2){
        const m=p.pedagogy,values=[ref,m.relatedIdeaGroupId,m.structuralSignature,m.primaryTechnique,[...m.reasoningDemand].sort().join('+')+':'+m.primaryTechnique,1];
        const old=target.prepare('SELECT * FROM cbank_selection_features WHERE problem_ref=?').get(ref);
        if(old&&canonical(Object.values(old))!==canonical(values))throw Error('Immutable selection feature conflict');
        if(!old)target.prepare('INSERT INTO cbank_selection_features VALUES (?,?,?,?,?,?)').run(...values);
      }
      if (row.state==='retired') target.prepare("UPDATE cbank_publication SET state='retired',retirement_reason=? WHERE problem_ref=? AND (state!='retired' OR retirement_reason IS NOT ?)").run(row.retirement_reason,ref,row.retirement_reason);
      measures.canonicalPayloadBytes += Buffer.byteLength(row.payload_json);
      measures.provenanceJsonBytes += Buffer.byteLength(canonical(p.provenance)); measures.validationJsonBytes += Buffer.byteLength(canonical(p.validation));
      measures.maxCanonicalBytes = Math.max(measures.maxCanonicalBytes,Buffer.byteLength(row.payload_json));
      if (measureCompression) measures.wholeRecordGzipBytes += gzipSync(row.payload_json,{level:9}).length;
    }
    const oldRelease = target.prepare('SELECT manifest_json,expected_count FROM cbank_releases WHERE release_id=?').get(release);
    if (oldRelease && (oldRelease.manifest_json!==manifest.manifest_json || oldRelease.expected_count!==manifest.expected_count)) throw Error('Immutable release conflict');
    target.prepare("INSERT INTO cbank_releases VALUES (?,?,?,'staging') ON CONFLICT DO NOTHING").run(release,manifest.manifest_json,manifest.expected_count);
    for (const pool of source.prepare('SELECT * FROM bank_pools WHERE release_id=? ORDER BY topic,difficulty,tag,family_id').iterate(release)) {
      const keys = [release,pool.topic,pool.difficulty,pool.tag,pool.family_id];
      target.prepare('INSERT INTO cbank_pools(release_id,topic,difficulty,tag,family_id,item_count) VALUES (?,?,?,?,?,?) ON CONFLICT DO NOTHING').run(...keys,pool.item_count);
      const item = target.prepare('SELECT pool_id,item_count FROM cbank_pools WHERE release_id=? AND topic=? AND difficulty=? AND tag=? AND family_id=?').get(...keys);
      if (item.item_count!==pool.item_count) throw Error('Immutable pool conflict');
      for (const slot of source.prepare('SELECT slot,problem_id,revision FROM bank_slots WHERE release_id=? AND topic=? AND difficulty=? AND tag=? AND family_id=? ORDER BY slot').iterate(...keys)) {
        const ref = target.prepare('SELECT problem_ref FROM cbank_problems WHERE problem_id=? AND revision=?').get(slot.problem_id,slot.revision).problem_ref;
        const old = target.prepare('SELECT problem_ref FROM cbank_slots WHERE pool_id=? AND slot=?').get(item.pool_id,slot.slot);
        if (old && old.problem_ref!==ref) throw Error('Immutable slot conflict');
        if (!old) target.prepare('INSERT INTO cbank_slots VALUES (?,?,?)').run(item.pool_id,slot.slot,ref);
      }
    }
    for (const row of source.prepare('SELECT * FROM bank_legacy_ids').iterate()) {
      const old=target.prepare('SELECT * FROM bank_legacy_ids WHERE source=? AND legacy_id=?').get(row.source,row.legacy_id);
      if(old && canonical(old)!==canonical(row))throw Error('Immutable legacy identity conflict');
      if(!old)target.prepare('INSERT INTO bank_legacy_ids VALUES (?,?,?,?)').run(row.source,row.legacy_id,row.problem_id,row.revision);
    }
    target.exec('COMMIT');
  } catch(e) { target.exec('ROLLBACK'); throw e; }
  return measures;
}
export function activateCompact(db,release) {
  const row = db.prepare('SELECT expected_count,state FROM cbank_releases WHERE release_id=?').get(release);
  const counts = db.prepare(`SELECT count(*) AS n,count(DISTINCT b.problem_id) AS ids FROM cbank_pools p JOIN cbank_slots s USING(pool_id) JOIN cbank_problems b USING(problem_ref) JOIN cbank_publication u USING(problem_ref) WHERE p.release_id=? AND p.tag='*' AND u.state='approved'`).get(release);
  if (!row || row.state==='retired' || counts.n!==row.expected_count || counts.ids!==counts.n) throw Error('Incomplete or retired release');
  db.exec('BEGIN IMMEDIATE');
  try { db.prepare("UPDATE cbank_releases SET state='published' WHERE release_id=?").run(release); db.prepare("INSERT INTO cbank_config VALUES ('active_release',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").run(release); db.exec('COMMIT'); }
  catch(e) { db.exec('ROLLBACK'); throw e; }
}
async function main() {
  const [command,sourcePath,targetPath,release='cn-2026-11-02-full-v2',reportPath] = process.argv.slice(2);
  if (!['build','sync','verify'].includes(command) || !targetPath) throw Error('Usage: compact.mjs build|sync|verify SOURCE TARGET [RELEASE] [REPORT]');
  if (command==='build' && existsSync(targetPath)) throw Error('Refusing to overwrite an existing serving artifact');
  const source = new DatabaseSync(sourcePath,{readOnly:true}), target = command==='verify'?new DatabaseSync(targetPath,{readOnly:true}):openCompact(targetPath);
  try {
    const measures = command==='verify'?null:syncCompact(source,target,release,{measureCompression:command==='build'});
    const verification = verifyCompact(target,source);
    if (command==='build') activateCompact(target,release); // LOCAL benchmark only; export never includes activation.
    const report = {format:'compact-gzip-shared-v1',release,source:sourcePath,target:targetPath,databaseBytes:statSync(targetPath).size,measures,verification};
    if (reportPath) writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({databaseBytes:report.databaseBytes,measures,verified:verification.verified,integrity:verification.integrity}));
  } finally { source.close(); target.close(); }
}
if (process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) main().catch(e=>{console.error(e);process.exitCode=1;});
