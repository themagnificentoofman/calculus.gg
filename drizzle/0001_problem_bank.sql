-- Content and memberships are append-only. Publication/retirement is separate.
CREATE TABLE bank_releases (
  release_id TEXT PRIMARY KEY, manifest_json TEXT NOT NULL,
  expected_count INTEGER NOT NULL CHECK(expected_count > 0),
  state TEXT NOT NULL DEFAULT 'staging' CHECK(state IN ('staging','published','retired'))
);
CREATE TABLE bank_problems (
  problem_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
  content_hash TEXT NOT NULL UNIQUE, semantic_hash TEXT NOT NULL,
  topic TEXT NOT NULL, difficulty TEXT NOT NULL, family_id TEXT NOT NULL,
  payload_json TEXT NOT NULL, PRIMARY KEY(problem_id, revision)
);
CREATE INDEX bank_semantics ON bank_problems(semantic_hash);
CREATE TRIGGER bank_content_immutable BEFORE UPDATE ON bank_problems BEGIN SELECT RAISE(ABORT, 'Create a new problem revision'); END;
CREATE TRIGGER bank_content_retained BEFORE DELETE ON bank_problems BEGIN SELECT RAISE(ABORT, 'Retire content; retain historical revisions'); END;
CREATE TABLE bank_publication (
  problem_id TEXT NOT NULL, revision INTEGER NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('approved','retired')),
  retirement_reason TEXT, PRIMARY KEY(problem_id, revision),
  FOREIGN KEY(problem_id, revision) REFERENCES bank_problems(problem_id, revision)
);
CREATE TABLE bank_pools (
  release_id TEXT NOT NULL, topic TEXT NOT NULL, difficulty TEXT NOT NULL,
  tag TEXT NOT NULL, family_id TEXT NOT NULL, item_count INTEGER NOT NULL CHECK(item_count > 0),
  PRIMARY KEY(release_id, topic, difficulty, tag, family_id)
);
CREATE TABLE bank_slots (
  release_id TEXT NOT NULL, topic TEXT NOT NULL, difficulty TEXT NOT NULL,
  tag TEXT NOT NULL, family_id TEXT NOT NULL, slot INTEGER NOT NULL,
  problem_id TEXT NOT NULL, revision INTEGER NOT NULL,
  PRIMARY KEY(release_id, topic, difficulty, tag, family_id, slot),
  UNIQUE(release_id, tag, problem_id),
  FOREIGN KEY(problem_id, revision) REFERENCES bank_problems(problem_id, revision)
);
CREATE TRIGGER bank_slots_immutable BEFORE UPDATE ON bank_slots BEGIN SELECT RAISE(ABORT, 'Create a new release'); END;
CREATE TRIGGER bank_slots_retained BEFORE DELETE ON bank_slots BEGIN SELECT RAISE(ABORT, 'Retain release membership'); END;
CREATE TABLE bank_config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE bank_legacy_ids (source TEXT NOT NULL, legacy_id TEXT NOT NULL, problem_id TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(source, legacy_id));
-- No mutable telemetry is stored inside immutable mathematical content.
CREATE TABLE bank_statistics (problem_id TEXT NOT NULL, revision INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, correct INTEGER NOT NULL DEFAULT 0, solve_ms INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(problem_id, revision));
CREATE TABLE bank_reports (uid TEXT NOT NULL, problem_id TEXT NOT NULL, revision INTEGER NOT NULL, reason TEXT NOT NULL, created_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open', PRIMARY KEY(uid, problem_id, revision));
CREATE TRIGGER bank_release_manifest_immutable BEFORE UPDATE OF release_id,manifest_json,expected_count ON bank_releases BEGIN SELECT RAISE(ABORT, 'Create a new release manifest'); END;
CREATE TRIGGER bank_pools_immutable BEFORE UPDATE ON bank_pools BEGIN SELECT RAISE(ABORT, 'Create a new release pool'); END;
CREATE TRIGGER bank_pools_retained BEFORE DELETE ON bank_pools BEGIN SELECT RAISE(ABORT, 'Retain release pools'); END;
-- Always empty. Exported SQL deliberately violates this check on an immutable conflict.
CREATE TABLE bank_import_checks (ok INTEGER NOT NULL CHECK(ok=1));
