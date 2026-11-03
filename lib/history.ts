import {execute,field,and,or,constant,switchOn,timestampToUnixMillis} from 'firebase/firestore/pipelines';
import type {Firestore} from 'firebase/firestore';
export const HISTORY_PAGE_SIZE=25;
export interface HistoryFilters {mode?:string;from?:string;to?:string;topic?:string;difficulty?:string;result?:string;replay?:string}
export type HistoryRow=Record<string,any>&{id:string};
export type HistoryCursor=Record<string,{value:unknown;id:string}>;
export function historyDate(value:any):number|null{
 let n:number;
 if(value?.toMillis)n=value.toMillis();else if(value instanceof Date)n=value.getTime();else if(typeof value==='string')n=Date.parse(value);else if(typeof value==='number')n=Math.abs(value)<100000000000?value*1000:value;else if(value&&typeof(value.seconds??value._seconds)==='number')n=(value.seconds??value._seconds)*1000+(value.nanoseconds??value._nanoseconds??0)/1000000;else return null;
 return Number.isFinite(n)?n:null;
}
// Stable keyset cursors for each historical encoding. Filters run in Firestore
// BEFORE page limits. No mutation, retention cap, or automatic history deletion.
export async function loadHistoryPage(db:Firestore,uid:string,filters:HistoryFilters={},cursor:HistoryCursor={}):Promise<{rows:HistoryRow[];cursor:HistoryCursor;hasMore:boolean}>{
 const created=field('createdAt'),kind=created.ifAbsent(null).type(),docId=field('__name__').documentId();
 const number=or(kind.equal('int64'),kind.equal('float64')),map=kind.equal('map');
 const seconds=field('createdAt.seconds').ifAbsent(field('createdAt._seconds')).ifAbsent(-8640000000000);
 const numeric=switchOn(created.lessThan(100000000000),created.multiply(1000),created);
 const known=or(kind.equal('timestamp'),number,map);
 const epoch=switchOn(kind.equal('timestamp'),timestampToUnixMillis(created),number,numeric,map,seconds.multiply(1000),constant(-8640000000000000));
 const cohorts=[{name:'epoch',condition:known,key:epoch},{name:'iso',condition:kind.equal('string'),key:created},{name:'unknown',condition:or(known,kind.equal('string')).not(),key:docId}];
 let base=db.pipeline().collection('games').where(field('players').arrayContains(uid));
 if(filters.mode&&filters.mode!=='all')base=base.where(filters.mode==='multiplayer'?or(field('mode').equal('multiplayer'),field('mode').equal('ffa')):field('mode').equal(filters.mode));
 if(filters.topic&&filters.topic!=='all')base=base.where(field('category').ifAbsent('unknown').equal(filters.topic==='mixed'?'all':filters.topic));
 if(filters.difficulty&&filters.difficulty!=='all')base=base.where(field('difficulty').ifAbsent('unknown').equal(filters.difficulty));
 if(filters.result&&filters.result!=='all')base=base.where(field(`receipts.${uid}.outcome`).ifAbsent('unknown').equal(filters.result));
 if(filters.replay&&filters.replay!=='all')base=base.where(filters.replay==='legacy'?field('replayVersion').ifAbsent(0).notEqual(1):field('replayVersion').ifAbsent(0).equal(1));
 const bounded=await Promise.all(cohorts.map(async cohort=>{
  if(cohort.name==='unknown'&&(filters.from||filters.to))return {name:cohort.name,rows:[] as HistoryRow[]};
  let query=base.where(cohort.condition);const c=cursor[cohort.name];
  if(filters.from)query=query.where(cohort.key.greaterThanOrEqual(cohort.name==='iso'?`${filters.from}T00:00:00.000Z`:Date.parse(`${filters.from}T00:00:00.000Z`)));
  if(filters.to){const end=Date.parse(`${filters.to}T00:00:00.000Z`)+86400000;query=query.where(cohort.key.lessThan(cohort.name==='iso'?new Date(end).toISOString():end));}
  if(c)query=query.where(or(cohort.key.lessThan(c.value),and(cohort.key.equal(c.value),docId.lessThan(c.id))));
  const snapshot=await execute(query.sort(cohort.key.descending(),docId.descending()).limit(HISTORY_PAGE_SIZE+1));
  return {name:cohort.name,rows:snapshot.results.map(row=>({...row.data(),id:row.id!})) as HistoryRow[]};
 }));
 // Merge by taking the head of each ordered stream; never advance past an
 // unreturned row, including malformed legacy dates. Unknown dates remain reachable.
 const rows:HistoryRow[]=[],next={...cursor};
 while(rows.length<HISTORY_PAGE_SIZE){const candidates=bounded.filter(c=>c.rows.length);if(!candidates.length)break;
  candidates.sort((a,b)=>(historyDate(b.rows[0].createdAt)??-Infinity)-(historyDate(a.rows[0].createdAt)??-Infinity)||b.rows[0].id.localeCompare(a.rows[0].id));
  const source=candidates[0],row=source.rows.shift()!;rows.push(row);next[source.name]={value:source.name==='iso'?row.createdAt:source.name==='unknown'?row.id:historyDate(row.createdAt)??-8640000000000000,id:row.id};
 }
 return {rows,cursor:next,hasMore:bounded.some(c=>c.rows.length>0)};
}
