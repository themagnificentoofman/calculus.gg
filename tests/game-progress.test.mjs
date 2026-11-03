import test from 'node:test';
import assert from 'node:assert/strict';
import { initializeApp, deleteApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, signInAnonymously } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator, doc, getDoc, setDoc, updateDoc, deleteDoc, collection, getDocs, query, where, terminate } from 'firebase/firestore';
import { firestoreStore } from '../lib/server/firestore-admin.ts';
import { createGameApi } from '../lib/server/game-api.ts';
import { loadLeaderboard, loadRecentGames, loadWaitingGames, searchPublicProfiles } from '../lib/stat-queries.ts';
const enabled = process.env.FIRESTORE_EMULATOR_HOST === '127.0.0.1:8080';
const project = 'demo-calculus-rendering';
const store = firestoreStore(project, '(default)', async () => 'owner', 'http://127.0.0.1:8080');
let clock = Date.now(), sequence = 0;
const actors = [], identities = new Map();
const fixture = (difficulty, count) => Array.from({length:count},(_,i)=>({latexProblem:String.raw`\int x^2\,dx`,options:[String.raw`\frac{x^3}{3}+C`,'x+C','2x+C','3x+C'],correctIndex:0,explanation:[String.raw`\textnormal{Apply the power rule.}`],topic:'integration',difficulty}));
const api = createGameApi({store,now:()=>clock,verify:async token=>{const c=identities.get(token);if(!c)throw Error('invalid');return c;},select:async({difficulty:d,count:n})=>({questions:fixture(d,n),relaxation:'none'}),quota:async()=>true});
async function actor() {
 const app=initializeApp({projectId:project,apiKey:'emulator-only',authDomain:'localhost'},`secure-${Date.now()}-${sequence++}`);
 const auth=getAuth(app);connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});const db=getFirestore(app);connectFirestoreEmulator(db,'127.0.0.1',8080);
 const {user}=await signInAnonymously(auth),token=await user.getIdToken();identities.set(token,{sub:user.uid,name:'Secure QA',email:'private@example.test'});
 const a={app,db,uid:user.uid,token,
  call:async(resource,body,expected=200)=>{const res=await api(resource,new Request(`https://test.invalid/api/${resource}`,{method:'POST',headers:{authorization:`Bearer ${token}`,'content-type':'application/json'},body:JSON.stringify(body)}));const payload=await res.json();assert.equal(res.status,expected,JSON.stringify(payload));return payload;},
  profile:async()=> (await getDoc(doc(db,'users',user.uid))).data(), game:async id=>(await getDoc(doc(db,'games',id))).data()};actors.push(a);await a.call('profile',{});return a;
}
async function game(a,mode='test',difficulty='easy',count=3,extra={}) {
 const set=await a.call('questions',{mode,category:'integration',difficulty,count});assert.deepEqual(Object.keys(set).sort(),['questionCount','questionSetId']);
 const options={category:'integration',difficulty,timeLimit:30,settings:{winCondition:'first_to_n',targetScore:5,timeLimit:30,penalties:false},...extra};
 return (await a.call('games',{action:'create',mode,questionSetId:set.questionSetId,options})).id;
}
const answer=(a,id,index,selectedOption=0,expected=200)=>a.call('games',{action:'answer',gameId:id,index,selectedOption},expected);
const all=async(a,id,choice=0)=>{for(let i=0;i<3;i++)await answer(a,id,i,choice);};
const denied=promise=>assert.rejects(promise,e=>e.code==='permission-denied');
test('Server-authoritative games and Firestore attack tests', {skip:!enabled,timeout:180000},async t=>{
 try {
  await t.test('Test: private generation, server grading, concurrent replay and exactly-once rewards',async()=>{
   const a=await actor(),id=await game(a);
   const first=await a.call('games',{action:'view',gameId:id});assert.ok(!JSON.stringify(first).includes('correctIndex'));assert.ok(!JSON.stringify(first).includes('explanation'));
   const r=await Promise.all([answer(a,id,0),answer(a,id,0)]);assert.equal(r.filter(x=>x.duplicate).length,1);assert.equal((await a.profile()).xp,10);
   assert.equal(r[0].progress.reviews[0].correctIndex,0);assert.equal(r[0].progress.reviews[1],undefined);
   await answer(a,id,1);await answer(a,id,2,1);await a.call('games',{action:'claim',gameId:id});await a.call('games',{action:'claim',gameId:id});
   const p=await a.profile();assert.equal(p.xp,20);assert.equal(p.gamesPlayed,1);assert.equal(p.answeredQuestions,3);assert.equal(p.correctAnswers,2);
   assert.equal((await loadRecentGames(a.db,a.uid))[0].id,id);
   const publicDoc=await a.game(id);assert.ok(!JSON.stringify(publicDoc).includes('correctIndex'));assert.ok(!JSON.stringify(publicDoc).includes('selectedOption'));
  });
  await t.test('All score, key, receipt, UID and private-profile tampering paths are denied',async()=>{
   const a=await actor(),b=await actor(),id=await game(a);
   for (const patch of [{xp:99999},{rating:99999},{topicRatings:{integration:99999}},{gamesPlayed:999},{uid:b.uid}]) await denied(updateDoc(doc(a.db,'users',a.uid),patch));
   await denied(setDoc(doc(a.db,'users','invented'),{uid:'invented',xp:999}));await denied(deleteDoc(doc(a.db,'users',a.uid)));
   for(const patch of [{scores:{[a.uid]:999}},{players:[b.uid]},{receipts:{[a.uid]:{newRating:999}}},{questions:fixture('olympiad',3)},{deadline:clock+10000000},{messages:[{text:'forged'}]}])await denied(updateDoc(doc(a.db,'games',id),patch));
   await denied(getDoc(doc(a.db,'gameSecrets',id)));await denied(getDoc(doc(a.db,'questionSets',id)));await denied(getDoc(doc(b.db,'users',a.uid)));await denied(getDoc(doc(b.db,'games',id)));await denied(getDocs(collection(a.db,'users')));
   await denied(setDoc(doc(a.db,'users_public',a.uid),{rating:999}));await denied(setDoc(doc(a.db,'games',id,'reviews',a.uid),{answers:{0:{correct:true}}}));
   for(const key of ['uid','score','xp','correct','correctIndex','now','deadline'])await a.call('games',{action:'answer',gameId:id,index:0,selectedOption:0,[key]:999},400);
   await a.call('profile',{patch:{xp:999}},400);await b.call('games',{action:'answer',gameId:id,index:0,selectedOption:0},403);
   await answer(a,id,2,0,409);await answer(a,id,-1,0,400);await answer(a,id,0,4,400);
   assert.equal((await a.profile()).xp,0);
  });
  await t.test('Question sets are bound to owner and mode, expire, and cannot be replayed as new games',async()=>{
   const a=await actor(),b=await actor(),set=await a.call('questions',{mode:'test',category:'integration',difficulty:'hard',count:3});
   await b.call('games',{action:'create',mode:'test',questionSetId:set.questionSetId,options:{}},403);
   await a.call('games',{action:'create',mode:'pvp',questionSetId:set.questionSetId,options:{}},403);
   const create={action:'create',mode:'test',questionSetId:set.questionSetId,options:{}};
   const [x,y]=await Promise.all([a.call('games',create),a.call('games',create)]);assert.equal(x.id,y.id);await all(a,x.id);assert.equal((await a.profile()).xp,90);
   assert.equal((await a.call('games',create)).id,x.id);assert.equal((await a.profile()).gamesPlayed,1);
   const expired=await a.call('questions',{mode:'test',category:'integration',difficulty:'easy',count:1});clock+=31*60_000;
   await a.call('games',{action:'create',mode:'test',questionSetId:expired.questionSetId,options:{}},400);
  });
  await t.test('Rapid uses server time, rejects early/late answers, and applies the time penalty',async()=>{
   const a=await actor(),id=await game(a,'rapid');await answer(a,id,0,0,409);clock+=4000;
   await answer(a,id,0);const before=(await a.game(id)).deadline;await answer(a,id,1,1);assert.equal((await a.game(id)).deadline,before-5000);
   await a.call('games',{action:'complete',gameId:id});assert.equal((await a.game(id)).status,'active');
   clock=before+1000;const late=await answer(a,id,2);assert.equal(late.answer,null);assert.equal(late.game.status,'finished');assert.equal((await a.profile()).xp,10);assert.equal((await a.profile()).gamesPlayed,1);
  });
  await t.test('PvP hides waiting questions, isolates reviews, waits for both and credits both atomically',async()=>{
   const a=await actor(),b=await actor(),id=await game(a,'pvp','medium');assert.equal((await a.game(id)).questions.length,0);
   await b.call('games',{action:'join',gameId:id,mode:'pvp'});clock+=4000;await all(a,id);assert.equal((await a.game(id)).status,'active');
   await denied(getDoc(doc(b.db,'games',id,'reviews',a.uid)));
   const view=await b.call('games',{action:'view',gameId:id});assert.ok(!JSON.stringify(view).includes('correctIndex'));assert.ok(!JSON.stringify(view).includes('selectedOption'));
   await answer(b,id,0);await answer(b,id,1,1);await answer(b,id,2,1);
   const pa=await a.profile(),pb=await b.profile();assert.equal(pa.rating,16);assert.equal(pb.rating,-16);assert.equal(pa.wins,1);assert.equal(pb.losses,1);assert.equal(pa.xp,60);assert.equal(pb.xp,20);
   await a.call('games',{action:'claim',gameId:id});await b.call('games',{action:'claim',gameId:id});assert.equal((await a.profile()).rating,16);
   const board=await loadLeaderboard(a.db);assert.ok(board.some(p=>p.id===b.uid));assert.ok(board.every(p=>!('email' in p)&&!('settings' in p)&&!('friends' in p)));
  });
  await t.test('Concurrent PvP joins respect capacity and outsider/early starts fail',async()=>{
   const a=await actor(),b=await actor(),c=await actor(),id=await game(a,'pvp');
   const join=async p=>{const res=await api('games',new Request('https://test.invalid/api/games',{method:'POST',headers:{authorization:`Bearer ${p.token}`,'content-type':'application/json'},body:JSON.stringify({action:'join',gameId:id,mode:'pvp'})}));return res.status;};
   assert.deepEqual((await Promise.all([join(b),join(c)])).sort(),[200,409]);assert.equal((await a.game(id)).players.length,2);
  });
  await t.test('Multiplayer ties, target completion and offline player results remain consistent',async()=>{
   const a=await actor(),b=await actor(),c=await actor(),id=await game(a,'multiplayer');
   await b.call('games',{action:'join',gameId:id,mode:'multiplayer'});await c.call('games',{action:'join',gameId:id,mode:'multiplayer'});await b.call('games',{action:'start',gameId:id},403);await a.call('games',{action:'start',gameId:id});
   await all(a,id);await all(b,id);await all(c,id,1);const g=await a.game(id);assert.equal(g.status,'finished');assert.deepEqual(Object.values(g.receipts).map(r=>r.rank).sort(),[1,1,3]);
   const ps=await Promise.all([a.profile(),b.profile(),c.profile()]);assert.equal(ps[0].rating,ps[1].rating);assert.equal(ps.reduce((n,p)=>n+p.rating,0),0);assert.equal(ps[0].draws,1);assert.equal(ps[2].losses,1);
   const target=await game(a,'multiplayer','olympiad',3,{settings:{winCondition:'first_to_n',targetScore:2,timeLimit:30,penalties:true}});await b.call('games',{action:'join',gameId:target,mode:'multiplayer'});await a.call('games',{action:'start',gameId:target});await answer(a,target,0);await answer(a,target,1);
   assert.equal((await a.game(target)).status,'finished');assert.equal((await b.profile()).gamesPlayed,2);assert.equal((await a.profile()).xp,130);
  });
  await t.test('Multiplayer accepts both UI target limits and rejects forged settings',async()=>{
   const a=await actor(),b=await actor();
   const one=await game(a,'multiplayer','easy',3,{settings:{winCondition:'first_to_n',targetScore:1,timeLimit:30,penalties:false}});
   await b.call('games',{action:'join',gameId:one,mode:'multiplayer'});await a.call('games',{action:'start',gameId:one});await answer(a,one,0);assert.equal((await a.game(one)).status,'finished');
   await game(a,'multiplayer','hard',20,{settings:{winCondition:'first_to_n',targetScore:20,timeLimit:300,penalties:true}});
   const set=await a.call('questions',{mode:'multiplayer',category:'integration',difficulty:'easy',count:3});
   for(const patch of [{targetScore:0},{targetScore:21},{timeLimit:29},{timeLimit:301},{penalties:'false'},{xp:999}])await a.call('games',{action:'create',mode:'multiplayer',questionSetId:set.questionSetId,options:{settings:{winCondition:'first_to_n',targetScore:2,timeLimit:30,penalties:false,...patch}}},400);
  });
  await t.test('Server reconciliation closes expired matches and cannot re-award historical games',async()=>{
   const a=await actor(),b=await actor(),id=await game(a,'multiplayer','easy',3,{settings:{winCondition:'time_limit',targetScore:5,timeLimit:30,penalties:false}});
   await b.call('games',{action:'join',gameId:id,mode:'multiplayer'});await a.call('games',{action:'start',gameId:id});await answer(a,id,0);
   // Unfinished untimed practice must not crowd expired matches out of reconciliation.
   await store.transaction(async tx=>{await tx.get(`users/${b.uid}`);for(let i=0;i<101;i++)tx.set(`gameSecrets/unended_${b.uid}_${i}`,{mode:'test',status:'active',players:[b.uid],progressionVersion:3});});
   clock+=31000;await b.call('games',{action:'sync'});
   assert.equal((await a.profile()).wins,1);assert.equal((await b.profile()).losses,1);await a.call('games',{action:'sync'});assert.equal((await a.profile()).gamesPlayed,1);
   await store.transaction(async tx=>{await tx.get('games/historical');tx.set('games/historical',{mode:'test',status:'finished',progressionVersion:2,players:[a.uid],scores:{[a.uid]:5},createdAt:'2025-01-01T00:00:00.000Z'});});
   await a.call('games',{action:'claim',gameId:'historical'},409);assert.equal((await a.profile()).gamesPlayed,1);assert.ok((await loadRecentGames(a.db,a.uid)).some(g=>g.id==='historical'));
  });
  await t.test('Profile preferences, private friendships, invitations and chat still work under locked rules',async()=>{
   const a=await actor(),b=await actor(),c=await actor();await a.call('profile',{patch:{displayName:'Player A',color:'#123456',settings:{soundEnabled:false}}});
   const r=await a.call('social',{action:'request',to:b.uid});await c.call('social',{action:'accept',id:r.id},404);await a.call('social',{action:'accept',id:r.id},403);await b.call('social',{action:'accept',id:r.id});assert.ok((await b.profile()).friends.includes(a.uid));
   const found=await searchPublicProfiles(b.db,b.uid,'player a');assert.ok(found.some(p=>p.uid===a.uid));assert.ok(found.every(p=>!('email'in p)));
   const id=await game(a,'pvp');assert.ok((await loadWaitingGames(b.db,b.uid,'pvp')).some(g=>g.id===id));
   await a.call('games',{action:'chat',gameId:id,text:3},400);const invite=await a.call('social',{action:'invite',to:b.uid,gameId:id});await b.call('social',{action:'invite_accept',id:invite.id});await b.call('games',{action:'join',gameId:id,mode:'pvp'});
   await c.call('games',{action:'chat',gameId:id,text:'forged'},403);await a.call('games',{action:'chat',gameId:id,text:'hello'});const m=(await a.game(id)).messages[0];assert.equal(m.senderId,a.uid);assert.equal(m.senderName,'Player A');assert.equal(m.timestamp,clock);
   await a.call('games',{action:'chat',gameId:id,text:'bad',senderId:b.uid},400);await denied(setDoc(doc(a.db,'friendRequests','spoof'),{from:b.uid,to:c.uid,status:'accepted'}));
   await b.call('social',{action:'remove',friendId:a.uid});assert.ok(!(await a.profile()).friends.includes(b.uid));
   const waiting=await game(a,'multiplayer');assert.ok((await getDocs(query(collection(b.db,'games'),where('status','==','waiting'),where('mode','==','multiplayer'),where('progressionVersion','==',3)))).docs.some(d=>d.id===waiting));
  });

  await t.test('Friend request send, duplicate, reciprocal, cancel, decline, accept and removal preserve consent',async()=>{
   const a=await actor(),b=await actor(),c=await actor();
   const r=await a.call('social',{action:'request',to:b.uid});
   await a.call('social',{action:'request',to:b.uid});
   await b.call('social',{action:'request',to:a.uid},409);
   await b.call('social',{action:'cancel',id:r.id},403);
   await a.call('social',{action:'cancel',id:r.id});
   assert.equal(await store.get(`friendRequests/${r.id}`),null);
   clock+=2001;const declined=await a.call('social',{action:'request',to:b.uid});
   await b.call('social',{action:'reject',id:declined.id});
   await b.call('social',{action:'accept',id:declined.id});
   assert.deepEqual((await a.profile()).friends,[]);
   clock+=2001;const accepted=await a.call('social',{action:'request',to:b.uid});
   // Reconcile a crossed request created by the previous release.
   await store.transaction(async tx=>{await tx.get(`friendRequests/${b.uid}_${a.uid}`);tx.set(`friendRequests/${b.uid}_${a.uid}`,{from:b.uid,to:a.uid,status:'pending',createdAt:new Date(clock)});});
   await b.call('social',{action:'accept',id:accepted.id});
   assert.equal(await store.get(`friendRequests/${b.uid}_${a.uid}`),null);
   await b.call('social',{action:'remove',friendId:a.uid});
   await a.call('social',{action:'accept',id:`${b.uid}_${a.uid}`},404);
   assert.deepEqual((await a.profile()).friends,[]);assert.deepEqual((await b.profile()).friends,[]);
   const before=await c.profile();await a.call('social',{action:'remove',friendId:c.uid});assert.deepEqual(await c.profile(),before);
   await a.call('social',{action:'request',to:a.uid},400);
   assert.deepEqual(await searchPublicProfiles(a.db,a.uid,'no-match-xyz'),[]);
  });
  await t.test('Invitations join atomically, reject full/expired/nonfriend rooms and cannot be replayed',async()=>{
   const a=await actor(),b=await actor(),c=await actor();const request=await a.call('social',{action:'request',to:b.uid});await b.call('social',{action:'accept',id:request.id});
   const full=await game(a,'pvp');const invite=await a.call('social',{action:'invite',to:b.uid,gameId:full});
   await c.call('games',{action:'join',gameId:full,mode:'pvp'});
   await b.call('social',{action:'invite_accept',id:invite.id},409);
   assert.equal((await store.get(`gameInvites/${invite.id}`)).status,'pending');
   await b.call('social',{action:'invite_reject',id:invite.id});
   clock+=2001;const id=await game(a,'pvp');const next=await a.call('social',{action:'invite',to:b.uid,gameId:id});
   const accepted=await b.call('social',{action:'invite_accept',id:next.id});assert.equal(accepted.gameId,id);assert.equal((await a.game(id)).status,'active');
   await b.call('social',{action:'invite_accept',id:next.id});assert.equal((await a.game(id)).players.length,2);
   clock+=2001;const waiting=await game(a,'multiplayer');const stale=await a.call('social',{action:'invite',to:b.uid,gameId:waiting});
   await b.call('social',{action:'remove',friendId:a.uid});await b.call('social',{action:'invite_accept',id:stale.id},409);
   await b.call('social',{action:'invite_reject',id:stale.id});
   await a.call('social',{action:'invite',to:c.uid,gameId:waiting},403);
  });
  await t.test('Leaving and cancelling lobbies changes server membership; abandoned lobbies expire',async()=>{
   const a=await actor(),b=await actor(),c=await actor();const id=await game(a,'multiplayer');
   await b.call('games',{action:'join',gameId:id,mode:'multiplayer'});
   await c.call('games',{action:'leave',gameId:id},403);
   await b.call('games',{action:'leave',gameId:id});assert.deepEqual((await a.game(id)).players,[a.uid]);
   await denied(getDoc(doc(b.db,'games',id,'reviews',b.uid)));
   await a.call('games',{action:'start',gameId:id},400);
   await a.call('games',{action:'leave',gameId:id});assert.equal((await a.game(id)).status,'cancelled');
   await c.call('games',{action:'join',gameId:id,mode:'multiplayer'},409);
   assert.ok(!(await loadWaitingGames(c.db,c.uid,'multiplayer')).some(g=>g.id===id));
   const expired=await game(a,'pvp');clock+=30*60000+1;await b.call('games',{action:'join',gameId:expired,mode:'pvp'},409);
   await a.call('games',{action:'view',gameId:expired});assert.equal((await a.game(expired)).status,'cancelled');
   const active=await game(a,'pvp');await b.call('games',{action:'join',gameId:active,mode:'pvp'});await a.call('games',{action:'leave',gameId:active},409);
   assert.equal((await a.profile()).xp,0);assert.equal((await a.profile()).ratedGames,0);
  });
  await t.test('Mutation throttling rejects before any profile or game database work',async()=>{
   const a=await actor();const before=await a.profile();
   const limited=createGameApi({store,verify:async()=>({sub:a.uid}),generate:async()=>[],quota:async()=>true,mutationQuota:async()=>false});
   const response=await limited('profile',new Request('https://test.invalid/api/profile',{method:'POST',headers:{authorization:`Bearer ${a.token}`,'content-type':'application/json'},body:JSON.stringify({patch:{displayName:'Should not change'}})}));
   assert.equal(response.status,429);assert.deepEqual(await a.profile(),before);
  });
  await t.test('Missing/forged authentication, cross-site requests and unbounded bodies fail closed',async()=>{
   for(const authorization of ['', 'Bearer forged']) {const r=await api('games',new Request('https://test.invalid/api/games',{method:'POST',headers:{authorization,'content-type':'application/json'},body:'{"action":"sync"}'}));assert.equal(r.status,401);}
   const a=await actor();const r=await api('games',new Request('https://test.invalid/api/games',{method:'POST',headers:{authorization:`Bearer ${a.token}`,origin:'https://evil.invalid','content-type':'application/json'},body:'{}'}));assert.equal(r.status,403);
   for (const resource of ['games','social','profile','questions']) await a.call(resource,null,400);
   for (const action of ['constructor','__proto__','toString']) await a.call('games',{action},400);
   await a.call('profile',{patch:7},400);
   await a.call('games',{action:'sync',padding:'x'.repeat(9000)},400);
   const app=initializeApp({projectId:project,apiKey:'emulator-only'},'unsigned-read');const db=getFirestore(app);connectFirestoreEmulator(db,'127.0.0.1',8080);await denied(getDocs(collection(db,'users_public')));await terminate(db);await deleteApp(app);
  });
 } finally {await Promise.all(actors.map(async a=>{await terminate(a.db);await deleteApp(a.app);}));}
});
