import test from 'node:test';
import assert from 'node:assert/strict';
import {isolatedQaStore,operatorQa} from '../lib/server/operator-qa.ts';
import {firestoreStore} from '../lib/server/firestore-admin.ts';
import {verifyHostedGameplay} from '../scripts/bank/operator-gameplay.mjs';
import {sqliteD1} from '../scripts/bank/sqlite-d1.mjs';
import {DatabaseSync} from 'node:sqlite';
import {copyFileSync,mkdtempSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
test('hosted QA prefixes every read, write, query and deletion without exposing player collections',async()=>{
  const seen=[],base={get:async p=>{seen.push(p);return null;},find:async p=>{seen.push(p);return [];},transaction:async fn=>fn({get:baseGet,set:p=>seen.push(p),delete:p=>seen.push(p)})};
  async function baseGet(p){seen.push(p);return null;}
  const qa=isolatedQaStore(base);await qa.get('users/fixedqa');await qa.find('games',[],3);
  await qa.transaction(async tx=>{await tx.get('gameSecrets/fixture');tx.set('games/fixture/reviews/fixedqa',{});tx.delete('users_public/fixedqa');});
  assert.deepEqual(seen,['users/fixedqa','games','gameSecrets/fixture','games/fixture/reviews/fixedqa','users_public/fixedqa'].map(p=>'cn_m1qa_ed08a3de_'+p));
  assert.throws(()=>qa.get('other/real'),/Unsupported/);
});
test('four-mode verification harness checks full bank gameplay and cleans isolated records',{skip:process.env.FIRESTORE_EMULATOR_HOST!=='127.0.0.1:8080',timeout:180000},async()=>{
  const dir=mkdtempSync(join(tmpdir(),'operator-qa-')),file=join(dir,'bank.sqlite');copyFileSync('../calculus.ninja/.bank-data/compact/serving.sqlite',file);
  const sql=new DatabaseSync(file),store=firestoreStore('demo-calculus-rendering','(default)',async()=>'owner','http://127.0.0.1:8080');
  try{
    sql.exec(readFileSync('drizzle/0000_dazzling_tenebrous.sql','utf8'));sql.exec("UPDATE cbank_releases SET state='published'; INSERT OR REPLACE INTO cbank_config VALUES ('active_release','cn-2026-11-02-full-v2')");
    const result=await verifyHostedGameplay(async input=>({qa:await operatorQa(input,sqliteD1(sql),store)}),()=>{});
    assert.equal(result.passed,true);assert.equal(result.modes,4);
  }finally{sql.close();rmSync(dir,{recursive:true,force:true});}
});
