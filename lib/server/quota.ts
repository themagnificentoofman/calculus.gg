export async function consumeQuota(db: D1Database, uid: string, now = Date.now()) {
  const minute = Math.floor(now / 60000);
  const day = Math.floor(now / 86400000);
  const limits = [
    { key: `user:${uid}:minute`, bucket: minute, period: 60000, limit: 5 },
    { key: `user:${uid}:day`, bucket: day, period: 86400000, limit: 60 },
    { key: 'site:day', bucket: day, period: 86400000, limit: 200 },
  ];
  // An atomic conditional upsert per counter prevents concurrent Workers from
  // overshooting any limit. Rejected attempts can conservatively consume slots
  // in the other counters. Stable keys bound storage to two rows per account.
  const results = await db.batch(limits.map(rule => db.prepare(`
    INSERT INTO ai_quota (key, count, expires_at) VALUES (?, 1, ?)
    ON CONFLICT(key) DO UPDATE SET
      count = CASE WHEN ai_quota.expires_at <= ? THEN 1 ELSE ai_quota.count + 1 END,
      expires_at = MAX(ai_quota.expires_at, excluded.expires_at)
    WHERE ai_quota.expires_at <= ? OR ai_quota.count < ?
    RETURNING count
  `).bind(rule.key, (rule.bucket + 1) * rule.period, now, now, rule.limit)));
  return results.every(result => result.results.length > 0);
}
