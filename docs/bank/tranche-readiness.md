# Tranche resumption status

> Historical checkpoint before the explicitly authorized [operator-budget mode](operator-budget.md). Its provider-allocation prerequisite is superseded for this existing bundle; preserve this record as pilot evidence.

The Sites four-batch pilot established authenticated writes, transaction receipts, canonical-content readback, and per-query D1 counters. It did not establish a remaining managed read/write allowance, reset window, expiry, or shared usage reservation. There are no pilot remaining-budget figures to carry forward.

The production checkpoint contains the original bundle's receipts 0–3. Next missing sequence is 4. The live pilot writer remains disabled and has a compiled four-batch cap. This local branch does not expand or deploy that endpoint.

The provider-neutral executor now accepts `startIndex` and `maxBatches`. Remote runs require an explicit finite limit and a freshly obtained allowance authorizing the exact `[startIndex, endIndexExclusive)` range. Each invocation calls `refreshAllowance`; previous receipts are reconciled before any write. A missing earlier receipt, checksum conflict, absent counters, expired allowance, or exhausted cumulative headroom stops execution. A committed batch records its next index before a metadata failure is reported. A subsequent invocation must refresh provider usage and reconcile receipts, including after lost responses. The result records the exact boundary, timestamps, duration, actual usage, database size, and the remaining allowance after measured operations.

The tests use explicitly synthetic allowances and counters. Passing those tests is not provider authorization or evidence of hosted remaining quota. A supported provider allowance/reservation adapter, a server-enforced cumulative budget ledger, and bounded full verification operations must still be integrated before enabling a larger hosted executor. The current four-batch hosted cap must not be bypassed.

To continue production, the provider must expose or confirm for this Site and DB binding:

- Current remaining read/write allocation after all shared usage, with its scope, checked-at time, reset/expiry, and a reservation or enforceable maximum for the import.
- Effective storage ceiling and fresh current usage/headroom, including account-specific/shared limits.
- A supported way to refresh those facts between tranches. Per-query `rows_read`, `rows_written`, and `size_after` cannot supply remaining shared quota.

Plan each allowed tranche using its exact manifest entries. The first four batches contain shared metadata and problem payloads; later publication and membership rows have different index-write costs. Keep separate reserves for receipt checks/reconciliation, uncertain retries, full content/membership verification, activation, and live application traffic. Do not derive a remaining quota by subtracting pilot consumption from an unverified limit. Keep the bank inactive until all 1,850 receipts and complete hosted verification pass. Version 27 is the saved compact-bank application candidate; version 23 uses the earlier layout.
