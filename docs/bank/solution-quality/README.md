# Worked-solution and notation audit

All **103,304 active problems in 385 families** received a reviewed presentation. Original records, answers, stable IDs, choice IDs, grades, ratings and saved replay content are preserved. No bank import, production database rewrite or model call was needed.

The reported problem is `cn_c05d5e5ff7186cb58716`. Its explanation now identifies odd/even symmetry, evaluates the actual π/6 endpoint, and concludes 1; the irrelevant generator parameter and undefined endpoint letters are removed. A desktop/mobile preview uses the actual React components and app CSS, with normal prose paragraphs and intact horizontally scrollable equations.

The [notation standard](../NOTATION-AND-SOLUTIONS.md) selects common forms documented by MathWorld, including ln, explicit logarithm bases, named inverse functions, upright differentials and explicitly defined Pochhammer notation. It is also published at `/help#notation` and required by `scripts/bank/AGENTS.md`.

## Evidence

- `full-inventory-audit.json`: every immutable source hash checked; every presented record meets the source-bound quality gate; 386,228 distinct mathematical expressions render with zero failures (the JSON is authoritative if this count changes during final validation).
- `baseline-audit.json`: 1,688 parameter prefaces, 1,976 narrow gathered-prose solutions, 160 unexplained endpoint formulas, 31,104 nonstandard natural-log solutions, and 480 ASCII-formula-in-prose solutions. Each category is zero after correction.
- `review-manifest.json`: exact digests of the finite registry, 100,800 legacy source hashes, audited recipe code, renderer/normalizer, and all family-review evidence. CI rejects an unreviewed change to this binding.
- `scripts/bank/solution-review/coverage`: 157 families / 1,256 records, 2,608 executed exact/boolean checks and 160 separately labeled analytic theorem applications.
- `scripts/bank/solution-review/supplemental`: 118 families / 944 records, 2,916 independently encoded intermediate checks.
- `scripts/bank/solution-review/integration-legacy`: 38 io3 families / 304 records plus 72 legacy families / 100,800 instances; 72 finite certificates, 207 independently recomputed basis operations, 288 legacy edge answers, 472 io3 source identities and 191 additional bridge/edge checks. Reciprocal bounded peer review adds 33 advanced ODE/multivariable and 22 advanced-series identity checks.

There are 56 exact-source-bound, meaning-preserving statement clarifications (48 supplemental and eight rising-factorial statements). Other statement changes are notation presentation. Original mathematical source records remain unchanged. Unknown source hashes and new finite instances cannot inherit an existing review. Future standalone polynomial v2 questions independently reconstruct their full record before admission; unsupported routes fail closed.

Automated symbolic checks do not prove general analytic theorems or detect every conceivable editorial issue. The family reports record domain, convergence, branch and uniqueness arguments separately. This is an exhaustive finite inventory check with AI-assisted mathematical/editorial family review, not a claim of human or formal-proof certification.

## Reproduction

Use the immutable source artifact with SHA-256 `1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677` and the combined local SQLite copy of the two active releases. Neither input is changed.

```
python scripts/bank/solution-review/compile.py IMMUTABLE.jsonl
node scripts/bank/audit-solutions.mjs IMMUTABLE-COMBINED.sqlite REPORT.json
npm run bank:solutions
npm run typecheck
npm test
node scripts/bank/worker-smoke.mjs
node scripts/bank/preview-solutions.mjs IMMUTABLE.jsonl 4177
```

Each research directory includes its mathematical checks. Coverage accepts `BANK_AUDIT_ARTIFACT` and `BANK_AUDIT_CONTENT_DIR`. Supplemental documents `CN_SOLUTION_SOURCE_REPO`, `CN_SOLUTION_SOURCE_ARTIFACT` and `CN_KATEX_MODULE`. Integration/legacy reproduction uses `BANK_AUDIT_REPO`, `BANK_AUDIT_ARTIFACT`, and `BANK_AUDIT_LEGACY_DB` (the immutable legacy-only SQLite copy). Its original delivery manifest records the inspected evidence; the root manifest binds the copied portable scripts. Reproduction may regenerate local evidence reports, which must be reviewed before updating the binding.

New rounds save reviewed explanations. Historical analysis receives a separately labeled source-bound overlay after the existing match/member gate; recorded playback retains the saved explanation. Older snapshots missing sufficient source evidence remain intact. A delayed Firestore review cannot undo a server-returned clarification, and cached reviews cannot reveal unanswered solutions.
