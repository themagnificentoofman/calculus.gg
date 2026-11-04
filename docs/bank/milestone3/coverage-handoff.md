# Original coverage asset: frozen handoff

This asset contributes **205 admitted families / 1,640 finite-domain instances**. It keeps **41 additional families quarantined** for difficulty or duplicated-recognition reasons. The complete raw catalogue has 246 families / 1,968 mathematically checked instances. These are preparation/admission counts, not imported or active production coverage.

The aggregate source hash is `d6caa8cb3cb94047b5cdfefd716e216f55045e01bbc76a38af0abcd7dbc4f52a`.

Copy these six files together with unchanged filenames and put their directory on the Python import path: `coverage.py`, `multivariable.py`, `extra.py`, `certificates.py`, `distractors.py`, `editorial.py`. Also copy `admission.json`. The attestation hashes all six source files; a changed or missing attestation leaves candidates unadmitted. No network calls, app mutations, or external problem scripts are used. SymPy is the sole mathematical dependency.

`catalog()` enumerates metadata. `build(family_id, instance_index)` accepts exactly integer indices 0 through 7, corresponding to m=4 through 11. `all_candidates()` also includes quarantined records; integration must filter `editorialStatus == "admitted"` and `validation.status == "verified"`. Invalid indices, booleans, strings and unknown families are rejected. Three conceptual growth families include extended-real limit answers (infinity); they are proved by exact symbolic limits and remain ordinary choice-ID-graded questions.

Every `proof()` call preserves its executed assertion records. Analytic certificates separately name the theorem, conditions and exact symbolic derivation steps. A symbolic assertion does not claim to re-prove an analytic theorem. Review is explicitly AI-assisted; no human review is claimed.

| Cell | Authored | Math checked | Quarantined | Admitted ready |
|---|---:|---:|---:|---:|
| integration/easy | 12 | 12 | 0 | 12 |
| integration/medium | 12 | 12 | 0 | 12 |
| integration/hard | 15 | 15 | 5 | 10 |
| differentiation/easy | 12 | 12 | 0 | 12 |
| differentiation/medium | 12 | 12 | 0 | 12 |
| differentiation/hard | 12 | 12 | 1 | 11 |
| differentiation/olympiad | 13 | 13 | 4 | 9 |
| limits/easy | 12 | 12 | 0 | 12 |
| limits/medium | 12 | 12 | 2 | 10 |
| limits/hard | 14 | 14 | 4 | 10 |
| limits/olympiad | 12 | 12 | 8 | 4 |
| series/easy | 12 | 12 | 5 | 7 |
| series/medium | 12 | 12 | 0 | 12 |
| series/hard | 17 | 17 | 5 | 12 |
| series/olympiad | 14 | 14 | 2 | 12 |
| multivariable/easy | 12 | 12 | 0 | 12 |
| multivariable/medium | 12 | 12 | 0 | 12 |
| multivariable/hard | 12 | 12 | 0 | 12 |
| multivariable/olympiad | 17 | 17 | 5 | 12 |

The parent integration combines these with the isolated ODE, differentiation, limits and series/easy assets and reclassified integration/Hard content. In particular, the seven remaining easy-series families deliberately exclude geometric and telescoping variants that would inflate independent coverage. The parent must normalize related ideas across modules before reporting globally distinct constructions.

Verification evidence:

- `verification-report.json`: full 1,968-instance run, followed by 48 explicit bounded rechecks covering six final growth/distractor revisions. All passed. It records the base complete-run source hash and the final source hash, so this incremental check is not disguised as a second full run.
- `render-report.json`: 17,248 strict KaTeX statement, option and solution expressions, zero errors. The final data include escaped prose, explicit special-function conventions, local-inverse assumptions, and corrected arc-length numerical denominators.
- `admitted-candidates.jsonl`: 1,640 ready records; `raw-candidates.jsonl`: all 1,968 including quarantines. These are review/export artifacts; `build` is the trusted constructor.
- `coverage-matrix.json`: per-cell counts for this module, excluding external supplements.

Distractors use authored errors such as omitted endpoint terms, wrong derivative order, missed Jacobians, incorrect branches and finite-index shifts. Selection considers every feasible correct numeric rank 1 through 4; it does not force the answer into the middle two. No admitted family has a fixed correct numeric rank across its eight instances. Aggregate ranks are 1:161, 2:507, 3:642, 4:330. The largest rank-only aggregate rate is 39.1%, not 25%; report that residual distribution honestly. It is not proof that every possible option shortcut has been removed. The parent global audit covers length, scale, parity, format and other shortcut features across the combined bank.

Representative independent advanced decisions include a constrained Vandermonde discriminant maximum; an anisotropic singular-integral threshold; a correlated Gaussian wedge; disk logarithmic potential and squared-log Parseval identities; a complex lemniscate area; a cube/simplex cap verified by independent convolution; polynomial-image winding with a proved zero-exclusion bound; Lambert totient divisor regrouping; and a differentiated Gaussian theta duality. The final four multivariable replacements received a separate AI-assisted peer proof/level audit with no blocker.

Source collections informed gap analysis, not wording adaptation. The mathematical source register is maintained by the parent/source researcher; NIST DLMF entries are theorem-background references only. `sourceRecordIds` stay empty for independently authored content when no source expression was reused.

Reproduce a full mathematical export with `python finalize.py`, then run `node render-check.cjs` in this workspace. A fresh import and representative `build` calls also confirm that source-hash attestation resolves to admitted/verified. The helper `attest.py` documents the one bounded post-run revision set; it should not be used to approve arbitrary later changes. Later content edits require new verification and attestation.
