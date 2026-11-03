# Costs and offline authoring

The deterministic seed uses **zero OpenAI API calls and $0 OpenAI spend**. No paid job was submitted. Local CPU, disk and operator time are not represented as zero-cost cloud services. Actual cost per automatically approved seed instance is $0 in model charges; no human-review cost is claimed.

## Protected Batch proposals

The offline `scripts/bank/author-batch.mjs` CLI uses operator environment credentials only. Gameplay never imports it. It requests family specifications, domain proofs, verifier ideas and distractor rationales, rather than one model call per materialized row. Structured output is still untrusted and stored as a quarantined proposal. Its approval/publication counters remain zero until a supported independently verified recipe exists.

```sh
node scripts/bank/author-batch.mjs plan .bank-data/authoring 100
# Only with an explicitly authorized operator budget and credential:
node scripts/bank/author-batch.mjs submit .bank-data/authoring 0.53
node scripts/bank/author-batch.mjs collect .bank-data/authoring
```

The dry run creates 100 deterministic request IDs for `gpt-6-luna`, an 8,000-token conservative input ceiling and 8,000-token output limit per request, and a maximum reserved envelope of **$0.528**, including two attempt-equivalents and a 10% surcharge reserve. No spending is authorized by `plan`. Submission reconstructs the bounded plan and checks the exact uploaded payload, requires an explicit cap covering that envelope, and refuses a cap above the operator ceiling of $5. Current implementation makes one submission and performs no automatic paid retries; failed items require another reviewed plan. This conservative reservation does not claim a second attempt has been executed.

The price snapshot checked November 2, 2026 is Batch $0.05 input/$0.25 output per million short-context tokens. Check [official pricing](https://developers.openai.com/api/docs/pricing) and [model support](https://developers.openai.com/api/docs/models/gpt-6-luna) before authorizing a future run. These rates are configuration, not a permanent price guarantee.

The [Batch guide](https://developers.openai.com/api/docs/guides/batch) documents asynchronous JSONL processing and unordered outputs. Results are matched by `custom_id`, never file order. The CLI stores the plan, request file, batch/file IDs, response/error files, per-request status and usage. Duplicate collections do not rebill ledger entries. Refusals, incomplete output and malformed proposals are rejected. A network interruption during submission leaves an ambiguous checkpoint and refuses blind resubmission; reconcile using batch `job_id` metadata before proceeding. A completed request in an expired/failed batch can still cost money. Missing usage remains explicitly unreconciled. Recorded token cost is computed from the pinned rate snapshot; the provider billing statement is authoritative for actual surcharges or discounts. Cost per approved proposal is null while approvals are zero.

## Database and serving costs

The existing D1 binding is reused. The bank adds immutable payloads, release slots/tag indexes, publication records and reports. Firebase still incurs profile/game transaction, snapshot, listener and history costs; Workers still incur request and CPU costs. No new hosting budget or plan was purchased.

[Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) checked November 2, 2026 lists paid-plan included usage of 25 billion rows read/month, 50 million rows written/month and 5 GB storage, then $0.001/million reads, $1/million writes and $0.75/GB-month. Index maintenance also affects writes. The free plan limits writes to 100,000/day and an individual database to 500 MB; a full indexed import may exceed those limits even though the problem count is only 100,800. These public plan figures do not establish the Sites-managed allocation. Obtain its actual ceiling, remaining capacity, read/write allowance, reset window and shared usage through Sites before rollout; no personal Cloudflare account is required by the current evidence. See the [measured compact comparison](storage/README.md).

The measured artifact size and sampler latency are recorded in `releases/benchmark.json`. Those are local SQLite measurements using production SQL, excluding network, Worker cold starts, token verification and Firebase commits. No live paid-generation benchmark was performed; the old 70-second generation timeout is a bound, not a latency measurement. A numerical speedup claim against that timeout would be misleading. Production latency and billed database counters remain deployment verification tasks.
