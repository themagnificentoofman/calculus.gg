import features from './legacy-features.json' with { type: 'json' };

// The 72 original fixed-kernel construction families, not every older question.
// Construction aliases preserve this origin when a reviewed revision is renamed.
export const LEGACY_FAMILIES = Object.freeze(Object.keys(features).sort());
export function isLegacyProblem(question) {
  return question?.legacy === true || LEGACY_FAMILIES.includes(question?.familyId)
    || LEGACY_FAMILIES.includes(question?.constructionFamilyId)
    || LEGACY_FAMILIES.includes(question?.pedagogy?.constructionId);
}
