'use client';
import {useAuth} from './AuthProvider';
import {usePathname} from 'next/navigation';
import {useEffect,useRef,useState} from 'react';
import {apiRequest} from '@/lib/game-session';
import {CaptureQueue,indexedCaptureStorage} from '@/lib/replay/queue';
import {registerCapture,observeReplay} from '@/lib/replay/browser-events';
import type {ClientEvent,ClientEventType} from '@/lib/replay/contracts';
let queue:CaptureQueue|undefined;
const getQueue=()=>queue ||= new CaptureQueue(indexedCaptureStorage,input=>apiRequest('replay',input),{mono:()=>performance.now(),wall:()=>Date.now(),uuid:()=>crypto.randomUUID()});
export interface CaptureView {index:number|null;feedbackIndex:number|null;serverEventId?:string;selectedOption:number|null;finished:boolean;settled?:boolean}
export function useReplayCapture(uid:string|undefined,round:string|null,version:unknown,view:CaptureView,captureQueue?:CaptureQueue){
 const [status,setStatus]=useState('Recording'),[revision,setRevision]=useState(0);
 const current=useRef(view);current.current=view;
 const emitter=useRef<((type:ClientEventType,data?:Partial<ClientEvent>)=>void)|null>(null);
 useEffect(()=>{
  if(!uid||!round||version!==1)return;
  const q=captureQueue||getQueue();let active=true,closed=false,chain:Promise<unknown>=q.create(uid,round),key='',retryAt=0,failures=0,broken=false,reportedFinal=false;
  chain=chain.then(k=>{key=k as string;});
  const emit=(type:ClientEventType,data:Partial<ClientEvent>={})=>{
   if(closed)return;const monotonicMs=performance.now(),snapshot={...current.current};if(type==='next'||type==='automatic_advance'){snapshot.index=(data.questionIndex??snapshot.index??-1)+1;snapshot.feedbackIndex=null;snapshot.selectedOption=null;}if(type==='selection_changed')snapshot.selectedOption=data.selectedOption??null;if(type==='session_closed')closed=true;
   chain=chain.then(async()=>{if(broken){await q.event(key,'capture_gap',{reason:'storage-unavailable',monotonicMs});}await q.event(key,type,{...data,monotonicMs},snapshot);}).catch(()=>{broken=true;if(active)setStatus('Partial — local capture could not be saved. Gameplay is unaffected.');});
  };
  previous.current={round:null,index:null,feedback:null,finished:false};emitter.current=emit;const unregister=registerCapture(round,emit);
  emit('session_open');emit(document.hidden?'visibility_hidden':'visibility_visible');
  const flush=async()=>{if(reportedFinal||Date.now()<retryAt||!navigator.onLine)return;try{await chain;await q.flush(uid);failures=0;const pending=(await q.storage.list(uid)).some(s=>s.roundId===round&&s.ackSequence<s.nextSequence-1);if(active){if(closed&&!pending){const result=await q.request({op:'statuses',roundIds:[round]});if(active)setStatus(broken?'Partial':result.statuses[round]);reportedFinal=['Available','Partial','Unavailable','Legacy'].includes(result.statuses[round]);}else setStatus(broken?'Partial':pending?'Syncing':'Recording');}}catch{failures++;retryAt=Date.now()+Math.min(60000,2000*2**Math.min(5,failures));if(active)setStatus('Syncing — events remain queued on this device.');}};
  const visibility=()=>{emit(document.hidden?'visibility_hidden':'visibility_visible');if(!document.hidden){const v=current.current;if(v.index!==null){emit('question_displayed',{questionIndex:v.index});if(v.selectedOption!==null)emit('selection_changed',{questionIndex:v.index,selectedOption:v.selectedOption});}if(v.feedbackIndex!==null)emit('feedback_displayed',{questionIndex:v.feedbackIndex,serverEventId:v.serverEventId});}void flush();};
  const offline=()=>emit('disconnect',{reason:'offline'}),online=()=>{emit('reconnect');retryAt=0;void flush();},leave=()=>{emit('page_leave');void flush();};
  document.addEventListener('visibilitychange',visibility);window.addEventListener('offline',offline);window.addEventListener('online',online);window.addEventListener('pagehide',leave);
  const interval=setInterval(flush,2500);setRevision(n=>n+1);void flush();
  return()=>{active=false;unregister();emitter.current=null;emit('page_leave',{reason:'page-unmounted'});emit('session_closed');void flush();clearInterval(interval);document.removeEventListener('visibilitychange',visibility);window.removeEventListener('offline',offline);window.removeEventListener('online',online);window.removeEventListener('pagehide',leave);};
 },[uid,round,version,captureQueue]);
 const previous=useRef<{round:string|null;index:number|null;feedback:string|null;finished:boolean;closed?:boolean}>({round:null,index:null,feedback:null,finished:false});
 useEffect(()=>{
  if(!round||version!==1||!emitter.current)return;
  const emit=emitter.current,p=previous.current;if(p.round!==round){p.round=round;p.index=null;p.feedback=null;p.finished=false;}
  if(view.index!==null&&view.index!==p.index&&!document.hidden)emit('question_displayed',{questionIndex:view.index});p.index=view.index;
  const feedback=view.feedbackIndex!==null?`${view.feedbackIndex}:${view.serverEventId}`:null;
  if(feedback&&feedback!==p.feedback&&!document.hidden)emit('feedback_displayed',{questionIndex:view.feedbackIndex!,serverEventId:view.serverEventId});p.feedback=feedback;
  if(view.finished&&!p.finished)emit('result_displayed');p.finished=view.finished;if(view.finished&&view.settled!==false&&!p.closed){emit('session_closed');p.closed=true;}
 },[round,version,view.index,view.feedbackIndex,view.serverEventId,view.finished,view.settled,revision]);
 return version===1?status:version===undefined?'':'Legacy';
}
export function ReplayCaptureStatus({status}:{status:string}){return status?<p className="my-2 text-xs text-zinc-400" role="status">Replay: {status}</p>:null;}
export {observeReplay};
/** A stored round is resumable without creating a replacement or new question set. */
export function useRoundUrl(uid:string|undefined,round:string|null,restore:(id:string)=>void){
 const initialized=useRef(false),previousRound=useRef<string|null>(null),callback=useRef(restore);callback.current=restore;
 useEffect(()=>{if(!uid||initialized.current)return;initialized.current=true;const id=new URLSearchParams(location.search).get('round');if(id&&/^[a-zA-Z0-9]{5,30}$/.test(id))callback.current(id);},[uid]);
 useEffect(()=>{if(!round){if(previousRound.current){clearRoundUrl();previousRound.current=null;}return;}previousRound.current=round;const url=new URL(location.href);url.searchParams.delete('join');url.searchParams.set('round',round);history.replaceState(null,'',url);},[round]);
}

export async function capturedView(uid:string,roundId:string){try{const segments=await indexedCaptureStorage.list(uid);return segments.filter(s=>s.roundId===roundId&&s.lastView).sort((a,b)=>(b.updatedAt||0)-(a.updatedAt||0))[0]?.lastView as CaptureView|undefined;}catch{return undefined;}}

export function ReplayQueueSync(){
 const {user}=useAuth(),path=usePathname();const [error,setError]=useState(false);
 useEffect(()=>{if(!user||path.startsWith('/replay/'))return;let stopped=false,failures=0,retryAt=0;const flush=async()=>{if(!navigator.onLine||Date.now()<retryAt)return;try{await getQueue().flush(user.uid);failures=0;if(!stopped)setError(false);}catch{failures++;retryAt=Date.now()+Math.min(60000,2000*2**Math.min(5,failures));if(!stopped)setError(true);}};void flush();const timer=setInterval(flush,5000);window.addEventListener('online',flush);return()=>{stopped=true;clearInterval(timer);window.removeEventListener('online',flush);};},[user?.uid,path]);
 return error&&!path.startsWith('/replay/')?<p role="status" className="border-b border-amber-500/20 px-4 py-2 text-center text-xs text-amber-200">Some replay events remain queued on this device. Synchronization will retry; saved game results are unaffected.</p>:null;
}

export function clearRoundUrl(){const url=new URL(location.href);url.searchParams.delete('round');history.replaceState(null,'',url);}
