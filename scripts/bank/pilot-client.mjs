// Operator client for the explicitly authorized four-batch pilot only.
// Usage: node pilot-client.mjs status|pilot|verify|baseline KEY_PATH IMPORT_DIR SERVING_DB REPORT_PATH
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash, sign } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { join, resolve } from 'node:path';
import { PILOT } from '../../lib/server/bank-pilot-plan.mjs';
import { signingMessage } from '../../lib/server/bank-pilot.mjs';
import { canonical, decodeCompact } from '../../lib/bank/compact-codec.mjs';
const [mode, keyPath, importDir, servingPath, reportPath] = process.argv.slice(2);
if (!['status', 'pilot', 'verify', 'baseline'].includes(mode)) throw Error('Use status, pilot, verify, or baseline');
const origin = 'https://calculus.ninja';
const reportFile = resolve(reportPath);
const report = existsSync(reportFile) ? JSON.parse(readFileSync(reportFile, 'utf8')) : { projectId: PILOT.projectId, bundleId: PILOT.bundleId, startedAt: new Date().toISOString(), events: [], issues: [] };
assert.equal(report.bundleId, PILOT.bundleId);
const save = () => writeFileSync(reportFile, JSON.stringify(report, null, 2) + '\n');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const record = event => { report.events.push({ at: new Date().toISOString(), ...event });save();console.log(JSON.stringify(event)); };
let privateKey;
async function call(input) {
  privateKey ||= readFileSync(keyPath);
  const body = JSON.stringify(input), timestamp = String(Date.now()), hash = createHash('sha256').update(body).digest('hex');
  const started = performance.now();
  let response;
  try { response = await fetch(origin + '/api/bank-import', { method: 'POST', body, redirect: 'error', signal: AbortSignal.timeout(40000), headers: {
    'Content-Type': 'application/json', 'x-bank-time': timestamp, 'x-bank-body-sha256': hash,
    'x-bank-signature': sign(null, Buffer.from(signingMessage(timestamp, hash)), privateKey).toString('base64'),
  } }); } catch (error) { record({ op: input.op, index: input.index, transportError: error.name, reconcileBeforeRetry: true });throw Error('Transport failure; reconcile receipts before continuing'); }
  const result = await response.json();
  record({ op: input.op, index: input.index, cursor: input.cursor, status: response.status, roundTripMs: Math.round(performance.now() - started), serverMs: result.serverMs ?? null, metrics: result.metrics ?? null, skipped: result.skipped, category: result.category });
  if (!response.ok) throw Error(`Pilot stopped: ${response.status} ${result.category || result.error || 'HTTP error'}`);
  if (input.op === 'import' && !result.skipped && (result.serverMs > 2000 || performance.now() - started > 10000)) throw Error('Pilot paused after committed batch: import latency threshold exceeded; reconcile receipts');
  return result;
}
async function health(label) {
  const started = performance.now();
  const response = await fetch(origin + '/api/health', { cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(10000) });
  const body = await response.json();
  const ms = Math.round(performance.now() - started);
  record({ op: 'health', label, status: response.status, roundTripMs: ms, body });
  assert.equal(response.status, 200);assert.equal(body.status, 'ok');assert.equal(body.aiConfigured, true);assert.equal(body.secureGameplayConfigured, true);
  if (report.baselineMedianMs && ms > Math.max(2000, 3 * report.baselineMedianMs)) throw Error('Pilot paused: health latency threshold exceeded');
  return ms;
}
async function baseline() {
  const values = [];
  for (let i = 0; i < 5; i++) { values.push(await health('baseline'));await pause(300); }
  report.baselineMedianMs = values.sort((a,b) => a-b)[2];save();
  const response = await fetch(origin + '/api/questions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', redirect: 'error', signal: AbortSignal.timeout(10000) });
  record({ op: 'gameplay-auth-check', status: response.status });assert.equal(response.status, 401);
}
function assertStatus(status) {
  assert.equal(status.bundleId, PILOT.bundleId);assert.equal(status.cap, 4);
  assert.ok(status.counts.problems <= 928);assert.ok(status.counts.shared <= 72);
  assert.equal(status.counts.publication, 0);assert.equal(status.counts.releases, 0);assert.equal(status.counts.activeRelease, null);
  assert.ok(status.receipts.length <= 4);
  for (let i = 0; i < status.receipts.length; i++) { assert.equal(status.receipts[i].batch_id, PILOT.bundleId + '/' + i);assert.equal(status.receipts[i].sha256, PILOT.batches[i].sha256); }
  assert.equal(status.counts.problems, status.receipts.length ? 178 + (status.receipts.length - 1) * 250 : 0);
  assert.equal(status.counts.shared, status.receipts.length ? 72 : 0);
}
try {
  if (mode === 'baseline') { await baseline();process.exit(0); }
  const initial = await call({ op: 'status' });assertStatus(initial);
  report.lastStatus = initial;save();
  if (mode === 'status') { console.log(JSON.stringify({ counts: initial.counts, receipts: initial.receipts, allowanceKnown: false }));process.exit(0); }
  if (mode === 'pilot') {
    if (!report.baselineMedianMs) await baseline();
    // Verify all four local bodies before sending any mutation, and refuse every other batch.
    const texts = PILOT.batches.map((batch, index) => {
      const text = readFileSync(join(importDir, `batch-${String(index).padStart(5, '0')}.json`), 'utf8');
      assert.equal(Buffer.byteLength(text), batch.bytes);assert.equal(createHash('sha256').update(text).digest('hex'), batch.sha256);return text;
    });
    for (let index = initial.receipts.length; index < 4; index++) {
      await health('before-' + index);await pause(2000);
      const result = await call({ op: 'import', index, text: texts[index] });assert.equal(result.sha256, PILOT.batches[index].sha256);
      await health('after-' + index);
      const status = await call({ op: 'status' });assertStatus(status);assert.equal(status.receipts.length, index + 1);report.lastStatus = status;save();
    }
    for (let index = 0; index < 4; index++) assert.equal((await call({ op: 'import', index, text: texts[index] })).skipped, true);
    report.duplicateRetryVerified = true;save();
  }
  const status = await call({ op: 'status' });assertStatus(status);assert.equal(status.receipts.length, 4);
  const source = new DatabaseSync(servingPath, { readOnly: true });
  try {
    let cursor = 0, verified = 0;const identity = createHash('sha256');
    while (true) {
      const { rows } = await call({ op: 'verify', cursor });if (!rows.length) break;
      for (const row of rows) {
        assert.ok(row.problem_ref > cursor && row.problem_ref <= 928);
        const expected = source.prepare('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) WHERE problem_ref=?').get(row.problem_ref);
        const actual = await decodeCompact(row);
        assert.equal(canonical(actual), canonical(await decodeCompact(expected)));
        identity.update(`${actual.problemId}@${actual.problemRevision}:${actual.contentHash}\n`);cursor = row.problem_ref;verified++;
      }
    }
    assert.equal(verified, 928);
    const shared = await call({ op: 'shared' });assert.equal(shared.rows.length, 72);
    for (const row of shared.rows) {
      const expected = source.prepare('SELECT * FROM cbank_shared WHERE shared_id=?').get(row.shared_id);
      assert.equal(row.metadata_json, expected.metadata_json);assert.deepEqual(Buffer.from(row.content_hash), Buffer.from(expected.content_hash));
    }
    report.verification = { verifiedAt: new Date().toISOString(), problems: verified, sharedRecords: 72, identitySha256: identity.digest('hex'), allCanonicalContentMatches: true, receipts: 4, publicationRows: 0, activeProblems: 0 };
    report.lastStatus = status;save();
  } finally { source.close(); }
  await health('final');report.completedAt = new Date().toISOString();save();
  console.log(JSON.stringify({ pilotComplete: true, verification: report.verification, fullImportStarted: false }));
} catch (error) { report.issues.push({ at: new Date().toISOString(), message: error.message });save();console.error(error.message);process.exitCode = 1; }
