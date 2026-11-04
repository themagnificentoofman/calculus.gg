import test from 'node:test';
import assert from 'node:assert/strict';
import {createServerGames,publicGame} from '../lib/server/game-engine.ts';
import {createReplayApi} from '../lib/server/replay-api.ts';
import {initialState,compileReplay,reduceEvent,orderEvents,originalClock,problemEvidence,roundAnalysis} from '../lib/replay/engine.ts';
import {PlaybackClock,loadReplay} from '../lib/replay/playback.ts';
import {replayStatus,REPLAY_LIMITS,legacyMessage} from '../lib/replay/contracts.ts';
import {CaptureQueue} from '../lib/replay/queue.ts';
const clone=v=>v===undefined?undefined:structuredClone(v);
class MemoryStore {
 docs=new Map();writes=0;retry=false;
 async get(path){return clone(this.docs.get(path)||null);}
 async find(){return [];}
 async transaction(fn){let result,writes;for(let attempt=0;attempt<(this.retry?2:1);attempt++){writes=new Map();result=await fn({get:async path=>{assert.equal(writes.size,0,'reads precede writes');return this.get(path);},set:(path,value)=>writes.set(path,clone(value)),delete:path=>writes.set(path,null)});}this.retry=false;for(const [p,v]of writes){if(v===null)this.docs.delete(p);else this.docs.set(p,v);this.writes++;}return result;}
}
const fixture=()=>Array.from({length:3},(_,i)=>({latexProblem:`x_${i}+1`,options:['1','2','3','4'],correctIndex:0,explanation:['Exact saved solution'],topic:'integration',difficulty:'easy',problemId:`cn_problem_${i}`,problemRevision:7,contentHash:`hash${i}`,bankRelease:'verified-release',familyId:'family',choiceOrder:['a','b','c','d'],context:{assumptions:'real',subtopic:'power',techniqueTags:['power'],parameters:{i}}}));
async function setup(){const store=new MemoryStore();let clock=1000000;const games=createServerGames(store,()=>clock),api=createReplayApi({store,now:()=>clock,verify:async token=>({sub:token})});for(const uid of ['alice','bobby','carol'])await games.profile(uid,{});
 const call=async(uid,body,status=200)=>{const response=await api(new Request('https://ninja.test/api/replay',{method:'POST',headers:{authorization:`Bearer ${uid}`,'content-type':'application/json'},body:JSON.stringify(body)}));const payload=await response.json();assert.equal(response.status,status,JSON.stringify(payload));return payload;};
 const create=async(mode,settings={winCondition:'first_to_n',targetScore:2,timeLimit:30,penalties:true})=>{const set=await games.storeQuestions('alice',mode,'integration','easy',fixture());await games.createGame('alice',set.questionSetId,mode,{timeLimit:30,settings});return set.questionSetId;};return {store,games,call,create,advance:n=>clock+=n,time:()=>clock};}
for(const mode of ['test','rapid','pvp','multiplayer-target','multiplayer-time'])test(`${mode}: atomic authoritative replay, immutable content, match gate and read-only replay`,async()=>{
 const s=await setup(),multi=mode.startsWith('multiplayer'),gameMode=multi?'multiplayer':mode,id=await s.create(gameMode,{winCondition:mode==='multiplayer-time'?'time_limit':'first_to_n',targetScore:2,timeLimit:30,penalties:true});
 const content=await s.store.get(`replayContent/${id}`);assert.deepEqual(content.questions,fixture());
 if(multi||mode==='pvp'){await s.games.act('bobby',id,'join',{mode:gameMode});if(multi)await s.games.act('alice',id,'start');}
 await s.call('carol',{op:'read',roundId:id},403);for(const op of ['read','server','client'])await s.call('alice',{op,roundId:id,start:0,segmentId:'session1'},409);
 s.advance(4000);s.store.retry=true;const first=await s.games.act('alice',id,'answer',{index:0,selectedOption:0,requestId:'request_one'});assert.ok(first.answer.serverEventId);
 const writes=s.store.writes,dup=await s.games.act('alice',id,'answer',{index:0,selectedOption:3,requestId:'request_two'});assert.equal(dup.answer.selectedOption,0);assert.equal(s.store.writes,writes);
 if(mode==='pvp'){for(let i=1;i<3;i++)await s.games.act('alice',id,'answer',{index:i,selectedOption:0});await s.call('alice',{op:'read',roundId:id},409);for(let i=0;i<3;i++)await s.games.act('bobby',id,'answer',{index:i,selectedOption:1});}
 else if(mode==='test'){for(let i=1;i<3;i++)await s.games.act('alice',id,'answer',{index:i,selectedOption:0});}
 else if(mode==='multiplayer-target')await s.games.act('alice',id,'answer',{index:1,selectedOption:0});
 else {const before=await s.store.get(`gameSecrets/${id}`);await s.games.act('alice',id,'answer',{index:1,selectedOption:1});const after=await s.store.get(`gameSecrets/${id}`);if(mode==='rapid')assert.equal(after.deadline,before.deadline-5000);else assert.equal(after.scores.alice,0);s.advance(60000);await s.games.act('alice',id,'complete');}
 const game=await s.store.get(`gameSecrets/${id}`),manifest=await s.store.get(`replayManifests/${id}`);assert.equal(game.status,'finished');assert.equal(manifest.logicalEndAt,game.logicalEndAt);assert.equal(manifest.settledAt,game.finishedAt);
 if(mode==='rapid'||mode==='multiplayer-time')assert.ok(manifest.logicalEndAt<manifest.settledAt);
 const snapshot=await s.call('alice',{op:'read',roundId:id});assert.deepEqual(snapshot.content.questions,fixture());
 const beforeReads=clone([...s.store.docs]),loaded=await loadReplay(id,b=>s.call('alice',b));assert.deepEqual([...s.store.docs],beforeReads,'playback never writes game, XP or rating');
 assert.equal(loaded.events.filter(e=>e.type==='answer_accepted'&&e.data.index===0).length,1);assert.ok(!loaded.events.some(e=>e.type==='answer_accepted'&&e.playerId==='bobby'));
 assert.equal(manifest.sequence,game.replaySequence);assert.equal(manifest.chunkCount,game.replayChunkCount);
 const seq=[...s.store.docs].filter(([k])=>k.startsWith(`replayServer/${id}_`)).flatMap(([,v])=>v.events.map(e=>e.sequence));assert.deepEqual(seq,Array.from({length:seq.length},(_,i)=>i+1));
 assert.ok(!JSON.stringify(publicGame(game)).includes('Exact saved solution'));assert.ok(!JSON.stringify(loaded).includes('private@example'));
 // A future bank revision cannot change this snapshot.
 await s.games.storeQuestions('alice','test','integration','easy',fixture().map(q=>({...q,latexProblem:'replacement',problemRevision:8})));assert.deepEqual((await s.store.get(`replayContent/${id}`)).questions,content.questions);
});
const event=(sequence,type,extra={})=>({schemaVersion:1,eventId:`event_${sequence}`,sequence,monotonicMs:sequence*100,type,...extra});
test('Client chunks: acknowledgements, identical retries, conflicts, gaps, bounded schema and participant privacy',async()=>{
 const s=await setup(),id=await s.create('test');await s.call('alice',{op:'open',roundId:id,segmentId:'segment1'});
 const payload={op:'upload',roundId:id,segmentId:'segment1',chunkIndex:0,anchorMs:50,uncertaintyMs:5,closed:false,events:[event(1,'session_open'),event(2,'question_displayed',{questionIndex:0})]};
 const saved=await s.call('alice',payload);assert.equal(saved.nextSequence,3);const writes=s.store.writes;assert.equal((await s.call('alice',payload)).duplicate,true);assert.equal(s.store.writes,writes);
 await s.call('alice',{...payload,events:[event(1,'disconnect')]},409);await s.call('alice',{...payload,chunkIndex:2},409);await s.call('carol',payload,403);
 await s.call('alice',{...payload,chunkIndex:1,events:[event(3,'session_closed',{chat:'private'})]},400);
 await s.call('alice',{...payload,chunkIndex:1,closed:true,events:[event(3,'session_closed')]});
 for(let i=0;i<3;i++)await s.games.act('alice',id,'answer',{index:i,selectedOption:0});
 const read=await s.call('alice',{op:'read',roundId:id});assert.equal(read.replayStatus,'Partial','missing presentation events cannot claim a complete replay');
 const c=await s.call('alice',{op:'client',roundId:id,segmentId:'segment1',start:0});assert.equal(c.events.length,3);assert.equal(c.events[0].at,1000000+100-50);
 await s.call('carol',{op:'client',roundId:id,segmentId:'segment1',start:0},403);
 await s.call('alice',{op:'client',roundId:id,segmentId:'other_segment',start:0},404);
});
test('Recovered unanchored segment is retained as unaligned, never assigned invented wall time',async()=>{const s=await setup(),id=await s.create('test');await s.call('alice',{op:'open',roundId:id,segmentId:'orphan1'});await s.call('alice',{op:'open',roundId:id,segmentId:'orphan1',clockUncertain:true});await s.call('alice',{op:'upload',roundId:id,segmentId:'orphan1',chunkIndex:0,anchorMs:0,uncertaintyMs:0,closed:true,events:[event(1,'session_closed')]});for(let i=0;i<3;i++)await s.games.act('alice',id,'answer',{index:i,selectedOption:0});const loaded=await loadReplay(id,b=>s.call('alice',b));assert.equal(loaded.status,'Partial');assert.equal(loaded.events.find(e=>e.source==='client').at,null);});
test('Legacy is capability based and rollout does not backfill active rounds',async()=>{const s=await setup(),id=await s.create('test');const game=await s.store.get(`gameSecrets/${id}`);delete game.replayVersion;s.store.docs.set(`gameSecrets/${id}`,game);s.store.docs.set(`games/${id}`,publicGame(game));await s.games.act('alice',id,'answer',{index:0,selectedOption:0});const result=await s.call('alice',{op:'read',roundId:id});assert.equal(result.message,legacyMessage);assert.equal(replayStatus(undefined,true,{},0),'Legacy');});
function replayFixture(){const events=[],add=(type,at,data={},source='client',serverEventId)=>events.push({schemaVersion:1,eventId:`fixture_${events.length}`,roundId:'round',playerId:'alice',source,type,sequence:events.length+1,at,receivedAt:at+20,segmentId:source==='client'?'segment1':undefined,serverEventId,data});
 add('round_start',1000,{startTime:4000,deadline:34000},'server');add('question_displayed',4000,{questionIndex:0});add('selection_changed',4500,{questionIndex:0,selectedOption:1});add('selection_changed',4600,{questionIndex:0,selectedOption:0});add('submission_started',5000,{questionIndex:0});add('answer_accepted',5100,{index:0,selectedOption:0,correct:true,xp:10},'server');const accepted=events.at(-1).eventId;add('feedback_displayed',5200,{questionIndex:0},'client',accepted);add('next',8200,{questionIndex:0});add('question_displayed',8201,{questionIndex:1});add('deadline_changed',9000,{deadline:29000},'server');add('round_end',29000,{status:'finished',logicalEndAt:29000},'server');add('final_result',40000,{receipt:{outcome:'completed'}},'server');return {manifest:{roundId:'round',createdAt:1000,logicalEndAt:29000,settledAt:40000},content:{questions:fixture(),initial:initialState(1000)},events,status:'Available',gaps:[],playerId:'alice'};}
test('Seek equals sequential reduction; playback preserves feedback dwell, deadlines, countdown and delayed settlement',()=>{const data=replayFixture(),compiled=compileReplay(data);for(const at of [1000,2000,3999,4000,5000,5199,5200,8199,8200,29000,40000]){let expected=initialState(1000);for(const event of orderEvents(data.events))if(event.at<=at)expected=reduceEvent(expected,event,'alice');assert.deepEqual(compiled.seek(at),{...expected,at});}assert.equal(compiled.seek(5199).feedbackVisible,false);assert.equal(compiled.seek(5200).feedbackVisible,true);assert.equal(compiled.seek(8200).feedbackVisible,false);assert.equal(originalClock(compiled.seek(2000),2000).countdownMs,2000);assert.equal(originalClock(compiled.seek(40000),40000).elapsedMs,25000);assert.equal(problemEvidence(data,0).feedbackDwellMs,3000);assert.equal(problemEvidence(data,0).totalToSubmitMs,1000);assert.equal(problemEvidence(data,2).exposedAt,null);});
test('Virtual clock is frame independent at all speeds, after background delay and seek',()=>{for(const speed of [.25,.5,1,1.5,2,4,8]){let t=0;const clock=new PlaybackClock(60000,()=>t);clock.speed(speed);clock.play();t=1234;assert.equal(clock.position(),1234*speed);clock.pause();t+=20000;assert.equal(clock.position(),1234*speed);clock.seek(100);clock.play();t+=1000;assert.equal(clock.position(),100+1000*speed);}});
test('Checkpointed long replay has exact seeks and bounded latency',()=>{const data=replayFixture();data.events=Array.from({length:4096},(_,i)=>({...data.events[1],eventId:`long_${i}`,sequence:i+1,at:i*10,data:{questionIndex:i%3}}));const start=performance.now(),compiled=compileReplay(data),build=performance.now()-start;const began=performance.now();for(let i=0;i<100;i++)assert.equal(compiled.seek(i*390).questionIndex,(i*39)%3);const seekMs=performance.now()-began;console.log(JSON.stringify({replayBenchmark:{events:data.events.length,bytes:JSON.stringify(data).length,buildMs:build,oneHundredSeeksMs:seekMs}}));assert.ok(build<2000&&seekMs<2000);});
class MemoryCapture {
 segments=new Map();events=new Map();
 async create(s){this.segments.set(s.key,clone(s));this.events.set(s.key,[]);}
 async append(key,e,view){const s=this.segments.get(key);if(s.closed)throw Error('closed');this.events.get(key).push({...clone(e),sequence:s.nextSequence++});s.lastView=view;if(e.type==='session_closed')s.closed=true;}
 async list(uid){return clone([...this.segments.values()].filter(s=>s.uid===uid));}
 async claim(key,owner,now){const s=this.segments.get(key);if(s.lease&&s.lease.until>now&&s.lease.owner!==owner)return null;s.lease={owner,until:now+60000};return clone(s);}
 async update(s){const fresh=this.segments.get(s.key);assert.equal(fresh.lease.owner,s.lease.owner);for(const k of ['anchorMs','uncertaintyMs','serverAnchorAt','clockUncertain','openSentMs','pending'])fresh[k]=clone(s[k]);}
 async chunk(key,after){return clone(this.events.get(key).filter(e=>e.sequence>after).slice(0,32));}
 async ack(key,owner,nextChunk,nextSequence){const s=this.segments.get(key);assert.equal(s.lease.owner,owner);s.nextChunk=nextChunk;s.ackSequence=nextSequence-1;delete s.pending;this.events.set(key,this.events.get(key).filter(e=>e.sequence>s.ackSequence));}
 async release(key,owner){const s=this.segments.get(key);if(s.lease?.owner===owner)delete s.lease;}
}
test('Durable queue survives response loss and restart, retries immutable chunks, and serializes tabs',async()=>{
 const s=await setup(),id=await s.create('test'),storage=new MemoryCapture();let mono=100,serial=0,lost=true,inflight=0,maxInFlight=0,uploads=[];
 const clock={mono:()=>mono,wall:s.time,uuid:()=>`uuid_${++serial}`};
 const request=async body=>{inflight++;maxInFlight=Math.max(maxInFlight,inflight);try{const result=await s.call('alice',body);if(body.op==='upload'){uploads.push(JSON.stringify(body));if(lost){lost=false;throw Error('response lost AFTER commit');}}return result;}finally{inflight--;}};
 const a=new CaptureQueue(storage,request,clock,'page1'),key=await a.create('alice',id);for(let i=0;i<34;i++){mono+=10;await a.event(key,'selection_changed',{questionIndex:0,selectedOption:i%4});}
 await assert.rejects(a.flush('alice'));assert.equal(storage.events.get(key).length,34);const persisted=clone(storage.segments.get(key).pending);
 const b=new CaptureQueue(storage,request,clock,'page2');await Promise.all([a.flush('alice'),b.flush('alice')]);assert.equal(maxInFlight,1);assert.equal(uploads[0],uploads[1]);assert.equal(JSON.stringify(persisted),uploads[1]);assert.equal(storage.events.get(key).length,2);
 await b.flush('alice');assert.equal(storage.events.get(key).length,0);const summary=await s.store.get(`replayCapture/${id}_alice`);assert.equal(summary.events,34);assert.equal(summary.segments[0].clockUncertain,false);
 const reopened=await b.create('alice',id);await b.event(reopened,'session_open');await b.event(reopened,'session_closed');await b.flush('alice');assert.equal((await s.store.get(`replayCapture/${id}_alice`)).segments.length,2);
});
test('Queue preserves offline events and marks an unanchored orphan instead of inventing an alignment',async()=>{const s=await setup(),id=await s.create('test'),storage=new MemoryCapture();let serial=0;const clock={mono:()=>500,wall:s.time,uuid:()=>`uuid_${++serial}`},q=new CaptureQueue(storage,async()=>{throw Error('offline');},clock,'old_page');const key=await q.create('alice',id);await q.event(key,'question_displayed',{questionIndex:0});await assert.rejects(q.flush('alice'));assert.equal(storage.events.get(key).length,1);const recovered=new CaptureQueue(storage,b=>s.call('alice',b),clock,'new_page');await recovered.flush('alice');assert.equal((await s.store.get(`replayCapture/${id}_alice`)).segments[0].clockUncertain,true);});
test('Missing chunks remain partial and provider failures do not acknowledge queued events',async()=>{const s=await setup(),id=await s.create('test');for(let i=0;i<3;i++)await s.games.act('alice',id,'answer',{index:i,selectedOption:0});s.store.docs.delete(`replayServer/${id}_000001`);const loaded=await loadReplay(id,b=>s.call('alice',b));assert.equal(loaded.status,'Partial');assert.ok(loaded.gaps.some(g=>g.startsWith('Missing server')));const broken=createReplayApi({store:{get:async()=>{throw Error('provider denied');}},verify:async()=>({sub:'alice'})});const response=await broken(new Request('https://ninja.test',{method:'POST',headers:{authorization:'Bearer alice','content-type':'application/json'},body:JSON.stringify({op:'open',roundId:id,segmentId:'segment1'})}));assert.equal(response.status,503);assert.ok(!(await response.json()).acknowledged);});
test('Capture limits are explicit and never delete old round history',async()=>{const s=await setup(),id=await s.create('test');for(let i=0;i<REPLAY_LIMITS.segmentsPerPlayer;i++)await s.call('alice',{op:'open',roundId:id,segmentId:`segment_${i}`});assert.equal((await s.call('alice',{op:'open',roundId:id,segmentId:'over_limit'})).replayStatus,'Partial');assert.ok(await s.store.get(`games/${id}`));assert.equal(replayStatus(1,true,{failed:true,segments:[{closed:true}]},0),'Partial');assert.equal(replayStatus(1,true,{segments:[{closed:false}]},1000,1100),'Syncing');assert.equal(replayStatus(1,true,{segments:[{closed:false}]},1000,200000),'Partial');});

test('Server rejection is recorded once with an unchanged answer/reward state',async()=>{const s=await setup(),id=await s.create('rapid');const before=await s.store.get('users/alice');await assert.rejects(s.games.act('alice',id,'answer',{index:0,selectedOption:1,requestId:'rejected_one'}),e=>e.status===409);const chunk=await s.store.get(`replayServer/${id}_000001`);assert.equal(chunk.events[0].type,'answer_rejected');assert.equal(chunk.events[0].requestId,'rejected_one');await assert.rejects(s.games.act('alice',id,'answer',{index:0,selectedOption:1,requestId:'rejected_one'}));const second=await s.store.get(`replayServer/${id}_000002`);assert.notEqual(second.events[0].eventId,chunk.events[0].eventId);assert.deepEqual(await s.store.get('users/alice'),before);assert.equal(Object.keys((await s.store.get(`gameSecrets/${id}`)).answers).length,0);});
test('Available requires presentation coverage for every accepted answer',()=>{const summary={segments:[{closed:true,events:10,gap:false}],observed:{question_displayed:[0],submission_started:[0],answer_response:[0],feedback_displayed:[0]}};assert.equal(replayStatus(1,true,summary,0,200000,{indices:[0],feedback:true}),'Available');assert.equal(replayStatus(1,true,summary,0,200000,{indices:[0,1],feedback:true}),'Partial');delete summary.observed.feedback_displayed;assert.equal(replayStatus(1,true,summary,0,200000,{indices:[0],feedback:false}),'Available');assert.equal(replayStatus(1,true,summary,0,200000,{indices:[0],feedback:true}),'Partial');});
test('Measure bounded replay overhead for a twenty-question Test round',async()=>{
 const s=await setup(),questions=Array.from({length:20},(_,i)=>({...fixture()[0],problemId:`benchmark_${i}`}));let replayWrites=0;const transact=s.store.transaction.bind(s.store);s.store.transaction=fn=>transact(tx=>fn({...tx,set:(path,value)=>{if(path.startsWith('replay'))replayWrites++;tx.set(path,value);}}));
 const set=await s.games.storeQuestions('alice','test','integration','easy',questions),id=set.questionSetId;await s.games.createGame('alice',id,'test',{});await s.call('alice',{op:'open',roundId:id,segmentId:'benchmark_segment'});
 const events=[];let mono=0;const append=(type,details={})=>events.push(event(events.length+1,type,{...details,monotonicMs:mono+=100}));append('session_open');append('visibility_visible');
 for(let i=0;i<20;i++){append('question_displayed',{questionIndex:i});append('selection_changed',{questionIndex:i,selectedOption:0});append('submission_started',{questionIndex:i});s.advance(1000);const result=await s.games.act('alice',id,'answer',{index:i,selectedOption:0});append('answer_response',{questionIndex:i,serverEventId:result.answer.serverEventId});append('feedback_displayed',{questionIndex:i,serverEventId:result.answer.serverEventId});append('next',{questionIndex:i});}append('result_displayed');append('session_closed');
 for(let start=0,n=0;start<events.length;start+=32,n++)await s.call('alice',{op:'upload',roundId:id,segmentId:'benchmark_segment',chunkIndex:n,anchorMs:0,uncertaintyMs:5,closed:start+32>=events.length,events:events.slice(start,start+32)});
 const documents=[...s.store.docs].filter(([path])=>path.startsWith('replay')),bytes=documents.reduce((n,[,v])=>n+new TextEncoder().encode(JSON.stringify(v)).length,0);let readRequests=0;const started=performance.now(),data=await loadReplay(id,b=>{readRequests++;return s.call('alice',b);}),loadMs=performance.now()-started;
 console.log(JSON.stringify({localReplayOverhead:{questions:20,clientEvents:events.length,serverEvents:data.events.filter(e=>e.source==='server').length,documents:documents.length,jsonBytes:bytes,replayDocumentWrites:replayWrites,loadHttpRequests:readRequests,inMemoryLoadMs:loadMs,providerBilling:'not measured; no production traffic'}}));
 assert.equal(replayWrites,52);assert.equal(readRequests,4);assert.ok(bytes<150000);
});

test('Analysis uses recorded verdicts and excludes unanswered questions and missing timing from aggregates',()=>{
 const data=replayFixture();data.content.questions[1].topic='limits';data.content.questions[2].topic='series';
 const accepted={...data.events.find(e=>e.type==='answer_accepted'),eventId:'accepted_second',at:10000,sequence:40,data:{index:1,selectedOption:2,correct:false,xp:0}};
 data.events.push(accepted,{...accepted,eventId:'score_second',type:'score_progress',sequence:41,data:{scores:{alice:1},progress:{alice:2}}});
 data.events.push({...accepted,source:'client',eventId:'untrusted_verdict',data:{index:2,correct:true,xp:900}});
 const analysis=roundAnalysis(data);assert.equal(analysis.overall.attempted,2);assert.equal(analysis.overall.accuracy,50);assert.equal(analysis.overall.recordedXp,10);assert.equal(analysis.overall.timed,1);assert.equal(analysis.overall.meanExposureToSubmitMs,1000);
 assert.equal(analysis.topics.find(t=>t.topic==='series').accuracy,null);assert.equal(analysis.topics.find(t=>t.topic==='limits').meanExposureToSubmitMs,null);assert.equal(analysis.problems[1].scoreAfter,1);assert.equal(analysis.problems[1].progressAfter,2);
});

test('exposure stages use immutable snapshots; display reports cannot become attempts or renew them',async()=>{
 const s=await setup(),id=await s.create('test');let recent=await s.store.get('bankRecent/alice');assert.ok(recent.exposures.every(e=>e.stage==='issued'));
 await s.call('alice',{op:'open',roundId:id,segmentId:'exposure1'});
 const envelope={op:'upload',roundId:id,segmentId:'exposure1',chunkIndex:0,anchorMs:0,uncertaintyMs:0,closed:false};
 const profileBefore=await s.store.get('users/alice');
 await s.call('alice',{...envelope,events:[event(1,'question_displayed',{questionIndex:2})]});
 recent=await s.store.get('bankRecent/alice');assert.equal(recent.exposures.find(e=>e.problemId===fixture()[2].problemId).stage,'displayed');assert.deepEqual(await s.store.get('users/alice'),profileBefore);
 await s.games.act('alice',id,'answer',{index:0,selectedOption:0});const attempted=(await s.store.get('bankRecent/alice')).exposures.find(e=>e.problemId===fixture()[0].problemId);assert.equal(attempted.stage,'attempted');
 s.advance(1000);await s.call('alice',{...envelope,chunkIndex:1,events:[event(2,'question_displayed',{questionIndex:0})]});assert.deepEqual((await s.store.get('bankRecent/alice')).exposures.find(e=>e.problemId===fixture()[0].problemId),attempted);
 const before=clone([...s.store.docs]);await s.call('alice',{...envelope,chunkIndex:2,events:[event(3,'question_displayed',{questionIndex:19})]},400);assert.deepEqual([...s.store.docs],before);
});
test('source-bound clarifications are separate from immutable replay content and never regrade a recorded answer',async()=>{
 const {readFileSync}=await import('node:fs'),p=JSON.parse(readFileSync(new URL('./fixtures/bank/solution-review-examples.json',import.meta.url)))[0];
 const s=await setup(),q={problemId:p.problemId,problemRevision:p.problemRevision,contentHash:p.contentHash,familyId:p.familyId,bankRelease:'cn-2026-11-03-ideas-v3',latexProblem:p.statement,options:p.choices.map(c=>c.math),correctIndex:p.choices.findIndex(c=>c.choiceId===p.answerChoiceId),explanation:p.solutionSteps,topic:p.topic,difficulty:p.difficulty};
 const set=await s.games.storeQuestions('alice','test',q.topic,q.difficulty,[q]),id=set.questionSetId;await s.games.createGame('alice',id,'test',{});
 const before=await s.store.get(`replayContent/${id}`);await s.call('alice',{op:'read',roundId:id},409);
 const answer=await s.games.act('alice',id,'answer',{index:0,selectedOption:q.correctIndex});assert.equal(answer.answer.correct,true);
 const allBefore=clone([...s.store.docs]),result=await s.call('alice',{op:'read',roundId:id});assert.deepEqual(result.content,before);assert.deepEqual([...s.store.docs],allBefore);
 assert.equal(result.solutionReviews[0].clarified,true);assert.equal(result.solutionReviews[0].sourceContentHash,p.contentHash);assert.equal(result.solutionReviews[0].steps.at(-1),'1');assert.ok(!result.solutionReviews[0].steps.some(s=>s.includes('Here ')));
 const loaded=await loadReplay(id,b=>s.call('alice',b));assert.deepEqual(loaded.content,before);assert.deepEqual(loaded.solutionReviews,result.solutionReviews);
});
