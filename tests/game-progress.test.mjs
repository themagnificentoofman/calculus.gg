import test from 'node:test';
import assert from 'node:assert/strict';
import { initializeApp, deleteApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, signInAnonymously } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator, doc, setDoc, getDoc, updateDoc, terminate, onSnapshot } from 'firebase/firestore';
import { createGameProgress, nextUnanswered, gameStandings } from '../lib/game-progress.ts';
import { loadLeaderboard, loadRecentGames } from '../lib/stat-queries.ts';
const enabled = process.env.FIRESTORE_EMULATOR_HOST === '127.0.0.1:8080';
const questions = ['easy','medium','hard'].map((difficulty,i)=>({latexProblem:'x',options:['1','2','3','4'],correctIndex:0,explanation:['x=1'],topic:i===2?'limits':'integration',difficulty}));
let clock = Date.now(), sequence = 0;
const actors = [];
async function actor() {
  const app = initializeApp({projectId:'demo-calculus-rendering',apiKey:'emulator-only',authDomain:'localhost'},`metrics-${Date.now()}-${sequence++}`);
  const auth = getAuth(app); connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});
  const db = getFirestore(app); connectFirestoreEmulator(db,'127.0.0.1',8080);
  const {user}=await signInAnonymously(auth);
  await setDoc(doc(db,'users',user.uid),{uid:user.uid,displayName:'Metrics QA',email:'',classification:'Novice',rating:0,gamesPlayed:0,wins:0,losses:0,createdAt:new Date().toISOString(),xp:0});
  const a={app,db,uid:user.uid,progress:createGameProgress(db,()=>clock),profile:async()=> (await getDoc(doc(db,'users',user.uid))).data(),game:async id=>(await getDoc(doc(db,'games',id))).data()};actors.push(a);return a;
}
const options={category:'all',difficulty:'medium'};
async function answerAll(a,id,choice=0) {for(let i=0;i<3;i++) await a.progress.submitAnswer(id,a.uid,i,choice);}
test('Enterprise emulator: game rewards, concurrency, results, and statistics', {skip:!enabled,timeout:120_000}, async t=>{
 try {
  await t.test('Test: duplicate submissions and duplicate completion claims award once',async()=>{
    const a=await actor(),id=await a.progress.createGame(a.uid,'test',questions,options);
    const results=await Promise.all([a.progress.submitAnswer(id,a.uid,0,0),a.progress.submitAnswer(id,a.uid,0,0)]);
    assert.equal(results.filter(r=>r.duplicate).length,1);assert.equal((await a.profile()).xp,10);
    await a.progress.submitAnswer(id,a.uid,1,0);await a.progress.submitAnswer(id,a.uid,2,1);
    await Promise.all([a.progress.claimResult(id,a.uid),a.progress.claimResult(id,a.uid)]);
    const p=await a.profile();assert.equal(p.xp,30);assert.equal(p.gamesPlayed,1);assert.equal(p.answeredQuestions,3);assert.equal(p.correctAnswers,2);assert.equal(p.rating,0);
    assert.equal((await loadRecentGames(a.db,a.uid))[0].id,id);
  });
  await t.test('Rapid: absolute deadline, immediate penalty expiry, and no late XP',async()=>{
    const a=await actor(),id=await a.progress.createGame(a.uid,'rapid',questions,{...options,timeLimit:6});
    await assert.rejects(a.progress.submitAnswer(id,a.uid,0,0),/not started/);
    clock+=4000;
    const r=await a.progress.submitAnswer(id,a.uid,0,1);assert.equal(r.game.status,'finished');
    await assert.rejects(a.progress.submitAnswer(id,a.uid,1,0),/ended/);
    await a.progress.claimResult(id,a.uid);assert.equal((await a.profile()).gamesPlayed,1);assert.equal((await a.profile()).xp,0);
    const second=await a.progress.createGame(a.uid,'rapid',questions,{...options,timeLimit:6});clock+=10_000;
    assert.equal((await a.progress.submitAnswer(second,a.uid,0,0)).answer,null);
    await a.progress.claimResult(second,a.uid);assert.equal((await a.profile()).gamesPlayed,1);
  });
  await t.test('PvP: consistent pre-match ratings, waits for both, and reconnect claims once',async()=>{
    const a=await actor(),b=await actor(),id=await a.progress.createGame(a.uid,'pvp',questions,options);
    await b.progress.joinGame(id,b.uid,'pvp');clock+=4000;
    await updateDoc(doc(a.db,'users',a.uid),{rating:100});
    await answerAll(a,id);assert.equal((await a.game(id)).status,'active');assert.equal(nextUnanswered(await a.game(id),a.uid),3);
    await b.progress.submitAnswer(id,b.uid,0,0);await b.progress.submitAnswer(id,b.uid,1,1);await b.progress.submitAnswer(id,b.uid,2,1);
    assert.equal((await a.game(id)).status,'finished');
    const ra=await a.progress.claimResult(id,a.uid);assert.equal(ra.ratingChange,16);assert.equal((await a.profile()).rating,116);
    await b.progress.syncPendingResults(b.uid);await b.progress.syncPendingResults(b.uid);
    assert.equal((await b.profile()).rating,-16);assert.equal((await b.profile()).losses,1);assert.equal((await a.profile()).wins,1);
    assert.equal((await a.profile()).xp,60);assert.equal((await b.profile()).xp,10);
    const board=await loadLeaderboard(a.db);assert.ok(board.some(p=>p.id===b.uid));
  });
  await t.test('Concurrent lobby joins cannot overfill PvP',async()=>{
    const a=await actor(),b=await actor(),c=await actor(),id=await a.progress.createGame(a.uid,'pvp',questions,options);
    const joined=await Promise.allSettled([b.progress.joinGame(id,b.uid,'pvp'),c.progress.joinGame(id,c.uid,'pvp')]);
    assert.equal(joined.filter(r=>r.status==='fulfilled').length,1);assert.equal((await a.game(id)).players.length,2);
  });
  await t.test('Multiplayer: tied winners get draws and equal rating changes',async()=>{
    const a=await actor(),b=await actor(),c=await actor(),id=await a.progress.createGame(a.uid,'multiplayer',questions,{...options,settings:{winCondition:'first_to_n',targetScore:5,timeLimit:60,penalties:false}});
    await b.progress.joinGame(id,b.uid,'multiplayer');await c.progress.joinGame(id,c.uid,'multiplayer');await a.progress.startGame(id,a.uid);
    await answerAll(a,id);await answerAll(b,id);assert.equal((await a.game(id)).status,'active');await answerAll(c,id,1);
    const [ra,rb,rc]=await Promise.all([a.progress.claimResult(id,a.uid),b.progress.claimResult(id,b.uid),c.progress.claimResult(id,c.uid)]);
    assert.equal(ra.outcome,'draw');assert.equal(rb.outcome,'draw');assert.equal(rc.outcome,'loss');assert.equal(ra.ratingChange,rb.ratingChange);
    assert.ok(Math.abs(ra.ratingChange+rb.ratingChange+rc.ratingChange)<1e-9);
    assert.equal((await a.profile()).draws,1);assert.equal((await a.profile()).wins,0);assert.equal((await a.profile()).xp,60);
    assert.deepEqual(gameStandings(await a.game(id)).map(p=>p.rank),[1,1,3]);
  });
  await t.test('Multiplayer: non-host ends expired game; unseen topics do not change',async()=>{
    const a=await actor(),b=await actor(),id=await a.progress.createGame(a.uid,'multiplayer',questions,{...options,settings:{winCondition:'time_limit',targetScore:5,timeLimit:2,penalties:true}});
    await b.progress.joinGame(id,b.uid,'multiplayer');await a.progress.startGame(id,a.uid);
    await b.progress.submitAnswer(id,b.uid,0,0);clock+=3000;
    await b.progress.completeGame(id,b.uid);const receipt=await b.progress.claimResult(id,b.uid);
    assert.equal(receipt.outcome,'win');assert.deepEqual(receipt.topicChanges,{});
    await a.progress.syncPendingResults(a.uid);assert.equal((await a.profile()).losses,1);
    await assert.rejects(b.progress.submitAnswer(id,b.uid,1,0),/ended/);
  });
  await t.test('Returning from an abandoned timed match reconciles its result before a new game',async()=>{
    const a=await actor(),b=await actor(),id=await a.progress.createGame(a.uid,'multiplayer',questions,{...options,settings:{winCondition:'time_limit',targetScore:5,timeLimit:1,penalties:false}});
    await b.progress.joinGame(id,b.uid,'multiplayer');await a.progress.startGame(id,a.uid);
    await a.progress.submitAnswer(id,a.uid,0,0);clock+=2000;
    await b.progress.syncPendingResults(b.uid);
    assert.equal((await b.profile()).losses,1);assert.equal((await a.game(id)).status,'finished');
    await a.progress.syncPendingResults(a.uid);assert.equal((await a.profile()).wins,1);
  });
  await t.test('Background listeners finalize and claim expired rounds without the game screen',async()=>{
    const a=await actor(),id=await a.progress.createGame(a.uid,'rapid',questions,{...options,timeLimit:1});
    clock+=3100;await a.progress.submitAnswer(id,a.uid,0,0);clock+=2000;
    let stopWatch=()=>{},stopProfile=()=>{},timer;
    try {
      await new Promise((resolve,reject)=>{
        timer=setTimeout(()=>reject(new Error('Background result did not settle')),5000);
        stopProfile=onSnapshot(doc(a.db,'users',a.uid),snapshot=>{if(snapshot.data()?.gamesPlayed===1)resolve();},reject);
        stopWatch=a.progress.watchPendingResults(a.uid,reject);
      });
      assert.equal((await a.profile()).xp,10);assert.equal((await a.game(id)).status,'finished');
    } finally {clearTimeout(timer);stopWatch();stopProfile();}
  });
  await t.test('Target-score completion is immediate, and historical matches never re-award',async()=>{
    const a=await actor(),b=await actor(),id=await a.progress.createGame(a.uid,'multiplayer',questions,{...options,settings:{winCondition:'first_to_n',targetScore:1,timeLimit:60,penalties:false}});
    await b.progress.joinGame(id,b.uid,'multiplayer');await a.progress.startGame(id,a.uid);
    assert.equal((await a.progress.submitAnswer(id,a.uid,0,0)).game.status,'finished');
    await a.progress.claimResult(id,a.uid);
    await setDoc(doc(a.db,'games','legacy-'+a.uid),{mode:'pvp',status:'finished',players:[a.uid,b.uid],scores:{[a.uid]:5,[b.uid]:0},createdAt:'2020-01-01T00:00:00.000Z'});
    const receipt=await a.progress.claimResult('legacy-'+a.uid,a.uid);assert.equal(receipt.legacy,true);assert.equal((await a.profile()).gamesPlayed,1);
    assert.equal((await loadRecentGames(a.db,a.uid))[0].id,id);
  });
 } finally {await Promise.all(actors.map(async a=>{await terminate(a.db);await deleteApp(a.app);}));}
});
