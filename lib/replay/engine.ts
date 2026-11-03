import type {ReplayData,ReplayEvent,ReplayState} from './contracts.ts';
export function initialState(at=0):ReplayState{return {at,status:'waiting',questionIndex:null,selectedOption:null,submission:'idle',feedbackVisible:false,feedbackIndex:null,visible:null,connected:null,scores:{},progress:{},startTime:null,deadline:null,logicalEndAt:null,result:null,gap:false,accepted:{}};}
export function orderEvents(events:ReplayEvent[]){return events.filter(e=>e.at!==null).sort((a,b)=>a.at!-b.at!||(a.source===b.source?0:a.source==='server'?-1:1)||(a.source==='server'?a.sequence-b.sequence:(a.segmentId||'').localeCompare(b.segmentId||'')||a.sequence-b.sequence)||a.eventId.localeCompare(b.eventId));}
export function reduceEvent(previous:ReplayState,event:ReplayEvent,playerId:string):ReplayState {
  const s={...previous,at:event.at!},d=event.data;
  if(event.source==='server'){
    if(event.type==='round_created'){s.status=d.status;s.scores={...d.scores};s.progress={...d.progress};}
    if(event.type==='countdown_start'){s.startTime=d.startTime;s.deadline=d.deadline??null;}
    if(event.type==='round_start'){s.status='active';s.startTime=d.startTime;s.deadline=d.deadline??null;}
    if(event.type==='answer_accepted'&&event.playerId===playerId){s.accepted={...s.accepted,[d.index]:{selectedOption:d.selectedOption,correct:d.correct,xp:d.xp,serverEventId:event.eventId,at:event.at!}};s.submission='accepted';}
    if(event.type==='score_progress'){s.scores={...d.scores};s.progress={...d.progress};}
    if(event.type==='deadline_changed')s.deadline=d.deadline;
    if(event.type==='round_end'){s.status=d.status;s.logicalEndAt=d.logicalEndAt;s.result=d.result||null;}
    if(event.type==='final_result'&&event.playerId===playerId)s.result=d.receipt;
    return s;
  }
  if(event.playerId!==playerId)return s;
  if(event.type==='question_displayed'){s.questionIndex=d.questionIndex;s.selectedOption=null;s.feedbackVisible=false;s.feedbackIndex=null;s.submission='idle';}
  if(event.type==='selection_changed'){s.selectedOption=d.selectedOption;}
  if(event.type==='submission_started')s.submission='pending';
  if(event.type==='submission_rejected')s.submission='rejected';
  if(event.type==='feedback_displayed'){
    const a=s.accepted[d.questionIndex];
    // Only a captured display linked to the accepted server event reveals a solution.
    if(a&&a.serverEventId===event.serverEventId){s.feedbackVisible=true;s.feedbackIndex=d.questionIndex;s.selectedOption=a.selectedOption;s.submission='accepted';}
    else s.gap=true;
  }
  if(event.type==='next'||event.type==='automatic_advance'){s.feedbackVisible=false;s.feedbackIndex=null;s.selectedOption=null;s.submission='idle';s.questionIndex=null;}
  if(event.type==='visibility_visible')s.visible=true;
  if(event.type==='visibility_hidden'||event.type==='page_leave')s.visible=false;
  if(event.type==='disconnect')s.connected=false;
  if(event.type==='reconnect'||event.type==='session_open')s.connected=true;
  if(event.type==='capture_gap')s.gap=true;
  return s;
}
export function compileReplay(data:ReplayData){
  const events=orderEvents(data.events),checkpoints:{index:number;at:number;state:ReplayState}[]=[];
  let state=structuredClone(data.content.initial);checkpoints.push({index:0,at:-Infinity,state:structuredClone(state)});
  events.forEach((event,i)=>{state=reduceEvent(state,event,data.playerId);if((i+1)%64===0)checkpoints.push({index:i+1,at:event.at!,state:structuredClone(state)});});
  const origin=Math.min(data.manifest.createdAt,...events.map(e=>e.at!));
  const end=Math.max(data.manifest.logicalEndAt??origin,...events.map(e=>e.at!));
  return {events,checkpoints,origin,end,duration:Math.max(0,end-origin),seek(at:number){let c=checkpoints[0];for(const candidate of checkpoints){if(candidate.at<=at)c=candidate;else break;}let s=structuredClone(c.state);for(let i=c.index;i<events.length&&events[i].at!<=at;i++)s=reduceEvent(s,events[i],data.playerId);return {...s,at};}};
}
export function originalClock(state:ReplayState,at:number){const effective=state.logicalEndAt===null?at:Math.min(at,state.logicalEndAt);return {elapsedMs:state.startTime===null?null:Math.max(0,effective-state.startTime),countdownMs:state.startTime===null?null:Math.max(0,state.startTime-at),remainingMs:state.deadline===null?null:Math.max(0,state.deadline-Math.max(state.startTime??0,effective))};}
export function problemEvidence(data:ReplayData,index:number){
  const events=orderEvents(data.events).filter(e=>e.source==='client'&&e.playerId===data.playerId);
  const exposure=events.filter(e=>e.type==='question_displayed'&&e.data.questionIndex===index),submission=events.find(e=>e.type==='submission_started'&&e.data.questionIndex===index),feedback=events.find(e=>e.type==='feedback_displayed'&&e.data.questionIndex===index);
  const next=feedback?events.find(e=>e.at!>=feedback.at!&&['next','automatic_advance'].includes(e.type)&&e.data.questionIndex===index):undefined;
  const accepted=data.events.find(e=>e.source==='server'&&e.type==='answer_accepted'&&e.playerId===data.playerId&&e.data.index===index);
  // Only closed visible intervals count. Open spans, clock-segment changes, or
  // missing events remain unknown instead of becoming fabricated solve times.
  let visibleMs=0,open:ReplayEvent|undefined,uncertain=false;
  for(const e of events){if(e.type==='question_displayed'&&e.data.questionIndex===index)open=e;else if(open&&['visibility_hidden','page_leave','submission_started','question_displayed','capture_gap'].includes(e.type)){if(e.segmentId!==open.segmentId||e.type==='capture_gap')uncertain=true;else visibleMs+=Math.max(0,e.at!-open.at!);open=undefined;}}
  if(open)uncertain=true;
  return {exposedAt:exposure[0]?.at??null,submissionAt:submission?.at??null,acceptedAt:accepted?.at??null,feedbackAt:feedback?.at??null,feedbackDwellMs:feedback&&next&&feedback.segmentId===next.segmentId?Math.max(0,next.at!-feedback.at!):null,visibleExposureMs:exposure.length&&!uncertain?visibleMs:null,totalToSubmitMs:exposure[0]&&submission&&exposure[0].segmentId===submission.segmentId?Math.max(0,submission.at!-exposure[0].at!):null,answer:accepted?.data??null};
}
