import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, sign, createHash } from 'node:crypto';
import { bankPilot, signingMessage } from '../lib/server/bank-pilot.mjs';
const { publicKey, privateKey } = generateKeyPairSync('ed25519');
const key = publicKey.export({ type: 'spki', format: 'der' }).toString('base64');
function request(input, overrides = {}) {
  const body = JSON.stringify(input), timestamp = String(Date.now()), hash = createHash('sha256').update(body).digest('hex');
  return new Request('https://test.invalid/api/bank-import', { method: 'POST', body, headers: {
    'x-bank-time': timestamp, 'x-bank-body-sha256': hash,
    'x-bank-signature': sign(null, Buffer.from(signingMessage(timestamp, hash)), privateKey).toString('base64'), ...overrides,
  } });
}
test('pilot rejects unauthenticated, expired, altered, cross-origin and out-of-cap requests before touching D1', async () => {
  let queries = 0;
  const db = { prepare() { queries++; throw Error('D1 must not be reached'); } };
  const call = (req, pub = key, expiry = String(Date.now() + 60000)) => bankPilot(req, db, pub, expiry);
  assert.equal((await call(new Request('https://test.invalid/api/bank-import', { method: 'POST' }))).status, 403);
  assert.equal((await call(request({ op: 'status' }), '')).status, 404);
  assert.equal((await call(request({ op: 'status' }), key, '1')).status, 404);
  assert.equal((await call(request({ op: 'status' }, { origin: 'https://test.invalid' }))).status, 403);
  assert.equal((await call(request({ op: 'status' }, { 'x-bank-time': '1000000000000' }))).status, 403);
  assert.equal((await call(request({ op: 'status' }, { 'x-bank-body-sha256': '0'.repeat(64) }))).status, 403);
  assert.equal((await call(request({ op: 'status' }, { 'content-length': '900001' }))).status, 400);
  assert.equal((await call(request({ op: 'import', index: 4, text: '[]' }))).status, 400);
  assert.equal((await call(request({ op: 'import', index: 0, text: '[]' }))).status, 400);
  assert.equal((await call(request({ op: 'activate' }))).status, 400);
  assert.equal((await call(request({ op: 'verify', cursor: 929 }))).status, 400);
  assert.equal((await call(request({ op: 'status', sql: 'SELECT 1' }))).status, 400);
  const altered = request({ op: 'status' });
  assert.equal((await call(new Request(altered.url, { method: 'POST', headers: altered.headers, body: '{"op":"shared"}' }))).status, 403);
  assert.equal(queries, 0);
});
