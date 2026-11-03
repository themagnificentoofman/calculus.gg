import { PILOT } from './bank-pilot-plan.mjs';
const encoder = new TextEncoder();
const reply = (body, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
export const signingMessage = (timestamp, hash) => `calculus-ninja-bank-pilot-v1\n${PILOT.projectId}\nPOST\n/api/bank-import\n${timestamp}\n${hash}`;
export async function digest(bytes) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join(''); }
export function metrics(results) {
  const list = Array.isArray(results) ? results : [results];
  const sum = key => list.every(r => Number.isFinite(r.meta?.[key])) ? list.reduce((n, r) => n + r.meta[key], 0) : null;
  return { rowsRead: sum('rows_read'), rowsWritten: sum('rows_written'), sizeAfter: list.at(-1)?.meta?.size_after ?? null, sqlDurationMs: sum('duration') };
}
async function boundedBody(request) {
  const declared = request.headers.get('content-length');
  if (declared !== null && (!/^\d+$/.test(declared) || Number(declared) > 900000)) throw Error('body');
  const reader = request.body?.getReader();
  if (!reader) throw Error('body');
  const chunks = []; let size = 0; const deadline = Date.now() + 10000;
  try {
    while (true) {
      let timer;
      const part = await Promise.race([reader.read(), new Promise((_, reject) => { timer = setTimeout(() => reject(Error('body')), Math.max(1, deadline - Date.now())); })]).finally(() => clearTimeout(timer));
      if (part.done) break;
      size += part.value.length; if (size > 900000 || Date.now() > deadline) throw Error('body');
      chunks.push(part.value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return bytes;
}
const hasOnly = (value, fields) => value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).every(k => fields.includes(k));
const receiptId = index => PILOT.bundleId + '/' + index;
export async function bankPilot(request, db, publicKey, expiresAt, now = Date.now()) {
  const expiry = Number(expiresAt);
  if (!db || !publicKey || !Number.isFinite(expiry) || now >= expiry) return reply({ error: 'Unavailable' }, 404);
  if (request.method !== 'POST' || new URL(request.url).pathname !== '/api/bank-import' || request.headers.has('origin')) return reply({ error: 'Forbidden' }, 403);
  const timestamp = request.headers.get('x-bank-time') || '', signature = request.headers.get('x-bank-signature') || '', bodyHash = request.headers.get('x-bank-body-sha256') || '';
  if (!/^\d{13}$/.test(timestamp) || Math.abs(now - Number(timestamp)) > 60000 || !/^[A-Za-z0-9+/]{86}==$/.test(signature) || !/^[a-f0-9]{64}$/.test(bodyHash)) return reply({ error: 'Forbidden' }, 403);
  try {
    const key = await crypto.subtle.importKey('spki', Uint8Array.from(atob(publicKey), c => c.charCodeAt(0)), 'Ed25519', false, ['verify']);
    if (!await crypto.subtle.verify('Ed25519', key, Uint8Array.from(atob(signature), c => c.charCodeAt(0)), encoder.encode(signingMessage(timestamp, bodyHash)))) return reply({ error: 'Forbidden' }, 403);
  } catch { return reply({ error: 'Forbidden' }, 403); }
  // Authenticate before reading bodies or touching D1. Authorization includes exact body hash.
  let input;
  try {
    const bytes = await boundedBody(request);
    if (await digest(bytes) !== bodyHash) return reply({ error: 'Body hash mismatch' }, 403);
    input = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch { return reply({ error: 'Invalid bounded JSON body' }, 400); }
  if (Date.now() >= expiry) return reply({ error: 'Expired' }, 403);
  const started = performance.now();
  try {
    if (input?.op === 'status' && hasOnly(input, ['op'])) {
      const counts = await db.prepare(`SELECT
        (SELECT count(*) FROM (SELECT shared_id FROM cbank_shared LIMIT 73)) AS shared,
        (SELECT count(*) FROM (SELECT problem_ref FROM cbank_problems LIMIT 929)) AS problems,
        (SELECT count(*) FROM (SELECT problem_ref FROM cbank_publication LIMIT 1)) AS publication,
        (SELECT count(*) FROM (SELECT release_id FROM cbank_releases LIMIT 1)) AS releases,
        (SELECT value FROM cbank_config WHERE key='active_release') AS activeRelease,
        (SELECT count FROM ai_quota WHERE key='site:day') AS currentGameCounter`).all();
      const receipts = await db.prepare('SELECT batch_id,sha256 FROM cbank_import_receipts WHERE batch_id IN (?,?,?,?) ORDER BY batch_id').bind(...PILOT.batches.map((_, i) => receiptId(i))).all();
      return reply({ bundleId: PILOT.bundleId, cap: 4, counts: counts.results[0], receipts: receipts.results, metrics: metrics([counts, receipts]), serverMs: performance.now() - started, allowanceKnown: false });
    }
    if (input?.op === 'verify' && hasOnly(input, ['op', 'cursor']) && Number.isInteger(input.cursor) && input.cursor >= 0 && input.cursor <= PILOT.maxProblemRef) {
      const result = await db.prepare('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) WHERE problem_ref>? AND problem_ref<=? ORDER BY problem_ref LIMIT 50').bind(input.cursor, PILOT.maxProblemRef).all();
      return reply({ rows: result.results, metrics: metrics(result), serverMs: performance.now() - started });
    }
    if (input?.op === 'shared' && hasOnly(input, ['op'])) {
      const result = await db.prepare('SELECT * FROM cbank_shared ORDER BY shared_id LIMIT 73').all();
      return reply({ rows: result.results, metrics: metrics(result), serverMs: performance.now() - started });
    }
    if (input?.op !== 'import' || !hasOnly(input, ['op', 'index', 'text']) || !Number.isInteger(input.index) || input.index < 0 || input.index >= PILOT.batches.length || typeof input.text !== 'string') return reply({ error: 'Outside four-batch pilot' }, 400);
    const batch = PILOT.batches[input.index], bytes = encoder.encode(input.text);
    if (bytes.length !== batch.bytes || await digest(bytes) !== batch.sha256) return reply({ error: 'Batch checksum mismatch' }, 400);
    const statements = JSON.parse(input.text);
    if (!Array.isArray(statements) || statements.length !== 250 || statements.some(s => typeof s !== 'string')) return reply({ error: 'Invalid batch' }, 400);
    const old = await db.prepare('SELECT sha256 FROM cbank_import_receipts WHERE batch_id=?').bind(receiptId(input.index)).all();
    if (old.results.length) {
      if (old.results[0].sha256 !== batch.sha256) return reply({ error: 'Receipt conflict' }, 409);
      return reply({ index: input.index, sha256: batch.sha256, skipped: true, metrics: metrics(old), serverMs: performance.now() - started });
    }
    const guards = [db.prepare("INSERT INTO cbank_import_checks SELECT 0 WHERE EXISTS(SELECT 1 FROM cbank_config WHERE key='active_release')")];
    if (input.index > 0) guards.push(db.prepare('INSERT INTO cbank_import_checks SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM cbank_import_receipts WHERE batch_id=? AND sha256=?)').bind(receiptId(input.index - 1), PILOT.batches[input.index - 1].sha256));
    // Plain receipt INSERT makes a concurrent duplicate roll back the entire transaction.
    // Only the four allowlisted byte-for-byte batches can reach this D1 call.
    const result = await db.batch([...guards, ...statements.map(s => db.prepare(s)), db.prepare('INSERT INTO cbank_import_receipts VALUES (?,?)').bind(receiptId(input.index), batch.sha256)]);
    if (result.some(r => !r.success)) throw Error('D1 batch failed');
    return reply({ index: input.index, sha256: batch.sha256, skipped: false, metrics: metrics([old, ...result]), serverMs: performance.now() - started });
  } catch (error) {
    // Never send SQL or answer-bearing error messages to the caller/logs.
    const text = String(error);
    const category = /quota|limit.*exceed|exceed.*limit|too many/i.test(text) ? 'quota-or-limit' : /overload|busy/i.test(text) ? 'overloaded' : /timeout|timed out/i.test(text) ? 'timeout' : /constraint/i.test(text) ? 'constraint' : 'database';
    return reply({ error: 'Database operation failed; reconcile receipts before retrying', category, serverMs: performance.now() - started }, 503);
  }
}
