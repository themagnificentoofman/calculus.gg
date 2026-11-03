import { readBoundedJson } from './questions-policy.mjs';
export function createProblemReport(deps: { verify: (token: string) => Promise<{ sub?: string }>; quota: (uid: string) => Promise<boolean>; db: D1Database; layout?: 'original' | 'compact' }) {
  return async (request: Request) => {
    const respond = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
    const origin = request.headers.get('origin');
    if (request.method !== 'POST') return respond({ error: 'Use POST.' }, 405);
    if (origin && origin !== new URL(request.url).origin || request.headers.get('sec-fetch-site') === 'cross-site') return respond({ error: 'Origin not allowed.' }, 403);
    const bearer = /^Bearer ([^\s]{1,8192})$/.exec(request.headers.get('authorization') || '');
    if (!bearer) return respond({ error: 'Please sign in.' }, 401);
    let uid: string;
    try { const sub = (await deps.verify(bearer[1])).sub; if (typeof sub !== 'string' || !sub) throw new Error(); uid = sub; } catch { return respond({ error: 'Please sign in again.' }, 401); }
    try {
      const body = await readBoundedJson(request, 4096);
      if (!body || Object.keys(body).some(k => !['problemId', 'problemRevision', 'reason'].includes(k)) || !/^cn_[a-f0-9]{20}$/.test(body.problemId) || !Number.isInteger(body.problemRevision) || body.problemRevision < 1 || typeof body.reason !== 'string' || body.reason.trim().length < 5 || body.reason.length > 2000) return respond({ error: 'Include a problem ID, revision, and a short description.' }, 400);
      if (!await deps.quota(uid)) return respond({ error: 'Please wait a minute before reporting again.' }, 429);
      await deps.db.prepare(`INSERT INTO bank_reports (uid,problem_id,revision,reason,created_at)
        SELECT ?,problem_id,revision,?,? FROM ${deps.layout==='original'?'bank_problems':'cbank_problems'} WHERE problem_id=? AND revision=?
        ON CONFLICT(uid,problem_id,revision) DO UPDATE SET reason=excluded.reason,status='open'`)
        .bind(uid, body.reason.trim(), Date.now(), body.problemId, body.problemRevision).run();
      // Never expose arbitrary-ID content or an answer lookup, even for a report.
      return respond({ ok: true });
    } catch { return respond({ error: 'The report could not be saved. Please retry.' }, 503); }
  };
}
