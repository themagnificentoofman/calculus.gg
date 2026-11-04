import registry from './legacy-eligibility.json' with { type: 'json' };
import { LEGACY_FAMILIES, isLegacyProblem } from '../bank/legacy-origin.mjs';

/** Exact immutable revisions only. Opt-in never substitutes for admission. */
export function createLegacyPolicy(records) {
  if (!Array.isArray(records) || records.length > 20000) throw Error('Invalid legacy review inventory');
  const byReference = new Map();
  for (const record of records) {
    if (!/^cn_[a-f0-9]{20}$/.test(record.problemId) || !Number.isSafeInteger(record.revision) || record.revision < 1
      || !/^[a-f0-9]{64}$/.test(record.contentHash) || !LEGACY_FAMILIES.includes(record.constructionId)
      || !/^[a-z][a-z0-9-]{1,100}$/.test(record.familyId) || !record.review?.path || !/^[a-f0-9]{64}$/.test(record.review.sha256)
      || !record.usefulness?.trim()) throw Error('Legacy eligibility needs exact source, review and usefulness evidence');
    const key = `${record.problemId}@${record.revision}`;
    if (byReference.has(key)) throw Error('Duplicate legacy approval');
    byReference.set(key, Object.freeze({ ...record }));
  }
  const families = [...new Set([...LEGACY_FAMILIES, ...records.map(r => r.familyId)])];
  return Object.freeze({
    familyJson: JSON.stringify(families),
    selection(includeLegacy) {
      const admitted = includeLegacy === true ? records : [];
      const allowedFamilies = new Set(admitted.flatMap(r => [r.familyId, r.constructionId]));
      return { excludedFamilies: JSON.stringify(families.filter(f => !allowedFamilies.has(f))),
        revisions: JSON.stringify(admitted.map(r => `${r.problemId}@${r.revision}`)) };
    },
    check(problem, constructionId, includeLegacy) {
      // A missing database alias must not erase an origin recorded in the
      // immutable canonical problem. Fail closed even after SQL sampling.
      const legacy = isLegacyProblem({ ...problem, constructionFamilyId: constructionId }) || families.includes(problem.familyId);
      if (!legacy) return false;
      const review = byReference.get(`${problem.problemId}@${problem.problemRevision}`);
      if (includeLegacy !== true || !review || review.contentHash !== problem.contentHash
        || review.familyId !== problem.familyId || review.constructionId !== constructionId) throw Error('Unreviewed legacy revision');
      return true;
    },
  });
}

export const legacyPolicy = createLegacyPolicy(registry.records);
export function includesLegacyForMode(mode, settings) {
  return (mode === 'test' || mode === 'rapid') && settings?.includeLegacyProblems === true;
}

/** Used by serving and offline capacity accounting before any relaxation. */
export function legacyEligibilitySql(base) {
  return base + ` AND ((p.family_id NOT IN (SELECT value FROM json_each((SELECT legacy_families FROM context))) AND COALESCE(fl.construction_id,p.family_id) NOT IN (SELECT value FROM json_each((SELECT legacy_families FROM context)))) OR b.problem_id||'@'||b.revision IN (SELECT value FROM json_each((SELECT legacy_revisions FROM context))))`;
}
