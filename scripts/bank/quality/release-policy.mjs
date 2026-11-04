// Offline release preparation. All policy rows are immutable, verified imports.
import {canonical} from '../admin.mjs';
import {LEGACY_FAMILIES} from '../../../lib/bank/legacy-origin.mjs';
import legacyEligibility from '../../../lib/server/legacy-eligibility.json' with {type:'json'};
export const MAX_RELEASE_SOURCES=64;

export function flattenSources(db,parent){
 const seen=new Set(),visiting=new Set();
 const visit=id=>{
  if(visiting.has(id))throw Error('Release inheritance cycle');
  if(seen.has(id))return;
  if(seen.size+visiting.size>=MAX_RELEASE_SOURCES)throw Error('Release source bound exceeded');
  const row=db.prepare('SELECT state FROM cbank_releases WHERE release_id=?').get(id);
  if(!row||row.state!=='published')throw Error('Unpublished or missing inherited release: '+id);
  visiting.add(id);
  for(const child of db.prepare('SELECT source_release_id FROM cbank_release_sources WHERE release_id=? ORDER BY source_release_id').all(id))visit(child.source_release_id);
  visiting.delete(id);seen.add(id);
 };
 visit(parent);return [...seen].sort();
}

function immutableInsert(db,table,row,keys){
 const existing=db.prepare(`SELECT * FROM ${table} WHERE ${keys.map(k=>k+'=?').join(' AND ')}`).get(...keys.map(k=>row[k]));
 if(existing){if(canonical(existing)!==canonical(row))throw Error('Immutable policy conflict: '+table);return;}
 db.prepare(`INSERT INTO ${table} (${Object.keys(row).join(',')}) VALUES (${Object.keys(row).map(()=>'?').join(',')})`).run(...Object.values(row));
}

function applyPolicy(db,manifest,newRecords){
 const release=manifest.releaseId,sources=flattenSources(db,manifest.parentRelease);
 if(sources.includes(release))throw Error('A release cannot inherit itself');
 for(const source of sources)immutableInsert(db,'cbank_release_sources',{release_id:release,source_release_id:source},['release_id','source_release_id']);
 // Carry only the parent's effective scoped exclusions. Its ancestor exclusions
 // have already been flattened. Also include older non-flat ancestor releases.
 const exclusions=new Map();
 for(const source of sources)for(const row of db.prepare('SELECT * FROM cbank_release_exclusions WHERE release_id=?').all(source))
  if(exclusions.get(row.problem_ref)?.scope!=='global')exclusions.set(row.problem_ref,{...row,release_id:release});
 const resolveRef=(id,revision)=>{const row=db.prepare('SELECT problem_ref FROM cbank_problems WHERE problem_id=? AND revision=?').get(id,revision);if(!row)throw Error('Unknown excluded revision');return row.problem_ref;};
 for(const p of newRecords){
  for(const row of db.prepare('SELECT problem_ref FROM cbank_problems WHERE problem_id=? AND revision<?').all(p.problemId,p.problemRevision))
   if(exclusions.get(row.problem_ref)?.scope!=='global')exclusions.set(row.problem_ref,{release_id:release,problem_ref:row.problem_ref,scope:'release',reason:'Superseded by reviewed revision '+p.problemRevision});
 }
 for(const item of manifest.exclusions||[]){
  if(!['release','global'].includes(item.scope)||!item.reason?.trim())throw Error('Explicit exclusion scope and reason required');
  const ref=resolveRef(item.problemId,item.revision),prior=exclusions.get(ref);
  // A globally withdrawn incorrect item must never be downgraded by a child.
  exclusions.set(ref,{release_id:release,problem_ref:ref,scope:prior?.scope==='global'?'global':item.scope,reason:item.reason});
 }
 for(const row of exclusions.values())immutableInsert(db,'cbank_release_exclusions',row,['release_id','problem_ref']);
 for(const item of manifest.withdrawals||[]){
  if(!sources.includes(item.sourceReleaseId)||!item.reason?.trim()||!db.prepare('SELECT 1 FROM cbank_pools WHERE release_id=? AND family_id=?').get(item.sourceReleaseId,item.familyId))throw Error('Unknown or unreasoned family withdrawal');
  immutableInsert(db,'cbank_withdrawn_families',{source_release_id:item.sourceReleaseId,family_id:item.familyId,introduced_by:release,reason:item.reason},['source_release_id','family_id','introduced_by']);
 }
 for(const item of manifest.lineage||[]){
  if(!db.prepare('SELECT 1 FROM cbank_problems WHERE problem_id=?').get(item.problemId)||!db.prepare('SELECT 1 FROM cbank_problems WHERE problem_id=?').get(item.lineageId))throw Error('Lineage needs existing mathematical identities');
  const canonicalId=db.prepare('SELECT lineage_id FROM cbank_problem_lineage WHERE problem_id=?').get(item.lineageId)?.lineage_id||item.lineageId;
  if(canonicalId!==item.lineageId)throw Error('Lineage mappings must be flattened');
  immutableInsert(db,'cbank_problem_lineage',{problem_id:item.problemId,lineage_id:item.lineageId},['problem_id']);
 }
 for(const item of manifest.familyLineage||[]){
  if(!item.familyId||!item.constructionId)throw Error('Invalid construction lineage');
  const target=db.prepare('SELECT construction_id FROM cbank_family_lineage WHERE family_id=?').get(item.constructionId);
  if(target&&target.construction_id!==item.constructionId)throw Error('Construction lineage must be flattened');
  immutableInsert(db,'cbank_family_lineage',{family_id:item.familyId,construction_id:item.constructionId},['family_id']);
 }
 return {sources,exclusions:exclusions.size,withdrawals:(manifest.withdrawals||[]).length};
}

// A rejected policy must leave no partial membership, exclusion, or alias rows.
export function applyReleasePolicy(db,manifest,newRecords){
 for(const [field,limit] of [['exclusions',20000],['withdrawals',1024],['lineage',20000],['familyLineage',1024]]){
  if(manifest[field]!==undefined&&(!Array.isArray(manifest[field])||manifest[field].length>limit))throw Error('Release policy bound exceeded: '+field);
 }
 const plannedFamilies=new Map((manifest.familyLineage||[]).map(r=>[r.familyId,r.constructionId]));
 const originFor=family=>plannedFamilies.get(family)||db.prepare('SELECT construction_id FROM cbank_family_lineage WHERE family_id=?').get(family)?.construction_id;
 for(const item of manifest.familyLineage||[])if(LEGACY_FAMILIES.includes(item.familyId)&&item.constructionId!==item.familyId)throw Error('Legacy origin cannot be relabeled');
 for(const p of newRecords){
  const approval=legacyEligibility.records.find(r=>r.problemId===p.problemId&&r.revision===p.problemRevision);
  const origin=LEGACY_FAMILIES.find(f=>f===p.familyId||f===p.pedagogy?.constructionId)||approval?.constructionId;
  if(origin&&p.familyId!==origin&&originFor(p.familyId)!==origin)throw Error('Legacy descendant requires its canonical origin alias');
 }
 for(const [field,source,target,table,key,value] of [
  ['lineage','problemId','lineageId','cbank_problem_lineage','problem_id','lineage_id'],
  ['familyLineage','familyId','constructionId','cbank_family_lineage','family_id','construction_id']]){
  const planned=new Map();
  for(const item of manifest[field]||[]){
   if(planned.has(item[source])&&planned.get(item[source])!==item[target])throw Error('Conflicting lineage declaration');
   planned.set(item[source],item[target]);
  }
  for(const targetId of planned.values()){
   const canonical=planned.get(targetId)||db.prepare(`SELECT ${value} FROM ${table} WHERE ${key}=?`).get(targetId)?.[value]||targetId;
   if(canonical!==targetId)throw Error('Lineage mappings must be flattened; no chains or cycles');
  }
 }
 db.exec('SAVEPOINT quality_policy');
 try{const result=applyPolicy(db,manifest,newRecords);db.exec('RELEASE quality_policy');return result;}
 catch(error){db.exec('ROLLBACK TO quality_policy; RELEASE quality_policy');throw error;}
}
