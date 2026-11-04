# Exact delta release and rollback

The frozen bundle is identified in `delta-plan.json` and `budget.json`. Its parent is `cn-2026-11-02-full-v2`. The delta adds 2,504 records and inherits the parent's published membership without regenerating or editing its 100,800 records. A future composed-parent release requires explicitly extending the planner's flattening check.

The release consists of 197 import batches, 63 decoded-payload pages, eight table/hash checks and 24 staged production-selector checks: 292 serial checkpoints. Each batch has at most 80 statements and a bounded payload; hashes bind exact statements to the compiled plan. Immutable-row triggers reject conflicting replays. Activation is a separate atomic operation after all verification checkpoints pass.

## Preparation and evidence

Run `.bank-venv/bin/python scripts/bank/content_pipeline.py --out .bank-data/milestone3/release-v3 --release cn-2026-11-03-ideas-v3` to reconstruct the finite content artifact. `delta.mjs MANIFEST BASELINE.sqlite FRESH_DIRECTORY` independently reconstructs every admitted record before preparing the additive SQL. `rehearse-delta.mjs DIRECTORY BASELINE.sqlite REPORT.json` uses real local workerd/D1 to exercise the signed endpoint, duplicate receipts, unchanged active pointer during staging, all-cell acceptance, activation, rollback and retained history. The full release artifact stays in ignored `.bank-data`, outside the public client and deployment archive.

Before publication, preserve the existing public audience and reconcile GitHub/Sites heads. The source helper packages the exact pushed commit. Deploying the new source applies only additive schema migrations; content is still staged separately.

## Bounded production operation

Create a temporary Ed25519 key locally in ignored storage with owner-only permissions. Install only its public SPKI value, a short expiry and the exact bundle allowance as `CONTENT_RELEASE_PUBLIC_KEY`, `CONTENT_RELEASE_EXPIRES_AT` and `CONTENT_RELEASE_ALLOWANCE` through Sites. The private key never enters source, browser storage, tool output or a deployment archive. Deploy the saved source version to apply runtime environment changes.

The current cap is 700,000 reads, 80,000 writes and 110 MB database size. Prior charged usage is 3,855,202 reads and 1,059,527 writes; the cap remains inside the cumulative 5,000,000/1,300,000/150 MB ceiling. It is not a fresh old allowance. The ledger reserves conservative charges before work, retains charges for ambiguous work, measures hosted operations separately, and halts on missing measurements, overspending, changed parent identity or failed verification. Initial 10,000/1,000 overhead covers bounded native preflight/schema actions whose provider counters are unavailable. Do not infer provider remaining quota or a reset time.

Run the serial client with Node's TypeScript support:

```text
node --experimental-strip-types scripts/bank/content-release-client.mjs init PLAN_DIRECTORY PRIVATE_KEY
node --experimental-strip-types scripts/bank/content-release-client.mjs continue PLAN_DIRECTORY PRIVATE_KEY 25
node --experimental-strip-types scripts/bank/content-release-client.mjs activate PLAN_DIRECTORY PRIVATE_KEY
```

Inspect each tranche's receipt, counters and health result before continuing. Repeat `continue` only while checkpoints remain. The client saves exact pending inputs and event receipts atomically, refuses concurrent local clients, and does not blindly retry network failures. A lost response is resumed from the same signed operation; the server's deterministic receipt prevents duplicate corpus writes. A stale server lease lasts two minutes; do not remove or bypass it. A halted ledger needs investigation, not manual reset.

After activation, verify the active pointer, new membership and all-cell selection evidence. Revoke the temporary credential by setting the public key to `disabled`, expiry to `0` and allowance to `null`, then deploy the same saved version again. In this release, removing the keys and redeploying reported success but left runtime signature validation active; explicit disabled values were deployed and verified instead. Both the old `/api/bank-import` and disabled `/api/content-release` must return 404 for POST (unsupported GET returns 405). Normal selection and grading make zero model calls.

## Rollback

While the short-lived operator is available, use:

```text
node --experimental-strip-types scripts/bank/content-release-client.mjs rollback PLAN_DIRECTORY PRIVATE_KEY
```

Rollback is permitted only if the current active pointer is this exact new release, so it cannot overwrite a newer release. It restores the parent pointer and retains all new problem revisions, published release data and historical snapshots. It never deletes accounts, ratings, games or replay data. Once the operator is disabled, re-enable a new short-lived public key for this same compiled plan through the established authorized Sites workflow and deploy before executing rollback; never expose the private key. The original source version 35 remains available if application code also needs reverting. Do not remove additive schema or content tables.

The tracked `release-manifest.json` and `delta-plan.json` preserve the exact preparation descriptor and hashes. Their preparation counters/status are immutable provenance; current imported and active counts are in `coverage.json` and the production receipt.
