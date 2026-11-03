import {REPLAY_LIMITS,type ClientEvent,type ClientEventType} from './contracts.ts';
export interface CaptureSegment {key:string;uid:string;roundId:string;segmentId:string;pageId:string;nextSequence:number;nextChunk:number;ackSequence:number;closed:boolean;anchorMs:number|null;uncertaintyMs:number;serverAnchorAt:number|null;clockUncertain:boolean;openSentMs?:number;lease?:{owner:string;until:number};pending?:any;lastView?:any;updatedAt?:number;failed?:boolean}
export interface CaptureStorage {create(segment:CaptureSegment):Promise<void>;append(key:string,event:Omit<ClientEvent,'sequence'>,view?:any):Promise<void>;list(uid:string):Promise<CaptureSegment[]>;claim(key:string,owner:string,now:number):Promise<CaptureSegment|null>;update(segment:CaptureSegment):Promise<void>;chunk(key:string,after:number):Promise<ClientEvent[]>;ack(key:string,owner:string,nextChunk:number,nextSequence:number):Promise<void>;release(key:string,owner:string):Promise<void>}
const asPromise=<T>(request:IDBRequest<T>)=>new Promise<T>((resolve,reject)=>{request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});
let connection:Promise<IDBDatabase>|undefined;
function database(){return connection ||= new Promise<IDBDatabase>((resolve,reject)=>{const r=indexedDB.open('calculus-ninja-replay-v1',1);r.onupgradeneeded=()=>{r.result.createObjectStore('segments',{keyPath:'key'});r.result.createObjectStore('events',{keyPath:['segmentKey','sequence']});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>{connection=undefined;reject(r.error);};r.onblocked=()=>{connection=undefined;reject(Error('Replay local storage is blocked.'));};});}
async function transaction<T>(stores:string[],fn:(tx:IDBTransaction)=>Promise<T>){const db=await database(),tx=db.transaction(stores,'readwrite',{durability:'strict'});const done=new Promise<void>((resolve,reject)=>{tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||Error('Local recording was not committed.'));});try{const value=await fn(tx);await done;return value;}catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}}
export const indexedCaptureStorage:CaptureStorage={
 async create(segment){await transaction(['segments'],async tx=>{tx.objectStore('segments').add(segment);});},
 async append(key,event,view){await transaction(['segments','events'],async tx=>{const store=tx.objectStore('segments'),s=await asPromise(store.get(key)) as CaptureSegment;if(!s||s.closed)throw Error('Capture segment is closed.');if(s.nextSequence>REPLAY_LIMITS.eventsPerPlayer){throw Error('Local capture limit reached.');}tx.objectStore('events').add({...event,segmentKey:key,sequence:s.nextSequence++});if(view)s.lastView=view;s.updatedAt=Date.now();if(event.type==='session_closed')s.closed=true;store.put(s);});},
 async list(uid){const db=await database();return (await asPromise(db.transaction('segments').objectStore('segments').getAll()) as CaptureSegment[]).filter(s=>s.uid===uid);},
 async claim(key,owner,now){return transaction(['segments'],async tx=>{const store=tx.objectStore('segments'),s=await asPromise(store.get(key)) as CaptureSegment;if(!s||s.lease&&s.lease.until>now&&s.lease.owner!==owner)return null;s.lease={owner,until:now+60000};store.put(s);return s;});},
 async update(segment){await transaction(['segments'],async tx=>{const store=tx.objectStore('segments'),fresh=await asPromise(store.get(segment.key)) as CaptureSegment;if(!fresh||fresh.lease?.owner!==segment.lease?.owner)throw Error('Capture lease changed.');store.put({...fresh,anchorMs:segment.anchorMs,uncertaintyMs:segment.uncertaintyMs,serverAnchorAt:segment.serverAnchorAt,clockUncertain:segment.clockUncertain,openSentMs:segment.openSentMs,pending:segment.pending});});},
 async chunk(key,after){const db=await database();const rows=await asPromise(db.transaction('events').objectStore('events').getAll(IDBKeyRange.bound([key,after+1],[key,Number.MAX_SAFE_INTEGER]),REPLAY_LIMITS.eventsPerChunk));return rows.map(({segmentKey:_segmentKey,...event})=>event) as ClientEvent[];},
 async ack(key,owner,nextChunk,nextSequence){await transaction(['segments','events'],async tx=>{const store=tx.objectStore('segments'),s=await asPromise(store.get(key)) as CaptureSegment;if(s.lease?.owner!==owner)throw Error('Capture lease changed.');s.nextChunk=nextChunk;s.ackSequence=nextSequence-1;delete s.pending;store.put(s);tx.objectStore('events').delete(IDBKeyRange.bound([key,0],[key,s.ackSequence]));});},
 async release(key,owner){await transaction(['segments'],async tx=>{const store=tx.objectStore('segments'),s=await asPromise(store.get(key)) as CaptureSegment;if(s?.lease?.owner===owner){delete s.lease;store.put(s);}});}
};
export class CaptureQueue {
 readonly pageId:string;readonly owner:string;private running=false;
 readonly storage:CaptureStorage;readonly request:(input:any)=>Promise<any>;readonly clock:{mono:()=>number;wall:()=>number;uuid:()=>string};
 constructor(storage:CaptureStorage,request:(input:any)=>Promise<any>,clock:{mono:()=>number;wall:()=>number;uuid:()=>string},pageId?:string){this.storage=storage;this.request=request;this.clock=clock;this.pageId=pageId||clock.uuid();this.owner=clock.uuid();}
 async create(uid:string,roundId:string){const segmentId=this.clock.uuid(),key=`${uid}:${roundId}:${segmentId}`;await this.storage.create({key,uid,roundId,segmentId,pageId:this.pageId,nextSequence:1,nextChunk:0,ackSequence:0,closed:false,anchorMs:null,uncertaintyMs:0,serverAnchorAt:null,clockUncertain:false});return key;}
 event(key:string,type:ClientEventType,data:Partial<ClientEvent>={},view?:any){return this.storage.append(key,{schemaVersion:1,eventId:this.clock.uuid(),monotonicMs:this.clock.mono(),type,...data},view);}
 async flush(uid:string){
  if(this.running)return;this.running=true;
  try{for(const listed of await this.storage.list(uid)){
   if(listed.ackSequence>=listed.nextSequence-1)continue;
   const s=await this.storage.claim(listed.key,this.owner,this.clock.wall());if(!s)continue;
   try{
    if(s.anchorMs===null){
     s.openSentMs??=this.clock.mono();s.clockUncertain=s.pageId!==this.pageId;await this.storage.update(s);
     const anchor=await this.request({op:'open',roundId:s.roundId,segmentId:s.segmentId,clockUncertain:s.clockUncertain});if(anchor.limited)throw Error('Recording limit reached; replay is partial.');
     const end=this.clock.mono();s.anchorMs=s.clockUncertain?0:(s.openSentMs+end)/2;s.uncertaintyMs=s.clockUncertain?0:Math.max(0,(end-s.openSentMs)/2);s.serverAnchorAt=anchor.serverNow;await this.storage.update(s);
    }
    // At most one immutable chunk per segment per sweep. A persisted pending
    // envelope is replayed byte-for-byte after a lost response or process reload.
    let payload=s.pending;
    if(!payload){const events=await this.storage.chunk(s.key,s.ackSequence);if(!events.length)continue;payload={op:'upload',roundId:s.roundId,segmentId:s.segmentId,chunkIndex:s.nextChunk,events,closed:events.at(-1)!.type==='session_closed',anchorMs:s.anchorMs,uncertaintyMs:s.uncertaintyMs};s.pending=payload;await this.storage.update(s);}
    const ack=await this.request(payload);if(!ack.acknowledged||ack.limited)throw Error('Recording could not synchronize; captured events remain local.');
    await this.storage.ack(s.key,this.owner,ack.nextChunk,ack.nextSequence);
   }finally{await this.storage.release(s.key,this.owner);}
  }}finally{this.running=false;}
 }
}
