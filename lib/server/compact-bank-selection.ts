import {presentBankProblem} from './solution-presentation.mjs';
import type { BankProblem, RoundSnapshot, SelectionDiagnostics } from '../bank/contracts.ts';
import type { GameQuestion } from '../game-progress.ts';
import { decodeCompact } from '../bank/compact-codec.mjs';
import { exposureWeight } from '../bank/exposure.ts';
import legacyFeatures from '../bank/legacy-features.json' with { type: 'json' };
import { BankUnavailableError, type RecentProblems } from './bank-selection.ts';
type Pool = { pool_id: number; release_id: string; active_release: string; family_id: string; item_count: number };
type Features = { idea: string; structure: string; technique: string; combination: string; weight: number };
type Candidate = { problem_ref: number; problem_id: string; family_id: string } & Features;
export const POOL_SQL = `SELECT p.*,c.value AS active_release FROM cbank_config c
 JOIN cbank_pools p ON p.release_id IN (SELECT c.value UNION SELECT source_release_id FROM cbank_release_sources WHERE release_id=c.value)
 JOIN cbank_releases r ON r.release_id=p.release_id JOIN cbank_releases active ON active.release_id=c.value
 WHERE c.key='active_release' AND active.state='published' AND r.state='published'
 AND p.difficulty=? AND p.tag=? AND (?='all' OR p.topic=?) ORDER BY p.topic,p.family_id LIMIT 193`;
export const SLOT_SQL = `SELECT b.problem_ref,b.problem_id,p.family_id FROM cbank_slots s
 JOIN cbank_problems b USING(problem_ref) JOIN cbank_publication u USING(problem_ref) JOIN cbank_pools p USING(pool_id)
 WHERE s.pool_id=? AND s.slot=? AND u.state='approved'`;
export const PAYLOAD_SQL = `SELECT b.*,m.metadata_json FROM cbank_problems b JOIN cbank_shared m USING(shared_id)
 JOIN cbank_publication u USING(problem_ref) WHERE u.state='approved' AND b.problem_ref IN `;
const random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296;
function shuffled<T>(values: T[], rng: () => number): T[] {
 const copy=[...values]; for(let i=copy.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[copy[i],copy[j]]=[copy[j],copy[i]];} return copy;
}
function weighted<T>(items: T[], score: (item:T)=>number, rng:()=>number):T {
 const weights=items.map(item=>Math.max(1e-8,score(item))),total=weights.reduce((a,b)=>a+b,0);let r=rng()*total;
 for(let i=0;i<items.length;i++){r-=weights[i];if(r<=0)return items[i];}return items.at(-1)!;
}
const gcd=(a:number,b:number):number=>b?gcd(b,a%b):a;
function features(row:Candidate):Candidate {
 const fallback=(legacyFeatures as Record<string,Features>)[row.family_id];
 return {...row,idea:row.idea||fallback?.idea||row.family_id,structure:row.structure||fallback?.structure||row.family_id,
 technique:row.technique||fallback?.technique||row.family_id,combination:row.combination||fallback?.combination||row.family_id,weight:row.weight??fallback?.weight??.15};
}
function historyWeights(recent:RecentProblems,now:number) {
 const ids=new Set<string>(),weights=new Map<string,number>();
 const add=(key:string,value:number)=>weights.set(key,(weights.get(key)||0)+value);
 if(recent.version===2){
  for(const e of recent.exposures||[]){const w=exposureWeight(e,now);if(!w)continue;
   // Only short-lived issued sets, reported displays, and actual attempts in
   // their respective windows participate. A report is never a graded attempt.
   ids.add(e.problemId);add('f:'+e.familyId,w);add('i:'+e.idea,w);add('s:'+e.structure,w);add('t:'+e.technique,w);add('c:'+e.combination,w);
  }
 }else{
  for(const id of recent.problems||[])ids.add(id);
  for(const family of recent.families||[])add('f:'+family,.25);
 }
 return {ids,weights};
}
function choose(candidates:Candidate[],count:number,cap:number,history:ReturnType<typeof historyWeights>,allowRecent:boolean,rng:()=>number,drill:boolean) {
 const selected:Candidate[]=[],used=new Set<string>(),counts=new Map<string,number>();
 while(selected.length<count){
  const eligible=candidates.filter(c=>!used.has(c.problem_id)&&(counts.get(c.family_id)||0)<cap&&(allowRecent||!history.ids.has(c.problem_id)));
  if(!eligible.length)return null;
  const last=selected.at(-1),groups=new Map<string,Candidate[]>();
  for(const c of eligible){const g=groups.get(c.family_id)||[];g.push(c);groups.set(c.family_id,g);}
  let families=[...groups.keys()];if(families.some(f=>f!==last?.family_id))families=families.filter(f=>f!==last?.family_id);
  const score=(c:Candidate)=>{
   const h=history.weights;
   const penalty=.9*(h.get('f:'+c.family_id)||0)+.45*(h.get('i:'+c.idea)||0)+.25*(h.get('s:'+c.structure)||0)
    +(drill?0:.15*(h.get('t:'+c.technique)||0))+.15*(h.get('c:'+c.combination)||0);
   const local=selected.slice(-3).reduce((n,p)=>n+Number(p.idea===c.idea)*1.1+Number(p.structure===c.structure)*.8+(drill?0:Number(p.technique===c.technique)*.25),0);
   return c.weight*Math.exp(-Math.min(8,penalty*.16+local+(counts.get(c.family_id)||0)*.45));
  };
  // Normalize within each family: 1,400 variants never get 175 times the
  // opportunity of eight carefully authored instances.
  const family=weighted(families,f=>groups.get(f)!.reduce((n,c)=>n+score(c),0)/groups.get(f)!.length,rng);
  const item=weighted(groups.get(family)!,score,rng);selected.push(item);used.add(item.problem_id);counts.set(family,(counts.get(family)||0)+1);
 }
 return selected;
}
/** Constrained random ordering, never an unconstrained final shuffle. */
function order(selected:Candidate[],rng:()=>number) {
 const pending=[...selected],result:Candidate[]=[];
 while(pending.length){
  const last=result.at(-1),available=pending.filter(p=>p.family_id!==last?.family_id);
  const canFinish=(choice:Candidate)=>{
   const counts=new Map<string,number>();for(const p of pending)if(p!==choice)counts.set(p.family_id,(counts.get(p.family_id)||0)+1);
   const remaining=pending.length-1;
   return [...counts].every(([family,n])=>n<=Math.ceil(remaining/2)-(family===choice.family_id&&remaining%2===1?1:0));
  };
  const feasible=available.filter(canFinish),eligible=feasible.length?feasible:available.length?available:pending;
  const next=weighted(eligible,c=>Math.exp(-result.slice(-2).reduce((v,p)=>v+Number(p.idea===c.idea)*1.5+Number(p.structure===c.structure),0)),rng);
  result.push(next);pending.splice(pending.indexOf(next),1);
 }
 return result;
}
/** <=192 pool rows, <=320 distinct indexed slot probes, exactly count decodes. */
export async function selectBankQuestions(db:D1Database,input:{category:string;difficulty:string;count:number;tag?:string},recent:RecentProblems={},rng=random,now=Date.now()) {
 if(!Number.isInteger(input.count)||input.count<1||input.count>20)throw new BankUnavailableError();
 const pools=(await db.prepare(POOL_SQL).bind(input.difficulty,input.tag||'*',input.category,input.category).all<Pool>()).results;
 if(!pools.length||pools.length>192)throw new BankUnavailableError();
 const familyCount=new Set(pools.map(p=>p.family_id)).size,history=historyWeights(recent,now),candidates=new Map<string,Candidate>();
 const slots=new Map(pools.map(p=>{let step=Math.max(1,Math.floor(rng()*p.item_count));while(gcd(step,p.item_count)!==1)step=step%p.item_count+1;return [p.pool_id,{start:Math.floor(rng()*p.item_count),step,used:0}];}));
 let probes=0,statements=1,chosen:Candidate[]|null=null,relaxation:RoundSnapshot['relaxation']='none';
 const reasons:SelectionDiagnostics['reasons']=[];
 // A catalogue with fewer than ten families proves a 20-question cap of two
 // impossible. Candidate sampling alone never proves that the pool is empty.
 let cap=Math.max(2,Math.ceil(input.count/familyCount));
 if(cap>2){reasons.push('family-cap-impossible');relaxation='family-cap';}
 for(let stage=0;stage<4;stage++){
  const wanted:number[][]=[];
  const schedule=shuffled(pools,rng);
  while(wanted.length<80){let added=0;
   for(const pool of schedule){const cursor=slots.get(pool.pool_id)!;if(cursor.used>=pool.item_count)continue;
    wanted.push([pool.pool_id,(cursor.start+cursor.step*cursor.used++)%pool.item_count]);added++;if(wanted.length===80)break;
   }if(!added)break;
  }
  const requests=[];for(let i=0;i<wanted.length;i+=40){const chunk=wanted.slice(i,i+40);
   requests.push(db.prepare(`WITH wanted(pool_id,slot) AS (VALUES ${chunk.map(()=>'(?,?)').join(',')})
    SELECT b.problem_ref,b.problem_id,p.family_id,f.idea,f.structure,f.technique,f.combination,f.weight
    FROM wanted w JOIN cbank_slots s USING(pool_id,slot) JOIN cbank_problems b USING(problem_ref)
    JOIN cbank_publication u USING(problem_ref) JOIN cbank_pools p USING(pool_id)
    LEFT JOIN cbank_selection_features f USING(problem_ref) WHERE u.state='approved'`).bind(...chunk.flat()));
  }
  probes+=wanted.length;statements+=requests.length;
  if(requests.length)for(const result of await db.batch<Candidate>(requests))for(const row of result.results)candidates.set(row.problem_id,features(row));
  chosen=choose([...candidates.values()],input.count,cap,history,false,rng,!!input.tag);
  if(chosen||wanted.length===0)break;
 }
 const exhausted=pools.every(p=>slots.get(p.pool_id)!.used===p.item_count);
 if(!chosen&&exhausted){
  const availableCounts=new Map<string,number>();for(const c of candidates.values())availableCounts.set(c.family_id,(availableCounts.get(c.family_id)||0)+1);
  const cappedCapacity=[...availableCounts.values()].reduce((n,size)=>n+Math.min(cap,size),0);
  // Retirement or a genuinely narrow inventory can require more than two.
  if(cappedCapacity<input.count){
   for(let trial=cap+1;trial<=input.count;trial++){chosen=choose([...candidates.values()],input.count,trial,history,false,rng,!!input.tag);if(chosen){cap=trial;relaxation='family-cap';if(!reasons.includes('family-cap-impossible'))reasons.push('family-cap-impossible');break;}}
  }
 }
 if(!chosen){
  chosen=choose([...candidates.values()],input.count,cap,history,true,rng,!!input.tag);
  if(chosen){relaxation='recent-problems';reasons.push(exhausted?'recent-items-exhausted':'candidate-sampling-limit');}
 }
 if(!chosen)throw new BankUnavailableError();
 const selected=order(chosen,rng);
 if(selected.some((p,i)=>i>0&&p.family_id===selected[i-1].family_id))reasons.push('adjacency-unavoidable');
 const rows=(await db.prepare(PAYLOAD_SQL+`(${selected.map(()=>'?').join(',')})`).bind(...selected.map(p=>p.problem_ref)).all()).results;statements++;
 if(rows.length!==input.count)throw new BankUnavailableError();
 const decoded=await Promise.all(rows.map(async row=>await decodeCompact(row) as BankProblem)),byId=new Map(decoded.map(p=>[p.problemId,p]));
 const questions:GameQuestion[]=selected.map(candidate=>{
  const original=byId.get(candidate.problem_id);
  const p=original?presentBankProblem(original) as BankProblem & {solutionQuality?:{version:string}}:null;
  if(!p||p.familyId!==candidate.family_id||p.difficulty!==input.difficulty||input.category!=='all'&&p.topic!==input.category||input.tag&&input.tag!=='*'&&!p.techniqueTags.includes(input.tag))throw Error('Bank pool/content mismatch');
  const choices=shuffled(p.choices,rng);
  return {problemId:p.problemId,problemRevision:p.problemRevision,contentHash:p.contentHash,bankRelease:pools[0].active_release,
   familyId:p.familyId,templateVersion:p.templateVersion,...(p.solutionQuality?{solutionReviewVersion:p.solutionQuality.version}:{}),...(p.pedagogy?{pedagogy:p.pedagogy}:{}),context:{assumptions:p.assumptions,subtopic:p.subtopic,techniqueTags:p.techniqueTags,parameters:p.parameters},
   choiceOrder:choices.map(c=>c.choiceId),latexProblem:p.statement,options:choices.map(c=>c.math),correctIndex:choices.findIndex(c=>c.choiceId===p.answerChoiceId),explanation:p.solutionSteps,topic:p.topic,difficulty:p.difficulty};
 });
 return {questions,relaxation,diagnostics:{policy:'exposure-weighted-v2' as const,candidateCount:candidates.size,probes,statements,catalogFamilies:familyCount,exhaustedInventory:exhausted,reasons}};
}
export async function assertBankSetPlayable(db:D1Database,questions:GameQuestion[]) {
 if(!questions.length||questions.length>20||questions.some(q=>!q.problemId||!q.problemRevision))throw new BankUnavailableError();
 const result=await db.prepare(`SELECT COUNT(*) AS n FROM cbank_problems b JOIN cbank_publication u USING(problem_ref)
 WHERE u.state='approved' AND (b.problem_id,b.revision) IN (${questions.map(()=>'(?,?)').join(',')})`).bind(...questions.flatMap(q=>[q.problemId!,q.problemRevision!])).all<{n:number}>();
 if(result.results[0]?.n!==questions.length)throw new BankUnavailableError();
}
