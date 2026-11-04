import {savedSolutionReviews} from './solution-presentation.mjs';
import type {Store,Data} from './firestore-admin.ts';
import {REPLAY_LIMITS,replayStatus,legacyMessage,type ClientEvent,type ReplayEvent} from '../replay/contracts.ts';
import {serverChunkPath} from './replay-recording.ts';
import {readBoundedJson} from './questions-policy.mjs';
import {recordExposures} from '../bank/exposure.ts';
import {displayExposureTime} from '../replay/exposure-time.ts';
const reply=(body:unknown,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
class ReplayError extends Error {status:number;constructor(message:string,status=400){super(message);this.status=status;}}
const id=(s:unknown)=>{if(typeof s!=='string'||!/^[a-zA-Z0-9_-]{5,128}$/.test(s)||['constructor','prototype','__proto__'].includes(s))throw new ReplayError('Invalid replay reference.');return s;};
const expected=(g:Data,uid:string)=>({indices:Object.keys(g.answers?.[uid]||{}).map(Number),feedback:g.mode!=='rapid'});
const terminal=(g:Data)=>['finished','cancelled'].includes(g.status);
const capturePath=(round:string,uid:string)=>`replayCapture/${round}_${uid}`;
const clientPath=(round:string,uid:string,segment:string,n:number)=>`replayClient/${round}_${uid}_${segment}_${String(n).padStart(4,'0')}`;
const allowedTypes=new Set(['session_open','question_displayed','selection_changed','submission_started','submission_rejected','answer_response','feedback_displayed','next','automatic_advance','visibility_hidden','visibility_visible','disconnect','reconnect','page_leave','session_closed','result_displayed','capture_gap']);
const hash=async(v:unknown)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(v)))),x=>x.toString(16).padStart(2,'0')).join('');
function validateEvents(events:unknown,expected:number):ClientEvent[]{
  if(!Array.isArray(events)||!events.length||events.length>REPLAY_LIMITS.eventsPerChunk)throw new ReplayError('Invalid event chunk.');
  if(new TextEncoder().encode(JSON.stringify(events)).length>REPLAY_LIMITS.chunkBytes)throw new ReplayError('Event chunk is too large.');
  let prior=-1;
  for(const e of events){
    if(!e||Object.keys(e).some(k=>!['schemaVersion','eventId','sequence','monotonicMs','type','questionIndex','selectedOption','requestId','serverEventId','reason'].includes(k))||e.schemaVersion!==1||!allowedTypes.has(e.type)||e.sequence!==expected++||!Number.isFinite(e.monotonicMs)||e.monotonicMs<0||e.monotonicMs<prior||e.monotonicMs>7*86400000)throw new ReplayError('Invalid event sequence or schema.');
    id(e.eventId);if(e.requestId!==undefined)id(e.requestId);if(e.serverEventId!==undefined)id(e.serverEventId);
    if(e.questionIndex!==undefined&&(!Number.isInteger(e.questionIndex)||e.questionIndex<0||e.questionIndex>19))throw new ReplayError('Invalid question index.');
    if(e.selectedOption!==undefined&&e.selectedOption!==null&&(!Number.isInteger(e.selectedOption)||e.selectedOption<0||e.selectedOption>3))throw new ReplayError('Invalid selected option.');
    if(e.reason!==undefined&&!['storage-unavailable','storage-full','transport-uncertain','request-rejected','page-unmounted','reload','offline','capture-limit'].includes(e.reason))throw new ReplayError('Invalid event reason.');
    prior=e.monotonicMs;
  }
  return events;
}
export function createReplayApi(deps:{store:Store;verify:(token:string)=>Promise<Data>;now?:()=>number}){
 const now=deps.now||Date.now,store=deps.store;
 return async(request:Request)=>{
  if(request.method!=='POST')return reply({error:'Use POST.'},405);
  if(request.headers.get('origin')&&request.headers.get('origin')!==new URL(request.url).origin||request.headers.get('sec-fetch-site')==='cross-site')return reply({error:'Request origin is not allowed.'},403);
  const bearer=/^Bearer ([^\s]+)$/.exec(request.headers.get('authorization')||'');if(!bearer)return reply({error:'Please sign in.'},401);
  let uid:string;try{uid=id((await deps.verify(bearer[1])).sub);}catch{return reply({error:'Your sign-in has expired.'},401);}
  try{
   const input=await readBoundedJson(request,40000).catch(()=>{throw new ReplayError('Invalid or oversized replay request.');}) as Data;
   if(!input||!['open','upload','read','server','client','statuses'].includes(input.op))throw new ReplayError('Invalid replay operation.');
   if(input.op==='statuses'){
    if(!Array.isArray(input.roundIds)||input.roundIds.length>25)throw new ReplayError('At most 25 history statuses per request.');
    const statuses:Data={};
    for(const value of input.roundIds){const round=id(value),g=await store.get(`games/${round}`);if(!g?.players?.includes(uid))throw new ReplayError('Replay access denied.',403);const summary=g.replayVersion===1?await store.get(capturePath(round,uid)):null;statuses[round]=replayStatus(g.replayVersion,terminal(g),summary,g.finishedAt??null,now(),expected(g,uid));}
    return reply({statuses});
   }
   const round=id(input.roundId),game=await store.get(`games/${round}`);
   if(!game?.players?.includes(uid))throw new ReplayError('Replay access denied.',403);
   if(game.replayVersion!==1)return reply({replayStatus:'Legacy',message:legacyMessage,summary:{mode:game.mode,status:game.status,createdAt:game.createdAt,scores:game.scores,category:game.category,difficulty:game.difficulty}});
   if(input.op==='open'){
    const segmentId=id(input.segmentId),receivedAt=now();
    return reply(await store.transaction(async tx=>{
      const summary=await tx.get(capturePath(round,uid))||{segments:[],events:0,failed:false};
      const existing=summary.segments.find((s:Data)=>s.id===segmentId);if(existing){if(input.clockUncertain===true&&!existing.clockUncertain&&existing.clientAnchorMs===null){existing.clockUncertain=true;summary.failed=true;tx.set(capturePath(round,uid),summary);}return {segment:existing,serverNow:existing.serverAnchorAt};}
      if(summary.segments.length>=REPLAY_LIMITS.segmentsPerPlayer){if(!summary.failed){summary.failed=true;tx.set(capturePath(round,uid),summary);}return {limited:true,replayStatus:'Partial'};}
      const segment={id:segmentId,clockUncertain:input.clockUncertain===true,serverAnchorAt:receivedAt,clientAnchorMs:null,uncertaintyMs:null,nextChunk:0,nextSequence:1,events:0,closed:false,gap:false,lastMono:-1};summary.segments.push(segment);tx.set(capturePath(round,uid),summary);return {segment,serverNow:receivedAt};
    }));
   }
   if(input.op==='upload'){
    const segmentId=id(input.segmentId),chunkIndex=input.chunkIndex;
    if(!Number.isInteger(chunkIndex)||chunkIndex<0||chunkIndex>=REPLAY_LIMITS.chunksPerSegment||typeof input.closed!=='boolean'||!Number.isFinite(input.anchorMs)||input.anchorMs<0||!Number.isFinite(input.uncertaintyMs)||input.uncertaintyMs<0)throw new ReplayError('Invalid capture envelope.');
    const receivedAt=now();const digest=await hash({events:input.events,closed:input.closed,anchorMs:input.anchorMs,uncertaintyMs:input.uncertaintyMs});
    return reply(await store.transaction(async tx=>{
      const summary=await tx.get(capturePath(round,uid));if(!summary)throw new ReplayError('Open a clock segment first.',409);
      const segment=summary.segments.find((s:Data)=>s.id===segmentId);if(!segment)throw new ReplayError('Unknown clock segment.',409);
      const old=await tx.get(clientPath(round,uid,segmentId,chunkIndex));
      if(old){if(old.hash!==digest)throw new ReplayError('Chunk identity conflict.',409);return {acknowledged:true,nextChunk:segment.nextChunk,nextSequence:segment.nextSequence,duplicate:true};}
      if(segment.closed||chunkIndex!==segment.nextChunk)throw new ReplayError(`Sequence gap: expected chunk ${segment.nextChunk}.`,409);
      const events=validateEvents(input.events,segment.nextSequence);
      if(events[0].monotonicMs<segment.lastMono||segment.clientAnchorMs!==null&&(segment.clientAnchorMs!==input.anchorMs||segment.uncertaintyMs!==input.uncertaintyMs))throw new ReplayError('Clock segment conflict.',409);
      if(summary.events+events.length>REPLAY_LIMITS.eventsPerPlayer){if(!summary.failed){summary.failed=true;tx.set(capturePath(round,uid),summary);}return {limited:true,replayStatus:'Partial'};}
      if(input.closed&&events.at(-1)?.type!=='session_closed')throw new ReplayError('Missing segment closure.');
      const displayed=events.filter(e=>e.type==='question_displayed'&&e.questionIndex!==undefined);
      // Only map reports to this member's immutable server snapshot. Client
      // reports never award XP, calibrate difficulty, or become attempts.
      const privateGame=displayed.length?await tx.get(`gameSecrets/${round}`):null;
      const recent=privateGame?await tx.get(`bankRecent/${uid}`)||{}:null;
      if(privateGame&&displayed.some(e=>!privateGame.questions?.[e.questionIndex!]))throw new ReplayError('Invalid displayed question.');
      summary.observed ||= {};for(const event of events)if(event.questionIndex!==undefined){const seen=summary.observed[event.type]||[];if(!seen.includes(event.questionIndex))summary.observed[event.type]=[...seen,event.questionIndex];}
      segment.clientAnchorMs=input.anchorMs;segment.uncertaintyMs=input.uncertaintyMs;segment.nextChunk++;segment.nextSequence+=events.length;segment.events+=events.length;segment.closed=input.closed;segment.lastMono=events.at(-1)!.monotonicMs;segment.gap ||= segment.clockUncertain||events.some(e=>e.type==='capture_gap');summary.failed ||= segment.gap;summary.events+=events.length;
      tx.set(clientPath(round,uid,segmentId,chunkIndex),{roundId:round,playerId:uid,segmentId,chunkIndex,hash:digest,receivedAt,events});tx.set(capturePath(round,uid),summary);
      if(privateGame&&recent){
       let history=recent;
       for(const event of displayed){
        const at=displayExposureTime(segment,event,input.anchorMs,input.uncertaintyMs,privateGame,receivedAt);
        if(at!==null)history=recordExposures(history,round,[privateGame.questions[event.questionIndex!]],'displayed',at,receivedAt);
       }
       tx.set(`bankRecent/${uid}`,history);
      }
      return {acknowledged:true,nextChunk:segment.nextChunk,nextSequence:segment.nextSequence};
    }));
   }
   // Every content/chunk endpoint repeats the match-level gate, including an early finisher.
   if(!terminal(game))return reply({replayStatus:'Recording',locked:true,message:'Replay and analysis unlock after the entire match ends.'},409);
   const manifest=await store.get(`replayManifests/${round}`),capture=await store.get(capturePath(round,uid));
   if(!manifest)return reply({replayStatus:'Unavailable',message:'Replay metadata is unavailable.'});
   const status=replayStatus(1,true,capture,manifest.settledAt,now(),expected(game,uid));
   if(input.op==='read'){
    const content=await store.get(`replayContent/${round}`);if(!content)return reply({replayStatus:'Unavailable',message:'The immutable replay snapshot is unavailable.'});
    const gaps:string[]=[];if(!capture?.segments?.length)gaps.push('Client presentation was not synchronized.');
    if(capture?.failed)gaps.push('Capture reported missing or rejected local events.');
    if(capture?.segments?.some((s:Data)=>!s.closed))gaps.push('One or more page sessions have no durable closing event.');
    if(status==='Partial'&&!gaps.length)gaps.push('Some accepted answers are missing captured exposure, submission, response, or feedback events.');
    if(content.contextMissing)gaps.push('Some problem context was absent from the captured snapshot.');
    return reply({replayStatus:content.contextMissing?'Partial':status,manifest,content,solutionReviews:savedSolutionReviews(content.questions),playerId:uid,segments:capture?.segments||[],gaps});
   }
   if(input.op==='server'){
    const start=input.start;if(!Number.isInteger(start)||start<0||start>manifest.chunkCount)throw new ReplayError('Invalid replay cursor.');
    const chunks=[],missing=[];
    for(let n=start;n<Math.min(start+REPLAY_LIMITS.readChunks,manifest.chunkCount);n++){
      const c=await store.get(serverChunkPath(round,n));if(!c){missing.push(n);continue;}
      // Opponent selections, verdict details, request IDs and client traces are private.
      c.events=c.events.filter((e:ReplayEvent)=>!['answer_accepted','answer_rejected'].includes(e.type)||e.playerId===uid).map((e:ReplayEvent)=>e.playerId===uid?e:{...e,requestId:undefined});chunks.push(c);
    }
    return reply({chunks,missing,next:Math.min(start+REPLAY_LIMITS.readChunks,manifest.chunkCount),done:start+REPLAY_LIMITS.readChunks>=manifest.chunkCount});
   }
   const segmentId=id(input.segmentId),segment=capture?.segments.find((s:Data)=>s.id===segmentId);if(!segment)throw new ReplayError('Capture segment unavailable.',404);
   const start=input.start;if(!Number.isInteger(start)||start<0||start>segment.nextChunk)throw new ReplayError('Invalid replay cursor.');
   const events:ReplayEvent[]=[],missing=[];
   for(let n=start;n<Math.min(start+REPLAY_LIMITS.readChunks,segment.nextChunk);n++){
    const c=await store.get(clientPath(round,uid,segmentId,n));if(!c){missing.push(n);continue;}
    for(const e of c.events as ClientEvent[])events.push({schemaVersion:1,eventId:e.eventId,roundId:round,playerId:uid,source:'client',type:e.type,sequence:e.sequence,at:segment.clockUncertain?null:segment.serverAnchorAt+e.monotonicMs-segment.clientAnchorMs,receivedAt:c.receivedAt,segmentId,monotonicMs:e.monotonicMs,uncertaintyMs:segment.uncertaintyMs,requestId:e.requestId,serverEventId:e.serverEventId,data:{questionIndex:e.questionIndex,selectedOption:e.selectedOption,reason:e.reason}});
   }
   return reply({events,missing,next:Math.min(start+REPLAY_LIMITS.readChunks,segment.nextChunk),done:start+REPLAY_LIMITS.readChunks>=segment.nextChunk});
  }catch(error){return error instanceof ReplayError?reply({error:error.message},error.status):reply({error:'Replay storage is unavailable. Captured local events will remain queued.'},503);}
 };
}
