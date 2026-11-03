// Temporary, read-only rollout diagnostics. No caller-supplied SQL or row content.
export async function bankPreflight(request: Request, db: D1Database | undefined, publicKey: string | undefined, expiresAt: string | undefined, now = Date.now()) {
  const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
  const expiry = Number(expiresAt);
  if (!db || !publicKey || !Number.isFinite(expiry) || now >= expiry) return reply({ error: 'Unavailable' }, 404);
  if (request.method !== 'POST' || request.headers.has('origin')) return reply({ error: 'Forbidden' }, 403);
  const timestamp = request.headers.get('x-bank-time') || '', signature = request.headers.get('x-bank-signature') || '';
  if (!/^\d{13}$/.test(timestamp) || Math.abs(now - Number(timestamp)) > 60_000 || !/^[A-Za-z0-9+/]{86}==$/.test(signature)) return reply({ error: 'Forbidden' }, 403);
  try {
    const key = await crypto.subtle.importKey('spki', Uint8Array.from(atob(publicKey), c => c.charCodeAt(0)), 'Ed25519', false, ['verify']);
    const message = new TextEncoder().encode(`calculus-ninja-d1-preflight-v1\nPOST\n/api/bank-preflight\n${timestamp}`);
    if (!await crypto.subtle.verify('Ed25519', key, Uint8Array.from(atob(signature), c => c.charCodeAt(0)), message)) return reply({ error: 'Forbidden' }, 403);
  } catch { return reply({ error: 'Forbidden' }, 403); }
  // Never read or interpret request payloads. Cloudflare/Vinext can expose an
  // empty POST as a stream; cancelling that stream can abort the response.
  if (Number(request.headers.get('content-length') || 0) > 0) return reply({ error: 'No body permitted' }, 400);
  let status;
  try { status = await db.prepare('SELECT 1 AS ready').all(); }
  catch (error) { return reply({ readAccess: false, phase: 'fixed-select', diagnostic: String(error).slice(0, 300), capacityConfirmed: false }, 502); }
  const diagnostics: Record<string, unknown> = {};
  for (const [name, sql] of [['pageSize', 'PRAGMA page_size'], ['maxPageCount', 'PRAGMA max_page_count']] as const) {
    try { diagnostics[name] = (await db.prepare(sql).all()).results; }
    catch { diagnostics[name] = { supported: false }; }
  }
  return reply({ readAccess: true, databaseBytes: status.meta?.size_after ?? null, storageDiagnostics: diagnostics,
    capacityConfirmed: false, capacityNote: 'SQLite diagnostics do not establish the hosting account plan, available storage quota or daily write allowance. No content was imported.', expiresAt: expiry });
}
