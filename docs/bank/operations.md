# Operator workflow and rollout

The CLI is deliberately outside the Worker and browser. Access requires the operator's private artifact files and, for hosted import, the supported Sites-managed database permissions. There is no public authoring/import/search endpoint and no client-side admin flag.

## Inspect, report, retire and correct

```sh
# Bounded results with full provenance/validation, optional exact ID:
node scripts/bank/admin.mjs inspect .bank-data/bank.sqlite integration medium
node scripts/bank/admin.mjs inspect .bank-data/bank.sqlite all all cn_EXACT_ID
node scripts/bank/admin.mjs reports .bank-data/bank.sqlite
node scripts/bank/admin.mjs retire .bank-data/bank.sqlite cn_EXACT_ID 1 'Verified mathematical correction required'
```

The review UI copies `problemId@revision` and accepts an authenticated report. Reports are stored in D1, limited independently of authoring, and do not send email automatically. An identical user's repeated report updates the same record. The endpoint returns no problem content and cannot reveal active-match answers.

Corrections must first be authored as a supported recipe and independently verified. Preserve the original permanent ID, increment the revision, recompute the content hash using the corrected immutable record, and place exactly one canonical JSONL record in a private file. The checker reconstructs all mathematical fields; arbitrary edited LaTeX or an approval flag is insufficient.

```sh
node scripts/bank/admin.mjs revise .bank-data/bank.sqlite corrected.jsonl 'Corrected initial condition'
```

`revise` inserts the next immutable revision and retires prior revisions. It does not make the correction playable until it belongs to a newly validated release. Keep the old revision and its retirement reason. A changed mathematical template or explanation requires a new revision for any retained problem ID; never update `payload_json`. Existing game snapshots and results remain unchanged. A pending unused set is rechecked against publication state before a new game is created. D1 and Firebase do not share a distributed transaction; a retirement concurrent with that final check has a narrow race, while already-issued active snapshots are intentionally preserved.

There were no retained legacy preset identifiers in the initial migration. `bank_legacy_ids` provides the future explicit source/legacy-ID mapping table; no mapping count is fabricated.

## Selection policy

The compact server reads only the active published release's small indexed pool catalogue (hard limit 192 families), then samples exact integer pool/slot keys. Up to 80 identity candidates per stage, four stages and 20 result questions: at most 320 probes, ten SELECT statements and 80 bound parameters per statement. Only the final selected payloads are fetched, decompressed and checked against their canonical content hashes. D1 `batch` reduces round trips. No `ORDER BY RANDOM()`, corpus scan/download, browser answer bank or per-session generation occurs. Cache scope is one selection, so activation and retirement are checked on each request. The original selector remains only for authoring-layout tests/comparisons; runtime uses `compact-bank-selection.ts`.

Families receive equal selection opportunity within the requested filter, intentionally differing from uniform row sampling. A round initially caps each family at two questions, excludes the last 100 issued/participated problem IDs, and excludes families from the last 20 entries. Bounded relaxation is: recent families, then a per-family cap based on the number of eligible pools, and only finally recent problems. This preserves recent-problem exclusion when a populous category has few method families. The selected level is recorded in the private round snapshot. A small or heavily retired filter can return `409 INSUFFICIENT_CONTENT` even when a larger unbounded scan could find more rows. It never changes topic/difficulty/tags or starts paid generation.

The host's recent history informs competitive issuance because future participants are unknown; joining participants record the shared set in their own recent history. All competitors still receive the same set. Concurrent issuance uses transactional bounded history updates, but selections can race before those updates; recency is a preference, while within-round identity uniqueness is strict.

## Prepare a hosted release

This Site is managed only through Sites. Read access is established. The supported authenticated bulk-import method, managed storage ceiling/remaining capacity and read/write allowances are separate unresolved questions. Native Sites database tools are read-only. A successful read or SQLite page diagnostic does not establish an allocation. Do not request a new personal Cloudflare account, substitute the placeholder Wrangler database ID, or assume vanilla Cloudflare plan limits apply. Use the [unsent capacity/import request](support-request.md) to obtain the actual supported path and allowance.

1. Preserve the verified original corpus and its checksums. The current seed is already complete; **do not regenerate it**. Work on a copy. `storage-audit.py` provides read-only per-object `dbstat` allocation, payload, unused-space, page and index-write estimates. The original authoring format remains the mathematical verification source.
2. Build the serving artifact from that verified copy, then verify/benchmark it. The output must be a new path. `sync` appends previously verified corrections/releases to the existing serving registry; it never renumbers existing references or revives retirement. `verify` compares every canonical reconstructed record, publication state and pool membership with the source. Keep pilot/expanded membership artifacts separately.

```sh
node scripts/bank/compact.mjs build .bank-data/compact/source.sqlite .bank-data/compact/serving.sqlite cn-2026-11-02-full-v2 .bank-data/compact/conversion.json
python3 scripts/bank/storage-audit.py .bank-data/compact/serving.sqlite .bank-data/compact/compact-audit.json
node --experimental-strip-types scripts/bank/benchmark.mjs .bank-data/compact/serving.sqlite .bank-data/compact/benchmark.json compact
node scripts/bank/compact-import.mjs export .bank-data/compact/serving.sqlite .bank-data/compact/import
```

`build` activates only the local artifact for benchmarking. Exports always stage release metadata and exclude active configuration. The initial export has 1,850 JSON batches of SQL statements, at most 250 data rows per batch, and a checksum manifest. The complete bank and compressed payloads are private artifacts outside Git, public assets and deployment archives. Shared metadata and payloads are append-only; immutable conflicts abort. The full export is 246,285,283 bytes of batch JSON; this transfer volume differs from the 90,337,280-byte rehearsed database allocation.

3. Rehearse against a fresh **local** target; a second run must skip completed receipts. Full verification decodes/re-hashes every record, checks the identity/publication/membership digests, coverage and release manifests, using indexed pagination. It does not infer correctness from counts alone.

```sh
node scripts/bank/compact-import.mjs apply-local .bank-data/compact/import-rehearsal.sqlite .bank-data/compact/import
node scripts/bank/compact-import.mjs apply-local .bank-data/compact/import-rehearsal.sqlite .bank-data/compact/import
node scripts/bank/compact-import.mjs verify-local .bank-data/compact/import-rehearsal.sqlite .bank-data/compact/import
node scripts/bank/worker-smoke.mjs
```

4. Obtain a supported Sites import executor and a fresh allowance covering this exact bundle. Record the ceiling, occupancy, agreed storage/write/read reserves, reset window, shared usage reservation and validity deadline. The proposed initial support envelope is 113 MB for the bank with 25% headroom plus existing usage, and 1.3 million writes for the initial import plus overhead; neither is an approved allocation. Future releases/revisions need a fresh capacity assessment. Do not start hosted mutation while any required allowance or method is unknown.
5. Through that executor, apply additive, bounded, schema-only migrations `0001_problem_bank.sql` and `0002_compact_bank.sql` after the existing quota migration. Never change already applied migrations or embed the corpus in migrations. Check supported statement/batch/payload limits before adapting the prepared format. `0002` does not modify original data.
6. The provider-neutral `runImport` function requires the supported atomic `prepare`/`batch` adapter and a `refreshAllowance` callback for every hosted invocation/resume. It is **not a currently available hosted import path**. Its approval object binds the Site ID, `DB`, exact bundle ID, supported method, fresh occupancy/budgets/reserves, shared-usage reservation and expiry. No credential or guessed HTTP endpoint is configured. Local CLI commands deliberately expose no hosted switch.

Every batch writes its checksum receipt in the same transaction as the data. On an interrupted response, read the receipt before retrying. Refresh actual usage on resume; a lost response can still have committed and consumed budget. Changed bytes/receipts or immutable conflicts stop the import. Replayed approvals cannot unretire content. `local-checkpoints.jsonl` and returned measurements record actual `rows_read`, `rows_written`, `size_after` and duration when supplied; missing provider counters remain null, never fabricated from SQLite changes. The hosted runner stops if counters disappear, the allowance expires or agreed headroom is reached. The adapter must also honor provider rate limits. Preserve application quota usage and the agreed shared-account reservation throughout.

7. While still staging, use the supported read path to run `verifyImported` against the exact plan. Its `onPage` callback must account for actual read counters and stop before the separately reserved verification budget is exhausted. Verify all 100,800 records and 260,400 memberships, publication state, coverage and release manifests, and run representative selection in the supported staging environment. The current verification scans are bounded pages (100 payloads / 1,000 memberships); they are operator work, never a game request.
8. Only after hosted verification succeeds, use `activateVerified` with a fresh verification result and the matching release. Activation uses an atomic approved-count/unique-ID guard, then publishes and sets the compact active release. A retired or incomplete release cannot activate. Capture activation resource metadata and confirm representative selection before deploying gameplay. Quota/account/Firebase data remains untouched.
9. Package the exact reviewed commit through the established Sites source helper and save a **new matching version**. Saved version 23 uses the original schema and cannot serve the compact layout. Saving source/version is separate from deployment. Preserve the existing Site ID and public audience; every Sites deployment URL is production. The healthy live version stays available until data readiness and resource checks pass.
10. Deploy only the matching saved version after activation. Verify signed-in Test, Rapid, PvP and Multiplayer, shared sets, reporting after answers, history, XP and ratings. Measure production latency/counters separately. Do not remove runtime credentials while the retained live path needs them. A health configuration flag alone proves neither bank contents nor capacity.

## Corrections in the compact serving registry

Use the original independently verified authoring correction workflow above, then `compact.mjs sync SOURCE EXISTING_SERVING_DB NEW_RELEASE`. Reuse that same serving database so internal IDs remain stable. Retain old content and publication reasons; create a new release for corrected memberships. New revision metadata may use a new immutable shared object. Re-export and apply changed state through the agreed operator path; stale approval exports cannot revive a retired revision. For an urgent retirement, the supported executor may apply a parameterized update to `cbank_publication` by the indexed external ID/revision in `cbank_problems`; there is no public admin endpoint. An existing active game uses its private snapshot and can still settle.

## Rollback

Keep previous compatible bank releases and game-authority versions. To roll back content, activate an earlier verified release whose selected revisions remain approved. Do not reactivate a known bad revision to satisfy a row count. Retirement overrides every release membership. If all compatible content is withdrawn, fail closed with the insufficient-content response.

Code rollback must retain server-authoritative scoring and restrictive Firestore rules. Existing active bank games are self-contained snapshots and can settle without consulting the active release. Do not restore client-writable scores, reset profiles, overwrite receipts or rewrite legacy games. Additive D1 tables need not be removed during code rollback. A legacy live-generator version would resume paid model use; that is an explicit operational rollback, not an automatic empty-bank fallback.
