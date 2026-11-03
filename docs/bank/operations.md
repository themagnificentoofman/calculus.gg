# Operator workflow and rollout

The CLI is deliberately outside the Worker and browser. Access requires the operator's private artifact files and, for hosted import, the existing Cloudflare/Sites deployment permissions. There is no public authoring/import/search endpoint and no client-side admin flag.

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

The server reads only the active published release's small pool catalogue (hard limit 192 families), then samples exact slots through composite primary-key joins. Up to 80 candidates per stage, four stages and 20 result questions: at most 320 probes, 21 SELECT statements, and 96 bound parameters per statement. D1 `batch` reduces network round trips. No `ORDER BY RANDOM()`, full-corpus download, browser answer bank or per-session generation occurs. Cache scope is one selection, so release activation and retirement are checked on each request.

Families receive equal selection opportunity within the requested filter, intentionally differing from uniform row sampling. A round initially caps each family at two questions, excludes the last 100 issued/participated problem IDs, and excludes families from the last 20 entries. Bounded relaxation is: recent families, then a per-family cap based on the number of eligible pools, and only finally recent problems. This preserves recent-problem exclusion when a populous category has few method families. The selected level is recorded in the private round snapshot. A small or heavily retired filter can return `409 INSUFFICIENT_CONTENT` even when a larger unbounded scan could find more rows. It never changes topic/difficulty/tags or starts paid generation.

The host's recent history informs competitive issuance because future participants are unknown; joining participants record the shared set in their own recent history. All competitors still receive the same set. Concurrent issuance uses transactional bounded history updates, but selections can race before those updates; recency is a preference, while within-round identity uniqueness is strict.

## Prepare a hosted release

1. Run all checks and all three content stages, then benchmark the full materialized corpus. Inspect the stratified review and record its automatic/human status accurately.
2. Back up the verified SQLite/JSONL artifacts privately. The committed source contains no full corpus or answer-key download.
3. Apply the additive `drizzle/0001_problem_bank.sql` migration to the existing D1 `DB`. It does not touch quota, account or Firebase tables. This is an explicit SQL migration; preserve it and its journal entry rather than regenerating it from the quota-only Drizzle model.
4. Export the verified release using the operator CLI:

```sh
node scripts/bank/admin.mjs export .bank-data/bank.sqlite .bank-data/d1-export
# With the actual authorized D1 configuration, apply each bank-NNNNN.sql in order:
npx wrangler d1 execute DB --remote --config YOUR_AUTHORIZED_CONFIG --file .bank-data/d1-export/bank-00000.sql
```

Keep a checkpoint of successful chunk filenames/hashes. A chunk is duplicate-safe; changed immutable content must be investigated, never overwritten. SQL exports stage release metadata first. Import every numbered chunk, then independently compare hosted counts, hashes, pool coverage and retired states to the manifest. The final `activate-after-verification.sql` includes a published-count guard and is applied **last**. Do not deploy the new gameplay path against an empty bank. A valid health configuration flag alone does not prove the corpus exists.

5. Through the established Sites helper, package the exact reviewed GitHub feature commit, save the matching version, and deploy after the bank import/activation is verified. Preserve the existing Site ID and public audience. A Sites URL is production, not an isolated preview. A PR and local UI preview are the review surfaces for this milestone.
6. Verify signed-in Test, Rapid, PvP and Multiplayer, joining shared sets, reporting an answered question, saved history, XP and ratings. Capture production D1 latency separately from the local benchmark. Remove any obsolete runtime OpenAI generation credential only through the normal secret-management process if it has no other authorized use.

Cloudflare administrative write access is required for remote D1 import. The connected Sites database tools expose bounded reads, not arbitrary bulk SQL writes. No new Cloudflare credentials or production corpus import are implied by a local SQLite report.

## Rollback

Keep previous compatible bank releases and game-authority versions. To roll back content, activate an earlier verified release whose selected revisions remain approved. Do not reactivate a known bad revision to satisfy a row count. Retirement overrides every release membership. If all compatible content is withdrawn, fail closed with the insufficient-content response.

Code rollback must retain server-authoritative scoring and restrictive Firestore rules. Existing active bank games are self-contained snapshots and can settle without consulting the active release. Do not restore client-writable scores, reset profiles, overwrite receipts or rewrite legacy games. Additive D1 tables need not be removed during code rollback. A legacy live-generator version would resume paid model use; that is an explicit operational rollback, not an automatic empty-bank fallback.
