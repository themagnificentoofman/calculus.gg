import {presentBankProblem} from './solution-presentation.mjs';
import type { BankProblem, RoundSnapshot } from '../bank/contracts.ts';
import type { GameQuestion } from '../game-progress.ts';

export class BankUnavailableError extends Error {
  constructor(message='There are not enough approved problems for these filters. Choose another topic or difficulty, or try again after a bank update.') { super(message); }
}
type Pool = { release_id: string; topic: string; difficulty: string; tag: string; family_id: string; item_count: number };
export type RecentProblems = import('../bank/exposure.ts').ExposureHistory;
export const POOL_SQL = `SELECT p.* FROM bank_pools p JOIN bank_releases r ON r.release_id=p.release_id
  WHERE p.release_id=(SELECT value FROM bank_config WHERE key='active_release') AND r.state='published'
  AND p.difficulty=? AND p.tag=? AND (?='all' OR p.topic=?) ORDER BY p.topic,p.family_id LIMIT 193`;
export const SLOT_SQL = `SELECT b.payload_json FROM bank_slots s
  JOIN bank_problems b ON b.problem_id=s.problem_id AND b.revision=s.revision
  JOIN bank_publication p ON p.problem_id=b.problem_id AND p.revision=b.revision
  WHERE s.release_id=? AND s.topic=? AND s.difficulty=? AND s.tag=? AND s.family_id=? AND s.slot=? AND p.state='approved'`;
const random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296;
function shuffled<T>(values: T[], rng: () => number): T[] {
  const copy = [...values];
  for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]]; }
  return copy;
}

/** At most 193 tiny pool rows + 320 primary-key probes. No corpus scan or ORDER BY RANDOM(). */
export async function selectBankQuestions(db: D1Database, input: { category: string; difficulty: string; count: number; tag?: string }, recent: RecentProblems = {}, rng = random) {
  const pools = (await db.prepare(POOL_SQL).bind(input.difficulty, input.tag || '*', input.category, input.category).all<Pool>()).results;
  if (!pools.length || pools.length > 192) throw new BankUnavailableError();
  const seen = new Set<string>(), familyCounts = new Map<string, number>();
  const recentProblems = new Set(recent.problems || []), recentFamilies = new Set(recent.families || []);
  const candidates = new Map<string, BankProblem>();
  const selected: BankProblem[] = [];
  let relaxation: RoundSnapshot['relaxation'] = 'none';
  const levels: RoundSnapshot['relaxation'][] = ['none', 'recent-families', 'family-cap', 'recent-problems'];
  // Cache only within this selection: retirement and activation take effect on every new request.
  for (let level = 0; level < levels.length && selected.length < input.count; level++) {
    const probes = Array.from({ length: 80 }, (_, i) => {
      const pool = shuffled(pools, rng)[i % pools.length];
      return [pool.release_id, pool.topic, pool.difficulty, pool.tag, pool.family_id, Math.floor(rng() * pool.item_count)];
    });
    // 16 six-field keys = 96 bindings, below D1's 100-parameter limit.
    // Five statements per stage keep even full relaxation below 50 D1 queries.
    const requests = [];
    for (let i = 0; i < probes.length; i += 16) {
      const chunk = probes.slice(i, i + 16);
      requests.push(db.prepare(`WITH wanted(release_id,topic,difficulty,tag,family_id,slot) AS (VALUES ${chunk.map(() => '(?,?,?,?,?,?)').join(',')})
        SELECT b.payload_json FROM wanted w JOIN bank_slots s USING(release_id,topic,difficulty,tag,family_id,slot)
        JOIN bank_problems b ON b.problem_id=s.problem_id AND b.revision=s.revision
        JOIN bank_publication p ON p.problem_id=b.problem_id AND p.revision=b.revision WHERE p.state='approved'`).bind(...chunk.flat()));
    }
    const results = await db.batch<{ payload_json: string }>(requests);
    for (const result of results) for (const row of result.results) {
      const p = JSON.parse(row.payload_json) as BankProblem;
      candidates.set(p.problemId, p);
    }
    const cap = level >= 2 ? Math.ceil(input.count / Math.min(pools.length, input.count)) + 1 : 2;
    // Family round-robin prevents large families and a single lucky sample dominating a round.
    const families = shuffled([...new Set(pools.map(p => p.family_id))], rng);
    for (let pass = 0; pass < cap && selected.length < input.count; pass++) for (const family of families) {
      if (selected.length === input.count) break;
      if (level === 0 && recentFamilies.has(family) || (familyCounts.get(family) || 0) >= cap) continue;
      const eligible = shuffled([...candidates.values()].filter(p => p.familyId === family && !seen.has(p.problemId) && (level >= 3 || !recentProblems.has(p.problemId))), rng);
      if (!eligible.length) continue;
      const p = eligible[0]; seen.add(p.problemId); selected.push(p); familyCounts.set(family, (familyCounts.get(family) || 0) + 1);
      relaxation = levels[level];
    }
  }
  if (selected.length !== input.count) throw new BankUnavailableError();
  const questions: GameQuestion[] = shuffled(selected, rng).map(original => {
    const p=presentBankProblem(original) as BankProblem & {solutionQuality?:{version:string}};
    const choices = shuffled(p.choices, rng);
    return { problemId: p.problemId, problemRevision: p.problemRevision, contentHash: p.contentHash, bankRelease: pools[0].release_id,
      familyId: p.familyId, templateVersion:p.templateVersion, ...(p.solutionQuality?{solutionReviewVersion:p.solutionQuality.version}:{}), choiceOrder: choices.map(c => c.choiceId), latexProblem: p.statement,
      options: choices.map(c => c.math), correctIndex: choices.findIndex(c => c.choiceId === p.answerChoiceId),
      explanation: p.solutionSteps, topic: p.topic, difficulty: p.difficulty };
  });
  return { questions, relaxation };
}

/** Recheck a pending set before creating a new game; active snapshots are untouched. */
export async function assertBankSetPlayable(db: D1Database, questions: GameQuestion[]) {
  if (!questions.length || questions.length > 20 || questions.some(q => !q.problemId || !q.problemRevision)) throw new BankUnavailableError();
  const result = await db.prepare(`SELECT COUNT(*) AS n FROM bank_publication WHERE state='approved' AND (problem_id,revision) IN (${questions.map(() => '(?,?)').join(',')})`)
    .bind(...questions.flatMap(q => [q.problemId!, q.problemRevision!])).all<{ n: number }>();
  if (result.results[0]?.n !== questions.length) throw new BankUnavailableError();
}
