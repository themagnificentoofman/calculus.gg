# Sustained-practice results (local)

All 28 pools pass 20 development and 20 reserved held-out sequences. Each Olympiad sequence has ten 20-question rounds; other levels have five. Histories remain continuous. No exact/equivalent repeats, within-round duplicates, family-cap violations, same-family adjacency, relaxation or request errors occur in the passing candidate runs.

| Pool | Baseline normalized tasks | Candidate normalized tasks | Constructions | Qualified O ideas | Cap capacity / required | Held-out mean O ideas | Failed gates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| integration/easy | 4296 | 120 | 12 | 0 | 120/100 | 0.000 | 0 |
| integration/medium | 4296 | 161 | 17 | 0 | 161/100 | 0.000 | 0 |
| integration/hard | 4304 | 206 | 29 | 0 | 206/100 | 0.000 | 0 |
| integration/olympiad | 4444 | 244 | 30 | 30 | 244/200 | 17.005 | 0 |
| differentiation/easy | 4296 | 120 | 12 | 0 | 120/100 | 0.000 | 0 |
| differentiation/medium | 4296 | 121 | 13 | 0 | 121/100 | 0.000 | 0 |
| differentiation/hard | 4296 | 177 | 20 | 0 | 177/100 | 0.000 | 0 |
| differentiation/olympiad | 4290 | 244 | 30 | 30 | 244/200 | 16.840 | 0 |
| limits/easy | 4296 | 120 | 12 | 0 | 120/100 | 0.000 | 0 |
| limits/medium | 4296 | 130 | 13 | 0 | 130/100 | 0.000 | 0 |
| limits/hard | 4296 | 187 | 20 | 0 | 181/100 | 0.000 | 0 |
| limits/olympiad | 4282 | 241 | 30 | 30 | 241/200 | 16.310 | 0 |
| series/easy | 4296 | 120 | 12 | 0 | 120/100 | 0.000 | 0 |
| series/medium | 4296 | 163 | 19 | 0 | 163/100 | 0.000 | 0 |
| series/hard | 4296 | 169 | 19 | 0 | 169/100 | 0.000 | 0 |
| series/olympiad | 4296 | 240 | 30 | 30 | 240/200 | 17.165 | 0 |
| differential equations/easy | 4296 | 120 | 12 | 0 | 120/100 | 0.000 | 0 |
| differential equations/medium | 4296 | 140 | 14 | 0 | 140/100 | 0.000 | 0 |
| differential equations/hard | 4296 | 189 | 24 | 0 | 189/100 | 0.000 | 0 |
| differential equations/olympiad | 4275 | 263 | 30 | 30 | 263/200 | 16.970 | 0 |
| multivariable/easy | 4296 | 140 | 14 | 0 | 140/100 | 0.000 | 0 |
| multivariable/medium | 4296 | 160 | 16 | 0 | 160/100 | 0.000 | 0 |
| multivariable/hard | 4296 | 125 | 13 | 0 | 113/100 | 0.000 | 0 |
| multivariable/olympiad | 4289 | 281 | 31 | 30 | 281/200 | 16.765 | 0 |
| all/easy | 25776 | 740 | 74 | 0 | 740/100 | 0.000 | 0 |
| all/medium | 25776 | 875 | 92 | 0 | 875/100 | 0.000 | 0 |
| all/hard | 25784 | 1053 | 125 | 0 | 1035/100 | 0.000 | 0 |
| all/olympiad | 25876 | 1513 | 181 | 164 | 1513/200 | 19.815 | 0 |

The full distributions, seeds, source digests, integration tolerances and failures are in summary.json and the compressed raw reports. Open [readable sequences](readable-sequences.html) for actual representative and worst-sequence questions, choices, answers and reasoning.

Multivariable Hard has 13% cap-effective headroom, below the approximate 20% planning target. Its two failed initial development seeds are preserved. Complete small catalogs now reserve feasible future capped capacity within the existing 320-probe bound; random family-normalized choice remains. The exact repair passes all development and reserved seeds and an uneven-inventory regression.

The 118 supplementary scenarios cover real-catalog short rounds, constrained and exhausted returning histories, 512 retained attempts, actual catalogs above 192 pools, narrow drills, sparse inventory, mass retirement and empty-allowlist opt-in parity. The first scenario fixture accidentally retained the v3 pointer; its invalid results and correction remain explicit.

The old baseline is evaluated using its own pinned v37 selector, presenter and history implementation with the same reviewed equivalence definitions. Older baseline menu weaknesses retain their own qualification dispositions. These are offline tests, not player telemetry or hosted timing/billing. Publication and the remaining budgeted Worker rehearsal are separate gates.
