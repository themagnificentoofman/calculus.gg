Supplemental solution presentation research, version 1

Scope: 118 families / 944 immutable source records. This covers 48 multivariable,
48 differential-equations, 12 limits additions, 5 differentiation additions, and
5 easy-series additions. The original bank, choices, answer IDs, semantic IDs,
and historical question records are unchanged.

Canonical code: solutions.py
  supports(record) -> bool
  corrected_solution(record) -> list[str]
  corrected_statement(record) -> str | None
The optional statement corrections are exact original ID/contentHash guarded,
formatting/concretization changes for 48 records in six families. They preserve
all mathematical conditions and requested results. The parent must also bind
solution presentation versions to the original record content hash.

Notation: natural logarithms use ln; inverse circular functions use arc names.
Auxiliary symbols are defined in the derivation, fixed builder values are
instantiated where meaningful, and metadata-only parameters are omitted. Prose
is not manually line-wrapped or put in gathered environments. The final step
matches the original correct answer after notation normalization.

Reproduction (Python 3 with SymPy, Node with KaTeX):
  export CN_SOLUTION_SOURCE_REPO=/path/to/inspected/repository
  export CN_SOLUTION_SOURCE_ARTIFACT=/path/to/immutable/artifact.jsonl
  export CN_KATEX_MODULE=/path/to/node_modules/katex/dist/katex.mjs
  export PYTHONDONTWRITEBYTECODE=1
  python source_check.py
  python validate.py
  python substantive_checks.py
  node render_check.mjs
  python audit.py

The input overrides are optional when repository/assets can be inferred from the
copied scripts/bank/solution-review/supplemental directory. The recorded original
artifact path is a final local fallback, not a hard-coded machine dependency.
Reports write only beside these scripts. The source repository is read-only.
The validate script refreshes the embedded statement guard table from the exact
reviewed immutable input; guard changes are reviewable generated code changes.

Evidence:
- source-checks.json: source builders reproduce every original correct answer.
- validation.json: rewritten result agrees with the trusted constructor;
  exact final answer, immutable input, notation, and statement guard checks.
- substantive-checks.json: independently encoded intermediate identities,
  including ODE residuals/ICs, operator transforms, geometry, Jacobians, Hessians,
  integration primitives, discrete identities, finite jets, and sign checks.
  It does not import the source constructors.
- render-checks.json: strict untrusted KaTeX parses every changed expression.
- family-audit.json: all 118 routes, hypotheses, symbol scopes, evidence IDs,
  original hashes, check names, and honest analytic/editorial boundaries.
- statement-clarifications.json: exact optional presentation statements.

Review boundary: AI mathematical and editorial review with reproducible exact
checks, not a human review or formal proof. Convergence theorems, uniqueness,
sharpness arguments, and geometry are explicitly recorded analytic certificates;
executed algebra does not purport to prove those theorems. Responsive visual
layout remains the parent application's responsibility.
