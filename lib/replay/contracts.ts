import type {GameQuestion, ResultReceipt} from '../game-progress.ts';
export const REPLAY_VERSION = 1 as const;
export const RULES_VERSION = 'progression-3-bank-1' as const;
export const REPLAY_LIMITS = {eventsPerChunk:32, chunkBytes:24000, segmentsPerPlayer:32, chunksPerSegment:128, eventsPerPlayer:4096, readChunks:16} as const;
export type ReplayStatus = 'Recording'|'Syncing'|'Available'|'Partial'|'Unavailable'|'Legacy';
export type ClientEventType = 'session_open'|'question_displayed'|'selection_changed'|'submission_started'|'submission_rejected'|'answer_response'|'feedback_displayed'|'next'|'automatic_advance'|'visibility_hidden'|'visibility_visible'|'disconnect'|'reconnect'|'page_leave'|'session_closed'|'result_displayed'|'capture_gap';
export type ServerEventType = 'round_created'|'participant_joined'|'participant_left'|'countdown_start'|'round_start'|'answer_accepted'|'answer_rejected'|'score_progress'|'deadline_changed'|'round_end'|'final_result';
export interface ReplayEvent {
  schemaVersion:1; eventId:string; roundId:string; playerId:string; source:'server'|'client'; type:ClientEventType|ServerEventType;
  sequence:number; at:number|null; receivedAt:number; segmentId?:string; monotonicMs?:number; uncertaintyMs?:number;
  requestId?:string; serverEventId?:string; data:Record<string,any>;
}
export interface ClientEvent {
  schemaVersion:1; eventId:string; sequence:number; monotonicMs:number; type:ClientEventType;
  questionIndex?:number; selectedOption?:number|null; requestId?:string; serverEventId?:string; reason?:string;
}
export interface ReplayManifest {
  replayVersion:1; roundId:string; mode:string; settings:Record<string,any>; participants:string[]; appVersion:string; rulesVersion:string;
  bankReleases:string[]; createdAt:number; startTime:number|null; deadline:number|null; logicalEndAt:number|null; settledAt:number|null;
  endReason:string|null; status:string; sequence:number; chunkCount:number; questionCount:number; scores:Record<string,number>;
  progress:Record<string,number>; receipts:Record<string,ResultReceipt>;
}
export interface ReplayContent {questions:GameQuestion[]; initial:ReplayState; contextMissing:boolean}
export interface ReplayState {
  at:number; status:string; questionIndex:number|null; selectedOption:number|null; submission:'idle'|'pending'|'accepted'|'rejected';
  feedbackVisible:boolean; feedbackIndex:number|null; visible:boolean|null; connected:boolean|null; scores:Record<string,number>; progress:Record<string,number>;
  startTime:number|null; deadline:number|null; logicalEndAt:number|null; result:Record<string,any>|null; gap:boolean;
  accepted:Record<string,{selectedOption:number;correct:boolean;xp:number;serverEventId:string;at:number}>;
}
export interface ReplayData {manifest:ReplayManifest;content:ReplayContent;events:ReplayEvent[];status:ReplayStatus;gaps:string[];playerId:string}
export const replayStatus = (capability:unknown,terminal:boolean,summary:any,settledAt:number|null,now=Date.now(),expected?:{indices:number[];feedback:boolean}):ReplayStatus => {
  if(capability!==1)return 'Legacy';
  if(!terminal)return summary?.failed?'Partial':'Recording';
  if(!summary?.segments?.length)return settledAt!==null&&now-settledAt<120000?'Syncing':'Partial';
  if(summary.failed)return 'Partial';
  if(summary.segments.some((s:any)=>!s.closed))return settledAt!==null&&now-settledAt<120000?'Syncing':'Partial';
  if(expected?.indices.some(i=>!['question_displayed','submission_started','answer_response',...(expected.feedback?['feedback_displayed']:[])].every(t=>summary.observed?.[t]?.includes(i))))return 'Partial';
  return summary.segments.every((s:any)=>s.events>0&&!s.gap)?'Available':'Partial';
};
export const legacyMessage = 'Legacy — replay was not recorded for this round.';
