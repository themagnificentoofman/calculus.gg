-- Additive, schema-only serving layout. Apply after 0001; bulk data is separate.
CREATE TABLE cbank_shared (
  shared_id INTEGER PRIMARY KEY, content_hash BLOB NOT NULL UNIQUE CHECK(length(content_hash)=32),
  metadata_json TEXT NOT NULL
);
CREATE TABLE cbank_problems (
  problem_ref INTEGER PRIMARY KEY,
  problem_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
  content_hash BLOB NOT NULL UNIQUE CHECK(length(content_hash)=32),
  semantic_hash BLOB NOT NULL CHECK(length(semantic_hash)=32),
  shared_id INTEGER NOT NULL REFERENCES cbank_shared(shared_id),
  payload_gzip BLOB NOT NULL CHECK(length(payload_gzip)<=65536),
  UNIQUE(problem_id,revision)
);
CREATE INDEX cbank_semantics ON cbank_problems(semantic_hash);
CREATE TABLE cbank_publication (
  problem_ref INTEGER PRIMARY KEY REFERENCES cbank_problems(problem_ref),
  state TEXT NOT NULL CHECK(state IN ('approved','retired')), retirement_reason TEXT
);
CREATE TABLE cbank_releases (
  release_id TEXT PRIMARY KEY, manifest_json TEXT NOT NULL,
  expected_count INTEGER NOT NULL CHECK(expected_count>0),
  state TEXT NOT NULL DEFAULT 'staging' CHECK(state IN ('staging','published','retired'))
) WITHOUT ROWID;
CREATE TABLE cbank_pools (
  pool_id INTEGER PRIMARY KEY, release_id TEXT NOT NULL REFERENCES cbank_releases(release_id),
  topic TEXT NOT NULL, difficulty TEXT NOT NULL, tag TEXT NOT NULL, family_id TEXT NOT NULL,
  item_count INTEGER NOT NULL CHECK(item_count>0),
  UNIQUE(release_id,difficulty,tag,topic,family_id)
);
CREATE TABLE cbank_slots (
  pool_id INTEGER NOT NULL REFERENCES cbank_pools(pool_id), slot INTEGER NOT NULL CHECK(slot>=0),
  problem_ref INTEGER NOT NULL REFERENCES cbank_problems(problem_ref),
  PRIMARY KEY(pool_id,slot), UNIQUE(pool_id,problem_ref)
) WITHOUT ROWID;
CREATE TABLE cbank_config (key TEXT PRIMARY KEY,value TEXT NOT NULL) WITHOUT ROWID;
-- Receipt and corpus changes must commit together through the agreed import executor.
CREATE TABLE cbank_import_receipts (batch_id TEXT PRIMARY KEY,sha256 TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE cbank_import_checks (ok INTEGER NOT NULL CHECK(ok=1));
CREATE TRIGGER cbank_content_immutable BEFORE UPDATE ON cbank_problems BEGIN SELECT RAISE(ABORT,'Create a new problem revision'); END;
CREATE TRIGGER cbank_content_retained BEFORE DELETE ON cbank_problems BEGIN SELECT RAISE(ABORT,'Retain historical revisions'); END;
CREATE TRIGGER cbank_shared_immutable BEFORE UPDATE ON cbank_shared BEGIN SELECT RAISE(ABORT,'Create new immutable metadata'); END;
CREATE TRIGGER cbank_shared_retained BEFORE DELETE ON cbank_shared BEGIN SELECT RAISE(ABORT,'Retain immutable metadata'); END;
CREATE TRIGGER cbank_slots_immutable BEFORE UPDATE ON cbank_slots BEGIN SELECT RAISE(ABORT,'Create a new release'); END;
CREATE TRIGGER cbank_slots_retained BEFORE DELETE ON cbank_slots BEGIN SELECT RAISE(ABORT,'Retain release membership'); END;
CREATE TRIGGER cbank_pools_immutable BEFORE UPDATE ON cbank_pools BEGIN SELECT RAISE(ABORT,'Create a new release pool'); END;
CREATE TRIGGER cbank_pools_retained BEFORE DELETE ON cbank_pools BEGIN SELECT RAISE(ABORT,'Retain release pools'); END;
CREATE TRIGGER cbank_release_immutable BEFORE UPDATE OF release_id,manifest_json,expected_count ON cbank_releases BEGIN SELECT RAISE(ABORT,'Create a new release manifest'); END;
CREATE TRIGGER cbank_release_retained BEFORE DELETE ON cbank_releases BEGIN SELECT RAISE(ABORT,'Retain release manifests'); END;
CREATE TRIGGER cbank_receipt_immutable BEFORE UPDATE ON cbank_import_receipts BEGIN SELECT RAISE(ABORT,'Import receipt is immutable'); END;
CREATE TRIGGER cbank_receipt_retained BEFORE DELETE ON cbank_import_receipts BEGIN SELECT RAISE(ABORT,'Retain import receipt'); END;
