#!/usr/bin/env node
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {canonical} from '../admin.mjs';
const [evaluatedPath,finalPath,baselinePath,output]=process.argv.slice(2);
if(!output||existsSync(output))throw Error('Use a new binding report');
const sha=b=>createHash('sha256').update(b).digest('hex');
const evaluated=new DatabaseSync(evaluatedPath,{readOnly:true}),final=new DatabaseSync(finalPath,{readOnly:true}),baseline=new DatabaseSync(baselinePath,{readOnly:true});
const tables={cbank_shared:['shared_id'],cbank_problems:['problem_ref'],cbank_publication:['problem_ref'],cbank_selection_features:['problem_ref'],cbank_pools:['pool_id'],cbank_slots:['pool_id','slot'],cbank_release_sources:['release_id','source_release_id'],cbank_release_exclusions:['release_id','problem_ref'],cbank_withdrawn_families:['source_release_id','family_id','introduced_by'],cbank_problem_lineage:['problem_id'],cbank_family_lineage:['family_id'],cbank_config:['key']};
const encode=row=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k,v instanceof Uint8Array?Buffer.from(v).toString('hex'):v]));
function fingerprint(db,table,keys,where='1',args=[]){const h=createHash('sha256');let rows=0;for(const row of db.prepare(`SELECT * FROM ${table} WHERE ${where} ORDER BY ${keys.join(',')}`).iterate(...args)){h.update(canonical(encode(row))+'\n');rows++;}return {rows,sha256:h.digest('hex')};}
const report={evaluatedDatabaseSha256:sha(readFileSync(evaluatedPath)),finalDatabaseSha256:sha(readFileSync(finalPath)),baselineDatabaseSha256:sha(readFileSync(baselinePath)),matchingTables:{},historicalPreservation:{}};
try{
 for(const [table,keys]of Object.entries(tables)){const a=fingerprint(evaluated,table,keys),b=fingerprint(final,table,keys);assert.deepEqual(b,a,table+' changed after horizon evaluation');report.matchingTables[table]=a;}
 for(const row of evaluated.prepare('SELECT * FROM cbank_releases ORDER BY release_id').all()){
  const other=final.prepare('SELECT * FROM cbank_releases WHERE release_id=?').get(row.release_id);assert.ok(other);assert.equal(row.state,other.state);assert.equal(row.expected_count,other.expected_count);
  if(row.manifest_json!==other.manifest_json){const full=JSON.parse(row.manifest_json),reference=JSON.parse(other.manifest_json);assert.equal(reference.format,'content-release-manifest-reference-v1');assert.equal(reference.fullManifestSha256,sha(canonical(full)));assert.equal(reference.artifactSha256,full.artifactSha256);report.compactManifestBinding={release:row.release_id,fullManifestSha256:reference.fullManifestSha256};}
 }
 for(const [table,key]of Object.entries({cbank_shared:'shared_id',cbank_problems:'problem_ref',cbank_publication:'problem_ref',cbank_selection_features:'problem_ref',cbank_pools:'pool_id',cbank_slots:'pool_id'})){
  const max=baseline.prepare(`SELECT max(${key}) n FROM ${table}`).get().n,a=fingerprint(baseline,table,tables[table]),b=fingerprint(final,table,tables[table],key+'<=?',[max]);assert.deepEqual(b,a,'Historical bytes changed: '+table);report.historicalPreservation[table]=a;
 }
 for(const row of baseline.prepare('SELECT * FROM cbank_releases ORDER BY release_id').all())assert.deepEqual(final.prepare('SELECT * FROM cbank_releases WHERE release_id=?').get(row.release_id),row,'Historical release manifest changed');
 report.passed=true;report.scope='Every selector-relevant logical row is identical to the evaluated local catalog. The new oversized audit manifest is replaced only by its verified compact reference. Every original canonical payload, publication row, feature, pool, slot and release manifest is byte-identical.';
}catch(error){report.passed=false;report.error=error.stack;process.exitCode=1;}finally{evaluated.close();final.close();baseline.close();}
writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
