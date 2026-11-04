# Cumulative release budget

The previous settled production charge remains 4,418,286 reads and 1,110,803 writes. The remaining allowance is 581,714 reads and 189,197 writes, with the 150,000,000-byte database ceiling unchanged. No prior charge was reclaimed.

The final local Worker/D1 rehearsal executes 397 steps, 28 staged selection checks, 16 idempotent retries, activation and rollback. It charges 551,946 reads and 65,433 writes, including the reserved 10,000-read/1,000-write preflight. This leaves 29,768 reads and 123,764 writes within the current allowance. Measured local engine work is 144,971 reads and 42,696 writes; these are not hosted counters or provider remaining quota.

The first local run preserved all import measurements but halted on a JSON-key lineage verification query. Every imported batch measured at most 2.237 reads per row, with a maximum 169 total reads for an 80-row batch. The revised plan conservatively reserves ten reads per import row plus 100 per batch and unchanged operation/request overhead. Table verification reserves twice the row count for range reads and four times for JSON-key reads, plus overhead. Every operation still charges measured excess and halts; cumulative ceilings remain enforced.

The full SQL batches, payloads, policy and active catalog are unchanged by reservation revision. The new bundle binds the prior bundle and complete local import evidence. The compact serving manifest binds the full audit manifest and policy arrays; all old manifests remain immutable. Actual hosted consumption and final disabled-operator state must be recorded after publication.
