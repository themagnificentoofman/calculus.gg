# Milestone verification — November 2, 2026

Historical original-layout report. The current serving representation and hosting checkpoint are in the [November 3 storage report](../storage/README.md). Read access through Sites is established; the bulk method and managed allowances remain unknown. The original artifacts and measurements below are retained.

**Infrastructure:** implemented and locally verified on `codex/indexed-problem-bank`. All four modes select bank revisions, with zero model calls for selection or grading. Server authority, round lengths, scoring, account ownership and historical results remain intact. The branch adds immutable revisions/releases, indexed sampling, private round snapshots, reports, retirement/corrections, offline authoring and operator tools.

**Corpus:** 100,800 approved, materialized, distinct problems are persisted and selectable in the private local artifact. Independent reconstruction and rendering passed for every record. All 24 topic/difficulty cells selected a 20-question round successfully. **Production bank count remains 0; this is not a completed hosted rollout.** This original report predates the temporary read preflight; that authorization was subsequently removed and live version 22 restored.

| Stage | Newly generated | Rejected | Duplicate generation | Approved / locally published |
| --- | ---: | ---: | ---: | ---: |
| Pilot | 1,008 | 0 | 0 | 1,008 |
| Expanded | 9,072 | 0 | 0 | 10,080 |
| Full | 90,720 | 0 | 0 | 100,800 |

Stages reuse prior approved instances. The final importer inserted 90,720 new revisions and safely recognized 10,080 existing revisions. Manifests describe the generated artifact and intentionally retain `publishedCount: 0` / `renderValidated: false`; the separate [operator report](release-report.json) records the subsequent successful import/render gates. No manifest is silently rewritten after publication.

The bank has 72 families, three in each topic/difficulty cell, 1,400 instances per family and 4,200 per cell. Maximum corpus family share is 1.389%. These are parameterized methods, not 100,800 unrelated contest problems. Exact normalized semantic hashes are distinct; general cross-technique equivalence is not exhaustively solved. Human-reviewed count is zero. Existing preset imports and third-party problem-text imports are both zero. Withdrawn pre-production v1 drafts are retained separately and do not contribute to these counts; [validation](../validation.md) explains the discovered defects and corrections.

## Verification evidence

- TypeScript check and production build passed.
- Unit tests: 57 passed, one emulator-only test skipped in that run.
- Firebase Auth/Firestore emulator suite: all 16 tests passed, including the four modes and access-control/settlement checks.
- Independent math regression suite: all eight tests passed.
- Full import: 100,800 independently reconstructed records, 100,800 render/schema checks, no failed final-v2 records.
- Persisted audit: 100,800 distinct IDs, semantic hashes and content hashes; database integrity and foreign keys pass; all 24 cells selectable.
- Browser QA: updated Help page inspected at a narrow viewport. Authenticated production play remains a deployment check.
- Production client and Worker build inspection found no OpenAI endpoint/key reference, authoring recipe or validation basis payload bundled into gameplay.

The local environment was macOS arm64, Apple M5, Node 26.13.0, SQLite 3.54.1, Python 3.14 and SymPy 1.14.0. CI pins Node 24, Python 3.12 and Java 21. [Detailed audit](validation-report.json) and [benchmark](benchmark.json) retain machine-readable evidence.

## Selection benchmark

The real 100,800-row release was used for 1,000 rounds, 250 per case, with 20 questions per round. The sampler uses the production SQL and implementation through a local SQLite D1 adapter.

| Filter | p50 | p95 | p99 | Maximum SQL statements |
| --- | ---: | ---: | ---: | ---: |
| Integration / easy | 2.61 ms | 3.30 ms | 3.74 ms | 16 |
| All topics / hard | 2.01 ms | 2.47 ms | 3.03 ms | 11 |
| Integration / medium / substitution | 2.49 ms | 3.32 ms | 4.20 ms | 16 |
| Multivariable / olympiad | 2.87 ms | 3.68 ms | 4.10 ms | 16 |

There were zero repeats from the last-100 problem window in measured rounds using recency history. Three-family filters had maximum family shares of 33.62% and 33.72%; the all-topic hard case's maximum was 5.78% across 18 families. The substitution filter deliberately has one eligible family, so its share is 100%. Family caps/recency relax explicitly without changing filters. Query plans show primary-key slot/problem/publication lookups; only the small release pool catalogue is filtered/sorted.

These timings exclude Cloudflare network, Worker cold starts, Firebase transactions and authentication. No paid live-generation benchmark was run; the previous 70-second timeout is not a measured latency. No numerical end-to-end speedup is claimed.

The benchmark database occupied 535,511,040 bytes. The finalized schema/audit artifact occupies 535,515,136 bytes (approximately 511 MiB). The difference is an added metadata page, not extra problems. Check D1 account capacity before importing; this exceeds the documented free individual-database limit.

## Costs, artifacts and remaining rollout

Actual OpenAI API calls: **0**. Model spend: **$0**, including failed/retried paid requests (none). A protected dry-run job for 100 family proposals reserves at most $0.528 at the checked price snapshot; authorized spend is $0 and nothing was submitted. CPU, storage, Worker and Firebase costs are separate, as described in [costs](../costs.md).

Large answer-bearing payloads remain in private workspace artifact storage, outside Git and public assets. The delivery archive contains the materialized SQLite database, canonical full JSONL, all three manifests, stratified full review, audit/benchmark reports, and 273 duplicate-safe D1 SQL chunks plus a guarded activation script. `artifact-index.json` records checksums. Recipes, small fixtures and these reports are committed.

The current blocker is the supported authenticated bulk-import method and managed resource allowance for the existing Sites-owned D1 binding. Sites read access is established; the absence of a personal Wrangler login does not require creating a Cloudflare account. Use the [compact rollout](../operations.md), [measured comparison](../storage/README.md) and [unsent support request](../support-request.md). Production imported/active bank counts remain 0/0.
