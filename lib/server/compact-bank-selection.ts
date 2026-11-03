import type { BankProblem, RoundSnapshot } from '../bank/contracts.ts';
import type { GameQuestion } from '../game-progress.ts';
import { decodeCompact } from '../bank/compact-codec.mjs';
import { BankUnavailableError, type RecentProblems } from './bank-selection.ts';
type Pool = { pool_id: number; release_id: string; family_id: string; item_count: number };
type Candidate = { problem_ref: number; problem_id: string; family_id: string };
export const POOL_SQL = `SELECT p.* FROM cbank_pools p JOIN cbank_releases r USING(release_id)
  WHERE p.release_id=(SELECT value FROM cbank_config WHERE key='active_release') AND r.state='published'
  AND p.difficulty=? AND p.tag=? AND (?='all' OR p.topic=?) ORDER BY p.topic,p.family_id LIMIT 193`;
export const SLOT_SQL = `SELECT b.problem_ref,b.problem_id,p.family_id FROM cbank_slots s
  JOIN cbank_problems b USING(problem_ref) JOIN cbank_publication u USING(problem_ref) JOIN cbank_pools p USING(pool_id)
  WHERE s.pool_id=? AND s.slot=? AND u.state='approved'`;
export const PAYLOAD_SQL = `SELECT b.*,m.metadata_json FROM cbank_problems b JOIN cbank_shared m USING(shared_id)
  JOIN cbank_publication u USING(problem_ref) WHERE u.state='approved' AND b.problem_ref IN `;
const random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296;
function shuffled<T>(values: T[], rng: () => number): T[] {
  const copy = [...values];
  for (let i=copy.length-1;i>0;i--) { const j=Math.floor(rng()*(i+1)); [copy[i],copy[j]]=[copy[j],copy[i]]; }
  return copy;
}
/** <=193 pool rows, <=320 indexed identity probes, exactly count payload decompressions. */
export async function selectBankQuestions(db: D1Database, input: { category: string; difficulty: string; count: number; tag?: string }, recent: RecentProblems = {}, rng = random) {
  if (!Number.isInteger(input.count) || input.count<1 || input.count>20) throw new BankUnavailableError();
  const pools = (await db.prepare(POOL_SQL).bind(input.difficulty,input.tag||'*',input.category,input.category).all<Pool>()).results;
  if (!pools.length || pools.length>192) throw new BankUnavailableError();
  const seen = new Set<string>(),familyCounts = new Map<string,number>();
  const recentProblems = new Set(recent.problems||[]),recentFamilies = new Set(recent.families||[]);
  const candidates = new Map<string,Candidate>(),selected: Candidate[] = [];
  let relaxation: RoundSnapshot['relaxation'] = 'none';
  const levels: RoundSnapshot['relaxation'][] = ['none','recent-families','family-cap','recent-problems'];
  for (let level=0;level<levels.length && selected.length<input.count;level++) {
    const probes = Array.from({length:80},(_,i)=>{
      const pool=shuffled(pools,rng)[i%pools.length];
      return [pool.pool_id,Math.floor(rng()*pool.item_count)];
    });
    const requests=[];
    for (let i=0;i<probes.length;i+=40) {
      const chunk=probes.slice(i,i+40);
      requests.push(db.prepare(`WITH wanted(pool_id,slot) AS (VALUES ${chunk.map(()=>'(?,?)').join(',')})
        SELECT b.problem_ref,b.problem_id,p.family_id FROM wanted w JOIN cbank_slots s USING(pool_id,slot)
        JOIN cbank_problems b USING(problem_ref) JOIN cbank_publication u USING(problem_ref)
        JOIN cbank_pools p USING(pool_id) WHERE u.state='approved'`).bind(...chunk.flat()));
    }
    for (const result of await db.batch<Candidate>(requests)) for (const p of result.results) candidates.set(p.problem_id,p);
    const cap = level>=2 ? Math.ceil(input.count/Math.min(pools.length,input.count))+1 : 2;
    const families = shuffled([...new Set(pools.map(p=>p.family_id))],rng);
    for (let pass=0;pass<cap && selected.length<input.count;pass++) for (const family of families) {
      if (selected.length===input.count) break;
      if (level===0 && recentFamilies.has(family) || (familyCounts.get(family)||0)>=cap) continue;
      const eligible = shuffled([...candidates.values()].filter(p=>p.family_id===family && !seen.has(p.problem_id) && (level>=3 || !recentProblems.has(p.problem_id))),rng);
      if (!eligible.length) continue;
      const p=eligible[0]; seen.add(p.problem_id); selected.push(p); familyCounts.set(family,(familyCounts.get(family)||0)+1); relaxation=levels[level];
    }
  }
  if (selected.length!==input.count) throw new BankUnavailableError();
  // Recheck approval while fetching only the final selection. No global decoded-payload cache.
  const rows = (await db.prepare(PAYLOAD_SQL+`(${selected.map(()=>'?').join(',')})`).bind(...selected.map(p=>p.problem_ref)).all()).results;
  if (rows.length!==input.count) throw new BankUnavailableError();
  const decoded = await Promise.all(rows.map(async row=>await decodeCompact(row) as BankProblem));
  const byId = new Map(decoded.map(p=>[p.problemId,p]));
  const questions: GameQuestion[] = shuffled(selected,rng).map(candidate=>{
    const p=byId.get(candidate.problem_id);
    if (!p || p.familyId!==candidate.family_id || p.difficulty!==input.difficulty || input.category!=='all' && p.topic!==input.category || input.tag && input.tag!=='*' && !p.techniqueTags.includes(input.tag)) throw Error('Bank pool/content mismatch');
    const choices=shuffled(p.choices,rng);
    return {problemId:p.problemId,problemRevision:p.problemRevision,contentHash:p.contentHash,bankRelease:pools[0].release_id,
      familyId:p.familyId,choiceOrder:choices.map(c=>c.choiceId),latexProblem:p.statement,options:choices.map(c=>c.math),
      correctIndex:choices.findIndex(c=>c.choiceId===p.answerChoiceId),explanation:p.solutionSteps,topic:p.topic,difficulty:p.difficulty};
  });
  return {questions,relaxation};
}
export async function assertBankSetPlayable(db: D1Database, questions: GameQuestion[]) {
  if (!questions.length || questions.length>20 || questions.some(q=>!q.problemId || !q.problemRevision)) throw new BankUnavailableError();
  const result = await db.prepare(`SELECT COUNT(*) AS n FROM cbank_problems b JOIN cbank_publication u USING(problem_ref)
    WHERE u.state='approved' AND (b.problem_id,b.revision) IN (${questions.map(()=>'(?,?)').join(',')})`)
    .bind(...questions.flatMap(q=>[q.problemId!,q.problemRevision!])).all<{n:number}>();
  if (result.results[0]?.n!==questions.length) throw new BankUnavailableError();
}
