import {gunzipSync} from 'node:zlib';
// Isolated historical storage/selector fixtures, not production content review.
// This dependency never writes the shipping eligibility registry.
import {createLegacyPolicy} from '../../../lib/server/legacy-selection.mjs';
import {LEGACY_FAMILIES} from '../../../lib/bank/legacy-origin.mjs';
import {reconstruct} from '../../../lib/bank/compact-codec.mjs';
export function fixtureLegacyPolicy(records) {
  return createLegacyPolicy(records.map(p => ({problemId:p.problemId,revision:p.problemRevision,contentHash:p.contentHash,
    familyId:p.familyId,constructionId:p.constructionFamilyId||p.familyId,
    review:{path:'isolated-test-fixture-only',sha256:'0'.repeat(64)},usefulness:'Exercises historical storage and selection mechanics; not playable release coverage.'})));
}
export async function historicalFixturePolicy(db) {
  const rows=(await db.prepare('SELECT b.*,m.metadata_json FROM cbank_problems b JOIN cbank_shared m USING(shared_id)').all()).results;
  const records=rows.map(row=>reconstruct(row,JSON.parse(gunzipSync(row.payload_gzip).toString())));
  return fixtureLegacyPolicy(records.filter(p=>LEGACY_FAMILIES.includes(p.familyId)));
}
