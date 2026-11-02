import { CONTACT_COOLDOWN_SECONDS, CONTACT_DAILY_LIMIT, CONTACT_TOPICS, type ContactTopic } from '../contact.ts';
import { readBoundedJson } from './questions-policy.mjs';

export const CONTACT_RECIPIENT = 'zacharyzheng2009@gmail.com';
type Identity = { sub?: unknown; email?: unknown };
type ContactMessage = { uid: string; email: string; topic: ContactTopic; message: string; requestId: string };
const json = (body: unknown, status = 200, retry = 0) => Response.json(body, { status, headers: {
  'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...(retry > 0 ? { 'Retry-After': String(retry) } : {}),
} });
const emailIsValid = (value: unknown): value is string => typeof value === 'string' && value.length <= 254 && /^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(value);

function quotaRules(uid: string, now: number) {
  const midnight = (Math.floor(now / 86400000) + 1) * 86400000;
  return [
    { key: `contact:${uid}:cooldown`, limit: 1, expires: now + CONTACT_COOLDOWN_SECONDS * 1000 },
    { key: `contact:${uid}:day`, limit: CONTACT_DAILY_LIMIT, expires: midnight },
    { key: 'contact:site:day', limit: 100, expires: midnight },
  ];
}

export async function contactRetryAfter(db: D1Database, uid: string, now = Date.now()) {
  let retry = 0;
  for (const rule of quotaRules(uid, now)) {
    const [result] = await db.batch<{ expires_at: number }>([db.prepare('SELECT expires_at FROM ai_quota WHERE key = ? AND count >= ? AND expires_at > ?').bind(rule.key, rule.limit, now)]);
    if (result.results.length) retry = Math.max(retry, Math.ceil((Number(result.results[0].expires_at) - now) / 1000));
  }
  return retry;
}

// Each conditional UPSERT is atomic across requests and Worker instances.
// Reject account spam before consuming the shared delivery budget.
export async function reserveContactQuota(db: D1Database, uid: string, now = Date.now()) {
  for (const rule of quotaRules(uid, now)) {
    const [result] = await db.batch([db.prepare(`
      INSERT INTO ai_quota (key, count, expires_at) VALUES (?, 1, ?)
      ON CONFLICT(key) DO UPDATE SET
        count = CASE WHEN ai_quota.expires_at <= ? THEN 1 ELSE ai_quota.count + 1 END,
        expires_at = MAX(ai_quota.expires_at, excluded.expires_at)
      WHERE ai_quota.expires_at <= ? OR ai_quota.count < ?
      RETURNING count
    `).bind(rule.key, rule.expires, now, now, rule.limit)]);
    if (!result.results.length) return Math.max(1, await contactRetryAfter(db, uid, now));
  }
  return 0;
}

export function resendContactSender(apiKey: string, from: string, transport: typeof fetch = fetch) {
  return async ({ uid, email, topic, message, requestId }: ContactMessage) => {
    const result = await transport('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json', 'Idempotency-Key': `contact/${uid}/${requestId}` },
      body: JSON.stringify({ from, to: [CONTACT_RECIPIENT], reply_to: email,
        subject: `[Calculus Ninja] ${CONTACT_TOPICS[topic]}`,
        text: `Account email: ${email}\nAccount ID: ${uid}\nTopic: ${CONTACT_TOPICS[topic]}\n\n${message}` }),
      signal: AbortSignal.timeout(12000),
    });
    if (!result.ok || typeof (await result.json() as { id?: unknown }).id !== 'string') throw new Error('Email delivery unavailable');
  };
}

export function createContactApi(deps: {
  verify: (token: string) => Promise<Identity>;
  reserve: (uid: string, now: number) => Promise<number>;
  status: (uid: string, now: number) => Promise<number>;
  send: (message: ContactMessage) => Promise<void>;
  now?: () => number;
}) {
  return async (request: Request) => {
    if (!['GET', 'POST'].includes(request.method)) return json({ error: 'Use GET or POST.' }, 405);
    const origin = request.headers.get('origin');
    if ((origin && origin !== new URL(request.url).origin) || request.headers.get('sec-fetch-site') === 'cross-site') return json({ error: 'Request origin is not allowed.' }, 403);
    const token = /^Bearer ([^\s]+)$/.exec(request.headers.get('authorization') || '')?.[1];
    if (!token || token.length > 8192) return json({ error: 'Please sign in to contact us.' }, 401);
    let identity: Identity;
    try {
      identity = await deps.verify(token);
      if (typeof identity.sub !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(identity.sub) || !emailIsValid(identity.email)) throw new Error('identity');
    } catch { return json({ error: 'Your sign-in has expired or has no email address. Please sign in again.' }, 401); }
    const uid = identity.sub as string, email = identity.email as string;
    const now = deps.now?.() ?? Date.now();
    try {
      if (request.method === 'GET') return json({ retryAfter: await deps.status(uid, now) });
      let body;
      try { body = await readBoundedJson(request, 20000); } catch { return json({ error: 'Send a valid message of at most 4,000 characters.' }, 400); }
      if (!body || typeof body !== 'object' || Array.isArray(body) || Object.keys(body).some(key => !['topic', 'message', 'requestId'].includes(key)) ||
        typeof body.topic !== 'string' || !Object.hasOwn(CONTACT_TOPICS, body.topic) ||
        typeof body.message !== 'string' || body.message.trim().length < 10 || body.message.length > 4000 || /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(body.message) ||
        typeof body.requestId !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(body.requestId)) {
        return json({ error: 'Choose a topic and write a message between 10 and 4,000 characters.' }, 400);
      }
      const retry = await deps.reserve(uid, now);
      if (retry) return json({ error: retry > 60 ? 'The daily contact limit has been reached. Please try again later.' : 'Please wait before sending another message.', retryAfter: retry }, 429, retry);
      try { await deps.send({ uid, email, topic: body.topic as ContactTopic, message: body.message.trim(), requestId: body.requestId }); }
      catch {
        return json({ error: 'Delivery could not be confirmed. Your message is still here; please wait a minute and retry.', retryAfter: CONTACT_COOLDOWN_SECONDS }, 503, CONTACT_COOLDOWN_SECONDS);
      }
      return json({ ok: true, retryAfter: CONTACT_COOLDOWN_SECONDS });
    } catch { return json({ error: 'Contact is temporarily unavailable. Please try again later.' }, 503); }
  };
}
