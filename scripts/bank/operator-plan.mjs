// Derive a public hash-only verification plan from the preserved compact database.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { canonical } from '../../lib/bank/compact-codec.mjs';
import { loadPlan } from './compact-import.mjs';
const [database, directory] = process.argv.slice(2), db = new DatabaseSync(database, {readOnly:true});
const plan = loadPlan(directory), sha = v => createHash('sha256').update(v).digest('hex');
function problemTuple(r) { return [r.problem_id,r.revision,Buffer.from(r.content_hash).toString('hex'),r.state,r.retirement_reason]; }
const problems=[], memberships=[], pilot=[];
let cursor=['',0];
while(true){const rows=db.prepare('SELECT b.problem_id,b.revision,b.content_hash,u.state,u.retirement_reason FROM cbank_problems b JOIN cbank_publication u USING(problem_ref) WHERE (b.problem_id,b.revision)>(?,?) ORDER BY b.problem_id,b.revision LIMIT 100').all(...cursor);if(!rows.length)break;problems.push({cursor,count:rows.length,hash:sha(canonical(rows.map(problemTuple)))});cursor=[rows.at(-1).problem_id,rows.at(-1).revision];}
let slot=[0,-1];
while(true){const rows=db.prepare('SELECT pool_id,slot,problem_ref FROM cbank_slots WHERE (pool_id,slot)>(?,?) ORDER BY pool_id,slot LIMIT 1000').all(...slot);if(!rows.length)break;memberships.push({cursor:slot,count:rows.length,hash:sha(rows.map(r=>canonical(r)+'\n').join(''))});slot=[rows.at(-1).pool_id,rows.at(-1).slot];}
for(let cursor=928;cursor<1928;cursor+=100){const rows=db.prepare('SELECT problem_id,revision,content_hash FROM cbank_problems WHERE problem_ref>? AND problem_ref<=? ORDER BY problem_ref').all(cursor,cursor+100);pilot.push({cursor,count:rows.length,hash:sha(canonical(rows.map(r=>[r.problem_id,r.revision,Buffer.from(r.content_hash).toString('hex')])))});}
const output={bundleId:plan.bundleId,projectId:'appgprj_6ad91db3d4788191b3e73074e27447f5',batches:plan.batches,expected:plan.expected,releases:plan.releases,problems,memberships,pilot,cells:Object.keys(plan.expected.coverage).sort()};
writeFileSync('lib/server/operator-plan.json',JSON.stringify(output)+'\n');
console.log(JSON.stringify({bundleId:plan.bundleId,batches:output.batches.length,problemPages:problems.length,membershipPages:memberships.length,pilotPages:pilot.length,cells:output.cells.length}));db.close();
