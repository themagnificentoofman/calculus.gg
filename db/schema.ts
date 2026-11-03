import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const aiQuota = sqliteTable('ai_quota', {
  key: text('key').primaryKey(),
  count: integer('count').notNull(),
  expiresAt: integer('expires_at').notNull(),
});

// One durable operation ledger. Corpus inserts and receipts remain in their existing tables.
export const bankOperatorLedger = sqliteTable('cbank_operator_ledger', {
  bundleId: text('bundle_id').primaryKey(),
  measuredReads: integer('measured_reads').notNull(),
  measuredWrites: integer('measured_writes').notNull(),
  overheadReads: integer('overhead_reads').notNull(),
  overheadWrites: integer('overhead_writes').notNull(),
  databaseBytes: integer('database_bytes').notNull(),
  nextSequence: integer('next_sequence').notNull(),
  trancheStart: integer('tranche_start').notNull(),
  trancheEnd: integer('tranche_end').notNull(),
  pilotVerified: integer('pilot_verified').notNull(),
  problemPages: integer('problem_pages').notNull(),
  membershipPages: integer('membership_pages').notNull(),
  metadataVerified: integer('metadata_verified').notNull(),
  selectionCells: integer('selection_cells').notNull(),
  activated: integer('activated').notNull(),
  pendingId: text('pending_id'),
  pendingHash: text('pending_hash'),
  pendingReads: integer('pending_reads').notNull(),
  pendingWrites: integer('pending_writes').notNull(),
  lastId: text('last_id'),
  lastHash: text('last_hash'),
  lastResult: text('last_result'),
  halted: text('halted'),
  updatedAt: text('updated_at').notNull(),
});
