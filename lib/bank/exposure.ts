import type { GameQuestion } from '../game-progress.ts';
import legacyFeatures from './legacy-features.json' with { type: 'json' };

export type ExposureStage = 'issued' | 'displayed' | 'attempted';
export interface Exposure {
  roundId: string;
  problemId: string;
  lineageId?: string;
  familyId: string;
  idea: string;
  structure: string;
  technique: string;
  combination: string;
  stage: ExposureStage;
  at: number;
}
export interface ExposureHistory { version?: 2; exposures?: Exposure[]; problems?: string[]; families?: string[] }
const rank = { issued: 0, displayed: 1, attempted: 2 };
const lifetime = { issued: 10 * 60_000, displayed: 86400_000, attempted: 14 * 86400_000 };
export const MAX_EXPOSURES = 512;

/** Client display reports are preferences, not proof of attempts or mastery. */
export function exposureWeight(exposure: Exposure, now: number): number {
  const age = Math.max(0, now - exposure.at);
  if (age > lifetime[exposure.stage]) return 0;
  return { issued: .06, displayed: .35, attempted: 1 }[exposure.stage] * Math.exp(-3 * age / lifetime[exposure.stage]);
}

export function recordExposures(history: ExposureHistory, roundId: string, questions: GameQuestion[], stage: ExposureStage, now: number, asOf=now): ExposureHistory {
  const entries = (history.exposures || []).filter(e => exposureWeight(e, asOf) > 0);
  for (const question of questions) {
    if (!question.problemId || !question.familyId) continue;
    const key = entries.findIndex(e => e.roundId === roundId && e.problemId === question.problemId);
    if (key >= 0 && rank[entries[key].stage] >= rank[stage]) continue;
    const p = question.pedagogy, legacy = (legacyFeatures as Record<string,{idea:string;structure:string;technique:string;combination:string}>)[question.familyId];
    const entry: Exposure = { roundId, problemId: question.problemId, lineageId: question.lineageId || question.problemId, familyId: question.constructionFamilyId || question.familyId,
      idea: p?.relatedIdeaGroupId || legacy?.idea || question.familyId, structure: p?.structuralSignature || legacy?.structure || question.familyId,
      technique: p?.primaryTechnique || legacy?.technique || question.context?.techniqueTags?.[0] || question.familyId,
      combination: p ? [...p.reasoningDemand].sort().join('+') + ':' + p.primaryTechnique : legacy?.combination || question.familyId,
      stage, at: now };
    if (key >= 0) entries[key] = entry; else entries.push(entry);
  }
  // Retain attempted material first when a user abandons many generated sets.
  const kept = entries.filter(e=>exposureWeight(e,asOf)>0).sort((a,b) => rank[a.stage]-rank[b.stage] || a.at-b.at).slice(-MAX_EXPOSURES).sort((a,b) => a.at-b.at);
  return { version: 2, exposures: kept,
    // Compatibility only; v2 selection uses stage-aware entries above.
    problems: kept.map(e=>e.problemId).slice(-100), families: kept.map(e=>e.familyId).slice(-20) };
}
