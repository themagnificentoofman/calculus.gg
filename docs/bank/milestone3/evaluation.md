# Matched selection evaluation

Reproduce with `node --experimental-strip-types scripts/bank/evaluate-quality.mjs BASELINE.sqlite CANDIDATE.sqlite REPORT.json`. The report records the fixed offline seeds; production uses fresh cryptographic randomness. Each of 24 cells has 100 matched baseline/candidate rounds at both sizes 5 and 20: 9,600 rounds total. Six Olympiad cells also have ten consecutive 20-question rounds with attempted history carried forward. Two narrow drills run 100 rounds each; sparse and retired cases are covered by focused tests. No production games or model calls were used.

**Acceptance:** all 4,800 candidate broad-pool rounds have zero exact within-round duplicates. Every broad 20-question round has at most two items per family and no same-family adjacency.

| Cell, 20-question independent rounds | Families before → after | Ideas after | Structures after | Primary methods after |
|---|---:|---:|---:|---:|
| integration / easy | 3.00 → 12.54 | 12.54 | 12.27 | 8.80 |
| integration / medium | 3.00 → 12.53 | 12.25 | 12.30 | 7.83 |
| integration / hard | 3.00 → 13.19 | 13.19 | 12.97 | 7.65 |
| integration / olympiad | 3.00 → 17.59 | 17.10 | 17.58 | 14.22 |
| differentiation / easy | 3.00 → 12.63 | 12.63 | 12.42 | 10.49 |
| differentiation / medium | 3.00 → 12.47 | 12.19 | 12.20 | 9.74 |
| differentiation / hard | 3.00 → 12.65 | 12.36 | 12.35 | 11.41 |
| differentiation / olympiad | 3.00 → 13.16 | 13.16 | 12.89 | 11.52 |
| limits / easy | 3.00 → 12.62 | 12.26 | 12.33 | 10.44 |
| limits / medium | 3.00 → 12.52 | 12.45 | 12.29 | 11.55 |
| limits / hard | 3.00 → 12.45 | 12.45 | 12.18 | 9.64 |
| limits / olympiad | 3.00 → 12.50 | 12.50 | 12.26 | 12.50 |
| series / easy | 3.00 → 12.69 | 12.62 | 12.39 | 9.78 |
| series / medium | 3.00 → 12.49 | 12.21 | 12.25 | 8.81 |
| series / hard | 3.00 → 12.77 | 12.77 | 12.50 | 10.95 |
| series / olympiad | 3.00 → 12.50 | 12.50 | 12.21 | 11.58 |
| differential equations / easy | 3.00 → 12.66 | 12.66 | 12.38 | 9.62 |
| differential equations / medium | 3.00 → 12.56 | 12.33 | 12.33 | 7.87 |
| differential equations / hard | 3.00 → 12.48 | 12.48 | 12.28 | 8.74 |
| differential equations / olympiad | 3.00 → 12.61 | 12.61 | 12.27 | 11.70 |
| multivariable / easy | 3.00 → 12.71 | 12.61 | 12.61 | 10.73 |
| multivariable / medium | 3.00 → 12.61 | 12.61 | 12.61 | 11.67 |
| multivariable / hard | 3.00 → 12.65 | 12.65 | 12.65 | 11.73 |
| multivariable / olympiad | 3.00 → 12.62 | 12.62 | 12.62 | 10.82 |

## Consecutive Olympiad sessions

| Topic | Mean families | Mean ideas | Mean primary methods | Exact repeats / 200 | Relaxed rounds |
|---|---:|---:|---:|---:|---:|
| integration | 17.7 | 17.0 | 14.1 | 0 | 0 |
| differentiation | 13.6 | 13.6 | 12.1 | 79 | 5 |
| limits | 13.0 | 13.0 | 13.0 | 79 | 5 |
| series | 13.0 | 13.0 | 12.3 | 77 | 5 |
| differential equations | 12.7 | 12.7 | 11.8 | 83 | 5 |
| multivariable | 13.1 | 13.1 | 11.3 | 82 | 5 |

Integration/Olympiad produces 200 distinct problems across ten rounds, no family adjacency, no recent-item relaxation, 17.0 related ideas and 14.1 primary methods per round on average. Baseline has three families, at most seven items from one family, and 4.6 family adjacencies per round. Near-clone three-question windows fall from 18 to 0.2. Alternative tags (18.1 on average) are reported separately and are not added to primary-method diversity.

Other Olympiad cells retain variety within each round but begin recent-item relaxation after five rounds: 77–83 exact repeats across 200 questions. This is a finite depth limit, not a claim of ten fully novel sessions. Diagnostics report `candidate-sampling-limit`, not proven exhaustion: large legacy families still contain unseen items, but only three such families cannot fill a 20-question round under the two-per-family cap.

Narrow substitution and parameter-differentiation drills respect their tags. Substitution records an impossible family cap; both drills eventually relax recent-item avoidance. They never change difficulty or cross filters. Strategy penalties are probabilistic: consecutive methods can recur, as in the first sample’s parameter-ODE cluster. The policy does not promise one method per question or an obvious method rotation.

Offline candidate p95 latency across broad cells is at most 2.79 ms on this machine. Repeated studies use at most 10 SQL statements and 356 returned rows per selection. These are local timings and returned rows, not billed rows, network latency, cold starts or Firebase costs. [rehearsal.json](rehearsal.json) contains separate local workerd/D1 engine measurements; production receipts must supply hosted measurements.

The full [evaluation.json](evaluation.json) includes concentration, adjacency, near-clone windows, exact-repeat rates, family return intervals, reasoning demand, strategy combinations, alternative tags, exposure-history bytes, query bounds and two complete playable sequences per repeated cell.

## Hosted release verification

All 24 staged production-selector checks passed before activation. They used four sampler SQL statements each; observed whole-operation reads, including operator bookkeeping, ranged from 604 to 651. Signed verification server time averaged 362.7 ms (p95 553 ms), including multiple remote D1 accounting operations. This is not ordinary gameplay latency. The full release observed 80,895 rows read and 32,605 rows written in returned provider measurements; conservative reservation charges were 563,084/51,276, including unmetered preflight coverage. See [production-verification.json](production-verification.json).
