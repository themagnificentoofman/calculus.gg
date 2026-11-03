// Local Worker/D1 integration test against four existing, checksum-verified batches.
import assert from 'node:assert/strict';
import { Miniflare } from 'miniflare';
import { generateKeyPairSync, sign, createHash } from 'node:crypto';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { PILOT } from '../../lib/server/bank-pilot-plan.mjs';
import { signingMessage } from '../../lib/server/bank-pilot.mjs';
import { decodeCompact } from '../../lib/bank/compact-codec.mjs';
const directory = resolve(process.argv[2]);
const { publicKey, privateKey } = generateKeyPairSync('ed25519');
const persist = mkdtempSync(join(tmpdir(), 'bank-pilot-http-'));
const modules = ['lib/server/bank-pilot.mjs', 'lib/server/bank-pilot-plan.mjs'].map(path => ({ type: 'ESModule', path, contents: readFileSync(path, 'utf8') }));
modules.unshift({ type: 'ESModule', path: 'pilot.mjs', contents: `import {bankPilot} from './lib/server/bank-pilot.mjs'; export default {fetch(request,env){return bankPilot(request,env.DB,env.KEY,env.EXPIRES)}};` });
const create = () => new Miniflare({ modules, modulesRoot: process.cwd(), compatibilityDate: '2026-04-01', d1Databases: { DB: 'pilot-smoke' }, d1Persist: persist,
  bindings: { KEY: publicKey.export({ type: 'spki', format: 'der' }).toString('base64'), EXPIRES: String(Date.now() + 3600000) } });
let mf = create();
async function call(input, expected = 200) {
  const body = JSON.stringify(input), timestamp = String(Date.now()), hash = createHash('sha256').update(body).digest('hex');
  const response = await mf.dispatchFetch('http://localhost/api/bank-import', { method: 'POST', body, headers: {
    'x-bank-time': timestamp, 'x-bank-body-sha256': hash, 'x-bank-signature': sign(null, Buffer.from(signingMessage(timestamp, hash)), privateKey).toString('base64'),
  } });
  const result = await response.json();assert.equal(response.status, expected, JSON.stringify(result));return result;
}
const batch = index => ({ op: 'import', index, text: readFileSync(join(directory, 'batch-' + String(index).padStart(5, '0') + '.json'), 'utf8') });
try {
  const db = await mf.getD1Database('DB');
  for (const file of ['0000_dazzling_tenebrous.sql','0001_problem_bank.sql','0002_compact_bank.sql']) await db.exec(readFileSync('drizzle/' + file, 'utf8').split('\n').filter(s => !s.trim().startsWith('--')).join(' '));
  assert.equal((await mf.dispatchFetch('http://localhost/api/bank-import', { method: 'POST' })).status, 403);
  await call({ op: 'import', index: 4, text: '[]' }, 400);
  await call(batch(1), 503); // Sequence guard atomically rejects a later batch.
  assert.equal((await call({ op: 'status' })).counts.problems, 0);
  await call(batch(0)); // Pretend client lost this response, then restart the Worker runtime.
  await mf.dispose();mf = create();
  assert.equal((await call(batch(0))).skipped, true);
  for (let index = 1; index < 4; index++) assert.equal((await call(batch(index))).skipped, false);
  for (let index = 0; index < 4; index++) assert.equal((await call(batch(index))).skipped, true);
  const status = await call({ op: 'status' });
  assert.equal(status.counts.shared, 72);assert.equal(status.counts.problems, 928);assert.equal(status.receipts.length, 4);
  assert.equal(status.counts.publication, 0);assert.equal(status.counts.releases, 0);assert.equal(status.counts.activeRelease, null);
  let cursor = 0, verified = 0;
  while (true) {
    const { rows } = await call({ op: 'verify', cursor });if (!rows.length) break;
    for (const row of rows) { await decodeCompact(row);cursor = row.problem_ref;verified++; }
  }
  assert.equal(verified, 928);
  assert.equal((await call({ op: 'shared' })).rows.length, 72);
  console.log(JSON.stringify({ scope: 'LOCAL Worker/D1 authenticated endpoint', passed: true, verified, shared: 72, receipts: 4, activation: false, bundleId: PILOT.bundleId }));
} finally { await mf.dispose();rmSync(persist, { recursive: true, force: true }); }
