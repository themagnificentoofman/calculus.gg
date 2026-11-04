import { sqliteTable, text, integer, real, primaryKey, index } from 'drizzle-orm/sqlite-core';

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

// Private selection metadata for new immutable revisions; old rows need no backfill.
export const bankSelectionFeatures = sqliteTable('cbank_selection_features', {
  problemRef: integer('problem_ref').primaryKey(),
  idea: text('idea').notNull(),
  structure: text('structure').notNull(),
  technique: text('technique').notNull(),
  combination: text('combination').notNull(),
  weight: real('weight').notNull(),
});

// Flat, explicit release composition avoids copying the old 260,400 memberships.
export const bankReleaseSources = sqliteTable('cbank_release_sources', {
  releaseId: text('release_id').notNull(),
  sourceReleaseId: text('source_release_id').notNull(),
}, t => [primaryKey({ columns: [t.releaseId, t.sourceReleaseId] })]);

export const bankDeltaLedger = sqliteTable('cbank_delta_ledger', {
  bundleId: text('bundle_id').primaryKey(),
  measuredReads: integer('measured_reads').notNull(),
  measuredWrites: integer('measured_writes').notNull(),
  chargedReads: integer('charged_reads').notNull().default(0),
  chargedWrites: integer('charged_writes').notNull().default(0),
  priorReads: integer('prior_reads').notNull().default(0),
  priorWrites: integer('prior_writes').notNull().default(0),
  databaseBytes: integer('database_bytes').notNull(),
  nextSequence: integer('next_sequence').notNull(),
  verified: integer('verified').notNull(),
  activated: integer('activated').notNull(),
  pendingId: text('pending_id'),
  pendingHash: text('pending_hash'),
  halted: text('halted'),
  updatedAt: text('updated_at').notNull(),
});

// Withdrawal becomes effective only when its introducing release publishes,
// then survives pointer rollback. Canonical data and old round snapshots stay.
export const bankWithdrawnFamilies = sqliteTable('cbank_withdrawn_families', {
  sourceReleaseId: text('source_release_id').notNull(),
  familyId: text('family_id').notNull(),
  introducedBy: text('introduced_by').notNull(),
  reason: text('reason').notNull(),
}, t => [primaryKey({columns:[t.sourceReleaseId,t.familyId,t.introducedBy]})]);

export const bankReleaseExclusions = sqliteTable('cbank_release_exclusions', {
  releaseId: text('release_id').notNull(),
  problemRef: integer('problem_ref').notNull(),
  scope: text('scope').notNull(),
  reason: text('reason').notNull(),
}, t => [primaryKey({columns:[t.releaseId,t.problemRef]}), index('cbank_exclusion_lookup').on(t.problemRef,t.releaseId)]);

// Only explicit reviewed equivalence mappings; default identity is problem_id.
export const bankProblemLineage = sqliteTable('cbank_problem_lineage', {
  problemId: text('problem_id').primaryKey(),
  lineageId: text('lineage_id').notNull(),
});
export const bankFamilyLineage = sqliteTable('cbank_family_lineage', {
  familyId: text('family_id').primaryKey(),
  constructionId: text('construction_id').notNull(),
});
