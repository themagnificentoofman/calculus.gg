Subject: Managed D1 capacity and resumable import for Calculus Ninja

Hello Sites support,

I manage Calculus Ninja only through Sites. Please help confirm the supported import path and resource allowance for its existing managed D1 database:

- Site: https://calculus.ninja
- Sites project: `appgprj_6ad91db3d4788191b3e73074e27447f5`
- D1 binding: `DB`
- Current production schema: `ai_quota` only; zero imported or active bank problems. A previous read diagnostic reported 32,768 bytes. Read access works, but it did not establish the allocation or write allowance.

We have 100,800 locally verified problems. The original SQLite layout is 535,515,136 bytes with approximately 1.47 million estimated row/index writes. A lossless compact layout now measures 90,050,560 bytes. A fresh import rehearsal measures **90,337,280 bytes including 1,850 batch receipts**, with **1,027,167 estimated row/index writes** for data and receipts. These are local measurements and estimates, not production D1 billing counters. All original IDs, revisions, content hashes and validation evidence are preserved.

Could you confirm:

1. The per-database storage ceiling and current remaining capacity, including indexes. We propose reserving at least **113 MB for the compact bank plus its initial 25% headroom**, in addition to existing application usage. Please confirm the operational headroom and capacity for future revisions/releases; the proposed reserve is not an assertion of our allocation.
2. The available write allowance, reset window/time zone, shared-account usage, and whether this import plus schema, activation, verification/retry overhead and normal application traffic is permitted. A provisional **1.3-million-write envelope** provides about 26% above the seed/receipt estimate; please confirm or replace it with an agreed allowance. Please also confirm the read budget for complete post-import hash/coverage verification.
3. The supported authenticated bulk-import method for this Sites-managed binding, without requiring a new personal Cloudflare account. We have 1,850 checksummed batches (at most 250 data rows each; largest SQL statement 5,052 bytes), immutable-conflict guards, and receipts that must commit atomically with each batch. Please provide supported limits, checkpoint/retry semantics, and access to actual `rows_read`, `rows_written`, and `size_after` metadata, or an equivalent supported workflow.

The healthy gameplay version remains live. We will import and independently verify counts, hashes, coverage and publication state before activating the release and deploying its matching application version. No production import or new deployment has been started. The compact comparison has not established a need for R2.

Thank you.

---
Prepared for the owner. **Not sent.** Measurements and implementation details: [storage comparison](storage/README.md).
