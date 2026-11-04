import test from 'node:test';
import assert from 'node:assert/strict';
import {openCompact} from '../scripts/bank/compact.mjs';
import {flattenSources,applyReleasePolicy} from '../scripts/bank/quality/release-policy.mjs';

function fixture(){
 const db=openCompact(':memory:');
 for(const id of ['v1','v2','v3','v4'])db.prepare("INSERT INTO cbank_releases VALUES (?,'{}',1,?)").run(id,id==='v4'?'staging':'published');
 db.exec("INSERT INTO cbank_release_sources VALUES ('v2','v1'),('v3','v2'),('v3','v1'); INSERT INTO cbank_pools VALUES (1,'v1','integration','easy','*','old-family',1)");
 // Policy-only immutable identities, not published mathematical content.
 for(let i=1;i<=3;i++){
  db.prepare('INSERT INTO cbank_shared VALUES (?,?,?)').run(i,Buffer.alloc(32,i),'{}');
  db.prepare('INSERT INTO cbank_problems VALUES (?,?,?,?,?,?,?)').run(i,'same-item',i,Buffer.alloc(32,i),Buffer.alloc(32,8),i,Buffer.from([1]));
 }
 return db;
}

test('a renamed legacy descendant needs an explicit canonical origin mapping',()=>{
 const db=fixture(),manifest={releaseId:'v4',parentRelease:'v3'},item={problemId:'same-item',problemRevision:3,familyId:'renamed-legacy',pedagogy:{constructionId:'polynomial-area'}};
 try{
  assert.throws(()=>applyReleasePolicy(db,manifest,[item]),/canonical origin alias/);
  assert.equal(db.prepare("SELECT count(*) n FROM cbank_release_sources WHERE release_id='v4'").get().n,0);
  applyReleasePolicy(db,{...manifest,familyLineage:[{familyId:'renamed-legacy',constructionId:'polynomial-area'}]},[item]);
  assert.throws(()=>applyReleasePolicy(db,{...manifest,familyLineage:[{familyId:'polynomial-area',constructionId:'unrelated'}]},[]),/cannot be relabeled/);
 }finally{db.close();}
});

test('transitive and overlapping release sources flatten exactly once and reject cycles',()=>{
 const db=fixture();try{
  assert.deepEqual(flattenSources(db,'v3'),['v1','v2','v3']);
  db.exec("INSERT INTO cbank_release_sources VALUES ('v1','v3')");
  assert.throws(()=>flattenSources(db,'v3'),/cycle/);
 }finally{db.close();}
});

test('policy preserves exclusions, supersedes old revisions, and is idempotent without changing history',()=>{
 const db=fixture();try{
  db.exec("INSERT INTO cbank_release_exclusions VALUES ('v2',1,'global','Incorrect old item')");
  const manifest={releaseId:'v4',parentRelease:'v3',withdrawals:[{sourceReleaseId:'v1',familyId:'old-family',reason:'Exploitable choice construction'}],lineage:[{problemId:'same-item',lineageId:'same-item'}],familyLineage:[{familyId:'renamed-family',constructionId:'old-family'}]};
  const before=db.prepare('SELECT * FROM cbank_problems').all();
  const result=applyReleasePolicy(db,manifest,[{problemId:'same-item',problemRevision:3}]);
  assert.deepEqual(result.sources,['v1','v2','v3']);assert.equal(result.exclusions,2);
  assert.deepEqual(applyReleasePolicy(db,manifest,[{problemId:'same-item',problemRevision:3}]),result);
  assert.equal(db.prepare("SELECT count(*) n FROM cbank_release_sources WHERE release_id='v4'").get().n,3);
  assert.equal(db.prepare('SELECT count(*) n FROM cbank_withdrawn_families').get().n,1);
  assert.deepEqual(db.prepare('SELECT * FROM cbank_problems').all(),before);
  assert.equal(db.prepare("SELECT scope FROM cbank_release_exclusions WHERE release_id='v4' AND problem_ref=1").get().scope,'global');
  assert.throws(()=>db.exec('DELETE FROM cbank_release_exclusions'),/Retain/);
 }finally{db.close();}
});

test('unknown withdrawals, conflicting lineage and unpublished ancestors fail closed',()=>{
 const db=fixture();try{
  assert.throws(()=>flattenSources(db,'v4'),/Unpublished/);
  assert.throws(()=>applyReleasePolicy(db,{releaseId:'v4',parentRelease:'v3',withdrawals:[{sourceReleaseId:'outside',familyId:'old-family',reason:'bad'}]},[]),/Unknown/);
  assert.throws(()=>applyReleasePolicy(db,{releaseId:'v4',parentRelease:'v3',lineage:[{problemId:'missing',lineageId:'same-item'}]},[]),/existing/);
 }finally{db.close();}
});

test('ancestor scoped exclusions never downgrade global exclusions and failed policies are atomic',()=>{
 const db=fixture();try{
  db.exec("INSERT INTO cbank_release_exclusions VALUES ('v1',1,'global','Incorrect'),('v3',1,'release','Scoped duplicate')");
  assert.throws(()=>applyReleasePolicy(db,{releaseId:'v4',parentRelease:'v3',withdrawals:[{sourceReleaseId:'outside',familyId:'old-family',reason:'bad'}]},[]),/Unknown/);
  assert.equal(db.prepare("SELECT count(*) n FROM cbank_release_sources WHERE release_id='v4'").get().n,0);
  assert.equal(db.prepare("SELECT count(*) n FROM cbank_release_exclusions WHERE release_id='v4'").get().n,0);
  applyReleasePolicy(db,{releaseId:'v4',parentRelease:'v3'},[]);
  assert.equal(db.prepare("SELECT scope FROM cbank_release_exclusions WHERE release_id='v4' AND problem_ref=1").get().scope,'global');
 }finally{db.close();}
});

test('planned aliases cannot create order-dependent chains, cycles, or unbounded policy',()=>{
 const db=fixture();try{
  const base={releaseId:'v4',parentRelease:'v3'};
  assert.throws(()=>applyReleasePolicy(db,{...base,familyLineage:[{familyId:'a',constructionId:'b'},{familyId:'b',constructionId:'c'}]},[]),/flattened/);
  assert.throws(()=>applyReleasePolicy(db,{...base,familyLineage:[{familyId:'a',constructionId:'b'},{familyId:'b',constructionId:'a'}]},[]),/flattened/);
  assert.throws(()=>applyReleasePolicy(db,{...base,withdrawals:Array(1025).fill({})},[]),/bound/);
 }finally{db.close();}
});
