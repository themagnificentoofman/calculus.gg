#!/usr/bin/env node
// CI gate for the reviewed source/data/renderer binding. Mathematics is checked
// by the separate reproducible family suites and complete inventory audit.
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const manifest=JSON.parse(readFileSync('docs/bank/solution-quality/review-manifest.json'));
for(const [path,expected]of Object.entries(manifest.files))assert.equal(createHash('sha256').update(readFileSync(path)).digest('hex'),expected,'Review binding changed: '+path);
const finite=JSON.parse(readFileSync('lib/server/solution-reviews/finite.json'));
assert.equal(Object.keys(finite).length,2504);assert.equal(new Set(Object.values(finite).map(p=>p.familyId)).size,313);
for(const [id,p]of Object.entries(finite)){assert.match(id,/^cn_[a-f0-9]{20}$/);assert.match(p.sourceContentHash,/^[a-f0-9]{64}$/);assert.equal(p.revision,1);assert.ok(p.steps.length>=2&&p.steps.length<=40);}
const hashes=JSON.parse(readFileSync('lib/server/solution-reviews/legacy-hashes.json'));assert.equal(hashes.length,100800*64);
let prior='';for(let i=0;i<hashes.length;i+=64){const next=hashes.slice(i,i+64);assert.match(next,/^[a-f0-9]{64}$/);assert.ok(next>prior);prior=next;}
const report=JSON.parse(readFileSync('docs/bank/solution-quality/full-inventory-audit.json'));
assert.equal(report.records,103304);assert.equal(report.reviewedRecords,103304);assert.equal(report.sourceHashesChecked,103304);assert.equal(report.familyCount,385);assert.equal(report.renderFailures+report.formatFailures+report.notationChanges,0);
console.log(JSON.stringify({reviewBinding:'passed',records:report.records,families:report.familyCount,expressions:report.uniqueRenderedExpressions,finiteCorrections:2504,legacySourceHashes:100800}));
