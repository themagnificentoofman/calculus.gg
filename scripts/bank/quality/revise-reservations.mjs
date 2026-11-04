#!/usr/bin/env node
// Rebind only conservative import reservations after a complete local import
// measurement. SQL, decoded content, policy, and prior cumulative charges stay
// identical. No production ledger is reset, reclaimed, or raised.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,existsSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {canonical} from '../admin.mjs';
const [sourceArg,evidenceArg,targetArg]=process.argv.slice(2),source=resolve(sourceArg),target=resolve(targetArg);
if(existsSync(target))throw Error('Use a fresh reservation-plan directory');
const sha=b=>createHash('sha256').update(b).digest('hex'),plan=JSON.parse(readFileSync(join(source,'plan.json'))),evidenceBytes=readFileSync(evidenceArg),evidence=JSON.parse(evidenceBytes);
const {bundleId,status,localDatabaseBytes,compression,...body}=plan;assert.equal(sha(canonical(body)),bundleId);assert.equal(evidence.bundleId,bundleId);
const imported=evidence.operations.filter(o=>o.kind==='import');assert.equal(imported.length,plan.batches.length,'measure every import batch before adjusting reservations');
for(const [i,batch]of body.batches.entries()){
 const bytes=readFileSync(join(source,batch.file));assert.equal(sha(bytes),batch.sha256);assert.equal(bytes.length,batch.bytes);
 const observed=imported.find(o=>o.step===i);assert.ok(observed);const actual=observed.measurements.reduce((n,m)=>n+m.rowsRead,0);
 assert.ok(actual<=batch.rows*10+100,'new conservative bound must cover complete measured operation');
 batch.estimatedReads=batch.rows*10+100;
}
body.reservationEvidence={priorPreparedBundleId:bundleId,completeLocalImportReportSha256:sha(evidenceBytes),importReadReservation:'10 per compiled row plus100 batch allowance; additional operator accounting remains unchanged',cumulativeCeilingsUnchanged:true};
const revised={...body,bundleId:sha(canonical(body)),status,localDatabaseBytes,compression};mkdirSync(target,{recursive:true});
for(const file of [...plan.batches.map(b=>b.file),'serving.sqlite','release-manifest.json'])copyFileSync(join(source,file),join(target,file));
writeFileSync(join(target,'reservation-evidence.json'),evidenceBytes);writeFileSync(join(target,'plan.json'),JSON.stringify(revised,null,2)+'\n');
console.log(JSON.stringify({bundleId:revised.bundleId,priorBundleId:bundleId,batches:revised.batches.length,operationAllowance:revised.operationAllowance,estimatedImportReads:revised.batches.reduce((n,b)=>n+b.estimatedReads,0)}));
