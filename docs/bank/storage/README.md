# Measured serving storage — November 3, 2026 UTC

The existing 100,800-problem corpus was converted losslessly, without regenerating any mathematical content. All 279 files in the original artifact index still match their sizes and SHA-256 checksums. The original SQLite, JSONL and pilot/expanded artifacts are retained. Human-reviewed count remains zero.

| Representation | SQLite bytes | Estimated data row/index writes | Local selection p95, four cases | Change |
| --- | ---: | ---: | --- | --- |
| Original layout, three releases | 535,515,136 | 1,473,054 | 2.92–4.68 ms | Full JSON plus repeated text memberships |
| Original layout, full-release memberships only | 527,650,816 | 1,386,374 | 1.95–3.23 ms | Pilot/expanded memberships kept in private original artifacts |
| Compact full-release serving artifact | 90,050,560 | 1,025,317 | 1.90–2.24 ms | Integer references, shared metadata, gzip residuals |
| Fresh compact import, including 1,850 receipts | 90,337,280 | 1,027,167 | Same serving implementation; staging until verified activation | Rehearsed duplicate-safe import |

Write estimates count each inserted table row and each additional index entry. An integer primary key aliases the rowid; a `WITHOUT ROWID` primary key is the table, so neither is counted twice. Estimates exclude schema operations, activation, verification reads, retries and ongoing application usage. The original/full-only totals exclude their active-config row (two further logical writes); the compact artifact total excludes its local active-config row (one). **No production D1 write counters have been measured.** The compact import reduces stored bytes by 83.13% and estimated seed writes by about 30.3%, but still needs an explicitly established managed allowance.

## Why JSONL is smaller than the original SQLite

The measured difference is not all index overhead:

| Component | Bytes |
| --- | ---: |
| Full canonical JSONL | 303,802,090 |
| JSONL line terminators (100,800) | −100,800 |
| Canonical payload text in `bank_problems` | 303,701,290 |
| Other problem-table fields and SQLite record encoding | 20,092,800 |
| Unused space within problem-table pages | 100,246,687 |
| Problem-table page/cell overhead | 2,373,303 |
| All other database tables and indexes | 109,101,056 |
| Total SQLite allocation | **535,515,136** |

Original page size is 4,096 bytes, page count 130,741, freelist count zero. `dbstat` reports 108,924,985 unused bytes across all allocated pages, including 100,246,687 in the problem table. Whole free pages and unused space inside occupied pages are different; this is not 100 MB of disposable freelist pages. All original indexes together allocate 72,867,840 bytes. `bank_problems` alone allocates 426,414,080 bytes. The individual original slots table and its two indexes allocate 31,870,976, 27,332,608 and 21,311,488 bytes respectively; publication plus its index uses 7,917,568 bytes.

The pilot and expanded releases add 2,604 and 26,040 slots, versus 260,400 full-release slots. Rebuilding with only full memberships reduces allocation by 7,864,320 bytes and estimated data writes by 86,680; it does not change the large problem table. The full-only comparison retains every problem revision and publication row. Detailed per-object allocation/payload/unused figures are in [original](original-audit.json), [full-only](full-only-audit.json), [compact](compact-audit.json) and [fresh import](import-audit.json) audits.

## Payload and membership representation

The original records contain 38,203,200 bytes of provenance JSON and 66,273,097 bytes of validation JSON. A recursive intersection of metadata within each family identifies 154,345,800 repeated JSON bytes, represented by 110,247 bytes across 72 immutable shared metadata objects. Arrays are shared only when identical; differing nested evidence remains in the individual record. Shared objects are content-addressed and immutable; corrections can reference new objects without changing previous evidence.

Per-record gzip alone totals 139,852,051 payload bytes. Factoring metadata and external identity fields first leaves 129,257,090 residual JSON bytes, compressed to 51,710,287 bytes. Identity/revision and binary content/semantic hashes are retained separately, then reconstructed before hashing. These payload-only measurements exclude table/index/page overhead and are not presented as alternative full-database sizes. The compact problem table allocates 67,342,336 bytes; slots and their uniqueness index total 7,725,056 bytes. All 100,800 reconstructed canonical records match the original payloads byte for byte, with identical content hashes, coverage and publication state. The fresh import repeats those hash checks using the actual Worker-compatible decoder.

Permanent `cn_…` IDs, revisions and snapshot references are unchanged. Integer IDs are internal to the serving database; retain that database as the registry when appending revisions/releases. Do not independently rebuild a different integer mapping and import it over an existing registry. Immutable SQL conflicts abort; approvals cannot revive retired revisions. The authoring/verifier workflow still enforces mathematics and consecutive revisions before serving conversion. `0002_compact_bank.sql` adds tables and immutable triggers only; it leaves `0001` and existing application data intact.

## Runtime and verification

The sampler queries indexed pools, at most 320 exact membership probes, then only the selected payloads (20 for a normal round). It has at most ten SELECT statements, at most 80 bound parameters per statement, and per-request caching only. Typical benchmark cases used six or eight statements. There is no corpus scan or full-bank cache in gameplay. Only final selections are decompressed; the decoder enforces a 64 KiB bound and verifies the original SHA-256. Corrupt content fails closed. Snapshot serialization and the public allowlist are unchanged; private content, answer keys and evidence remain server-side.

The [original](original-benchmark.json), [full-only](full-only-benchmark.json) and [compact](benchmark.json) benchmarks each ran 1,000 rounds against 100,800 materialized problems on Apple M5/macOS arm64, Node 26.13.0, SQLite 3.54.1. The compact query plans show indexed/primary-key searches throughout; only the small pool catalogue is filtered. Across the four cases, history-aware rounds had zero last-100 problem repeats. These measurements include local decoding/hash checks but exclude hosted D1 latency, Worker cold starts, authentication and Firebase transactions. Local timings vary with CPU/cache state and do not establish production performance or a speedup over live generation.

The relevant regression suite covers exact reconstruction, revisions/new release activation, retirement, immutable conflicts, filter/recency behavior, bounded decompression, private/shared snapshots, report identity, server XP and idempotent settlement. Full unit run: 62 pass plus one emulator-only skip; Auth/Firestore emulator run: all 16 pass. A separate local workerd/Miniflare test imported and verified the 72-family fixture through the D1 API and selected questions using the production decoder. This verifies API/binary/compression compatibility, not managed capacity. A complete local import committed 1,850 batches; retry skipped all 1,850 receipts. All 100,800 imported records and 260,400 memberships then passed paged verification. Import staging contains no active config.

Workers supports [gzip decompression streams](https://developers.cloudflare.com/workers/runtime-apis/web-standards/). D1 documents [atomic batches](https://developers.cloudflare.com/d1/worker-api/d1-database/) and [result metadata](https://developers.cloudflare.com/d1/worker-api/return-object/). Public [D1 limits](https://developers.cloudflare.com/d1/platform/limits/) do **not** establish this Sites-managed database's allowance.

## Hosting state and remaining gates

The reconciled starting GitHub main is `005a38ee1cb2c748d0f45c6520a356c47a8b1f6f` (merged PR 16). Saved bank version **23** uses that source and the original layout. Live production remains version **22**, source `ba3eb4194905e3a3a456967c59f65c067c93686c`, rollback deployment `appgdep_6ae96ec7e6b88191a9bde57f7a4599b2`, environment revision 5. Sites source history also contained temporary preflight versions 24–26, latest source `392c6f972a5459cff7e70fa9f5841bc597be6963`; this branch reconciles that history without retaining its operational endpoints. The temporary authorization was removed before this work.

| Question | Established state |
| --- | --- |
| Managed D1 read access | Yes, through Sites; production schema currently contains only `ai_quota` |
| Supported authenticated bulk-write method | **Unknown**; connected database tools expose reads |
| Storage ceiling / remaining allocation | **Unknown**; the earlier 32,768-byte diagnostic was current occupancy only |
| Write/read allowances, reset window, shared usage | **Unknown** |
| Locally validated problems | **100,800** |
| Production imported / active bank problems | **0 / 0** |

This layout requires a new built/tested Sites version; version 23 cannot serve it. Source publication and saving a version do not deploy it. The final save receipt is recorded separately with the exact source/archive hash. No migration, corpus import, activation or deployment is performed while the method and resource allowance are unresolved. The healthy live version stays available.

The measured compact size has not established a need for R2, so no R2 architecture, provisioning, uploads or cost claims are introduced. Binding `r2` remains null. If the managed D1 ceiling cannot accommodate the compact size and agreed headroom, first establish supported private R2 provisioning/upload limits before evaluating that alternative. See the [unsent support request](../support-request.md) and [rollout instructions](../operations.md).
