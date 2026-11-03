# Content validation and diversity

## Coverage policy fixed before scaling

All six topics retain their current display names: integration, differentiation, limits, series, differential equations, multivariable. Each topic has easy, medium, hard and olympiad. There are **three distinct method families per cell, 72 total**. Each family contributes exactly 14/140/1,400 rows at the three stages. Each topic/difficulty cell therefore contains 42/420/4,200 rows. No family exceeds 1/72 (1.389%) of a complete release. Technique coverage and counts are in each manifest.

The initial corpus intentionally uses many parameterized instances of a finite set of methods. It is not 100,800 unrelated contest problems. Most families use bounded coefficients 1–16 applied to three fixed mathematical kernels. The three advanced ODE families vary their parameters directly. Coefficient size does not determine difficulty. Every instance is materialized, validated and persisted; unused combinations do not count.

| Display level | Method rubric | Initial solve-time estimate |
| --- | --- | --- |
| Easy | One fundamental derivative, integral, continuity, geometric-series or initial-value rule | 45 seconds |
| Medium | Choose/combine standard rules, substitution, partial fractions, an integrating factor or mixed partials | 90 seconds |
| Hard | Coupled steps, higher derivatives, improper/convergence analysis, resonance or nonrectangular domains | 180 seconds |
| Olympiad | Discover a concealed identity/transformation: reflection, Frullani grouping, inverse-series extraction, finite differences, Fourier reconstruction, nonlinear shift, envelope or a multivariable transformation | 360 seconds |

These are automated editorial estimates, not calibrated ratings. The second-order Riemann-sum and rotated-disk families are especially sensitive to what methods a player has already learned. Difficulty calibration is future work; do not claim human adjudication.

## Independent correctness

`families.py` contains typed SymPy expressions, operation parameters, bounds and domains. LaTeX is only a rendering output and is never evaluated as code. The independent checker evaluates exact derivatives, integrals, limits, sums, partials and ODE residuals. Fixed-basis linearity certificates apply to every bounded coefficient instance. Advanced supported families use exact finite sums, polynomial coefficients, partial fractions, binomial/beta identities or explicitly justified uniform remainder bounds. Nonlinear ODEs use residual, initial/branch and domain checks, not a linearity certificate.

For every record the importer reconstructs the statement, four choices, answer ID and full solution from that mathematical representation, compares the entire record, then checks every displayed formula with the production KaTeX renderer and gameplay size/schema limits. Solutions include method identities and exact basis evaluations. No LLM agreement or numerical spot check is treated as proof.

Distractors are exact perturbations by a provably nonzero mathematical unit. Their sign patterns vary deterministically so the key does not occupy a fixed numerical rank. Rational answers use rational units with compatible denominators; symbolic answers preferentially reuse a known nonzero term. The four offsets are distinct, so precisely one equals the verified answer. This is a correctness guarantee, not a claim of expert-designed misconception diagnostics. Offline authoring can propose better distractors, but they must pass the same proof gates.

The initial integration corpus uses definite/improper integrals. Antiderivative support must compare derivatives on each connected stated domain; options differing only by an additive constant are both correct and must be rejected. Regression tests explicitly cover that ambiguity, singular integrals, divergent endpoint series, wrong expected values, dependent rational kernels and rendered numeric products.

## Deduplication boundary

Stable semantic keys omit wording, choices, their ordering, topic labels and difficulty. They include the structured mathematical operation, canonical expanded/cancelled source expression and mathematical operation parameters. Bound variables are fixed by the supported recipes; variable renaming is not an authoring dimension. Rational basis rank checks reject dependencies that would create equivalent coefficient variants. An import with an already-known semantic key under another permanent ID is rejected.

This does **not** solve general symbolic equivalence. Trigonometric transformations, substitutions, equality of integral values and cross-technique isomorphisms are not exhaustively identified. Equal final answers alone do not make two different problems identical. The second-order Riemann family has an exact basis dependency whose smallest coefficient changes exceed the permitted 1–16 cube; the bounded instances remain distinct. Family IDs remain visible to the sampler regardless of parameter changes.

## Review and quarantine

A deterministic stratified review file contains the first and last retained instance of every family at each stage. All 72 families also have a small committed fixture. Review checks statements, domains, methods, identity/render consistency, answer rank patterns and source rights. Automated independent review is recorded as automated; it must never increment `humanReviewedCount`.

Pre-production v1 drafts were withdrawn after automated review discovered (1) a rendered Euler initial-condition product and (2) a dependent rational kernel that defeated expansion-only deduplication. Their local artifacts were retained, and no production game used them. V2 substitutes structured initial conditions before rendering, canonicalizes rational expressions, checks basis rank, varies answer ranks and includes substantive family derivations. Regression tests preserve these findings.

Failed/unsupported mathematical artifacts remain outside published membership. The generator checkpoints rejects; the importer aborts a failed release before activation. Unverified historical AI output and Batch proposals are never silently approved.
