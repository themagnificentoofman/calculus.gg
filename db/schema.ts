import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const aiQuota = sqliteTable('ai_quota', {
  key: text('key').primaryKey(),
  count: integer('count').notNull(),
  expiresAt: integer('expires_at').notNull(),
});
