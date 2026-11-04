# Calculus Ninja notation and worked-solution standards

Version: `calculus-ninja-notation-v1` / `worked-solutions-v1`.
Player-facing reference: [Help → Mathematical notation](https://calculus.ninja/help#notation).
These rules apply to statements, choices, explanations, new families, standalone questions, and source adaptations. A source textbook's conventions do not override the product conventions.

The [standing problem-authoring standards](PROBLEM-AUTHORING-STANDARDS.md) extend these rules to construction variety, independent options-visible review, distractors, lineage, provenance, session quality, and safe publication. Follow their checklist for every addition and preserve newly demonstrated successes as documented rules with evidence.

## Reference policy

Use widely accepted mathematical forms, consulting Wolfram MathWorld for definitions and conventions. A reference can document several valid notations; pick one consistent, explicit convention instead of claiming a universal notation. Prefer the established spelling and symbol for a special function, and state its definition/domain where readers may not know it. Never copy a computer-language function identifier into mathematical prose.

Checked references (2026-11-03): [Natural logarithm](https://mathworld.wolfram.com/NaturalLogarithm.html) uses `ln` for base e; [Inverse tangent](https://mathworld.wolfram.com/InverseTangent.html) recognizes `arctan`; [Inverse hyperbolic sine](https://mathworld.wolfram.com/InverseHyperbolicSine.html) records accepted arc/area variants; [Pochhammer symbol](https://mathworld.wolfram.com/PochhammerSymbol.html) defines the rising factorial and explains the conflicting combinatorial convention. The site selects `arcsinh/arccosh/arctanh` with stated real domains, and `(a)_n` for the explicitly defined rising factorial.

## Notation

- Write the natural logarithm as `\ln x`. Write another base explicitly, for example `\log_{10}x` or `\log_b x`, with the base's domain stated. Never change an explicitly based logarithm into a natural logarithm.
- Use `\arcsin`, `\arccos`, `\arctan` for inverse circular functions; use `\operatorname{arcsinh}`, `\operatorname{arccosh}`, `\operatorname{arctanh}` for inverse hyperbolic functions. Avoid the ambiguous `sin^{-1}` convention. Trigonometric arguments are in radians unless stated otherwise.
- Use upright differentials, for example `\,\mathrm{d}x`, `\frac{\mathrm{d}y}{\mathrm{d}x}` and `\frac{\mathrm{d}^2y}{\mathrm{d}x^2}`. Partial derivatives use `\partial`; primes are appropriate when the independent variable is clear. Do not reinterpret an algebraic variable named `d` as a differential.
- Use real variables and principal nonnegative square roots unless another domain or branch is specified. Give logarithm domains; use `\ln|x|` for the real primitive of `1/x` on intervals avoiding zero. State complex branches explicitly when used.
- Include `+C` for an indefinite integral. A *chosen* antiderivative can omit it when identified as such and checked by differentiation. Apply actual endpoint values for definite integrals.
- Use `=` for equality, `\approx` for numerical approximation, `\sim` for asymptotic equivalence, and `O(\cdot)`/`o(\cdot)` with the relevant limit and order. Do not replace these relations with one another.
- Use `(a)_n` for a rising factorial and `a^{\underline{n}}` for a falling factorial; define the finite product and its empty-product value when these less familiar symbols appear.
- Set summation indices and limits, specify one-sided limits where needed, distinguish vectors from scalars, and define all auxiliary functions, constants, coordinates, special functions, and operators before using them. A letter has one clearly stated role within an argument.
- Use proper TeX superscripts, fractions, subscripts, function names, matrices and piecewise cases. Formula fragments such as `x^m` must be math, never escaped into prose.

## Worked solutions

1. Begin with the mathematical idea and connect it to this problem's displayed expression, bounds, point, domain or initial conditions.
2. Show the essential intermediate identity or transformation. Naming a technique and then printing the answer is insufficient. For harder problems, show why that technique applies: convergence, domination, branch choice, boundary terms, uniqueness, rank, symmetry, or exactness conditions as relevant.
3. Define every introduced symbol in a mathematical role. Do not expose internal builder parameters (`Here m = ...`) when the displayed question already contains the numerical instance. Prefer actual bounds over unexplained `F(b)-F(a)`.
4. Keep prose in normal responsive paragraphs; equations in complete display blocks; short mathematical phrases inline. Do not wrap prose into narrow centered `gathered` rows. Never split nested fractions, environments, or paired delimiters around a text command.
5. Finish with an explicit expression matching the verified correct choice. An answer string appended to unsupported claims is not a derivation.
6. Independently verify the result, uniqueness of the correct choice, assumptions, and displayed intermediate identities. Record what was executed and what rests on an analytic argument. Do not label automated checks as human review or formal proof.

## Admission and preservation

`lib/math-notation.mjs` implements conservative presentation normalization. It is not an algebraic simplifier and does not authorize changing a source's mathematical meaning. `lib/solution-format.mjs` separates top-level prose while preserving complete mathematical groups. `lib/bank/solution-quality.mjs` checks the mechanical rules; these checks cannot establish a proof's logic by themselves.

`lib/server/solution-presentation.mjs` admits only registered, reviewed presentations: exact source-hash-bound finite corrections, the audited legacy constructor on its bounded domain, and the independently reconstructed standalone polynomial v2 constructor. A new family or a new finite instance needs a mathematical/editorial review and a source-bound registry entry before publication; self-declared approval flags do not bypass the gate. `scripts/bank/admin.mjs` applies the gate on every insert; the delta path uses this same insert, after independent Python reconstruction. Changing a frozen constructor, answer, statement meaning, or parameter domain requires fresh verification and a revision, not silent presentation substitution.

The focused quality release adds `scripts/bank/quality/reviewed.json` and `quality/contract.py` for exact finite reviewed constructions and permitted adaptations, plus `lib/server/solution-reviews/quality.json` for their destination source bindings. A local registry entry is not evidence of production import. `ProblemStatement` uses the same protected mathematical grouping as `SolutionSteps`, with responsive prose and display treatment for long prompt equations.

For each addition:

- Write or extend a reproducible verifier and source-bound review; preserve licensing and provenance.
- Check every admitted instance, including its displayed intermediate identities and final choice, and retain edge/domain evidence for parameterized recipes.
- Run Python reconstruction/contracts, strict KaTeX and solution-quality checks, relevant application tests, and the Worker bundle smoke test. Inspect representative short/long/mixed solutions at desktop and mobile widths using the actual `SolutionSteps` component.
- Include notation version, review version, source and review-code digests, exact inventory/family counts, failures and verification limitations in the release evidence. Do not publish with missing coverage or a failing check.

Canonical bank records, content hashes, IDs, answers and saved round snapshots remain immutable. New rounds store the reviewed presentation. Reviews of older finite questions use a separate exact-source-bound explanation overlay; recorded playback keeps the saved explanation, while analysis labels later clarifications. Older snapshots without enough source evidence are never reconstructed by guessing. A correctness change requires a new revision and explicit historical treatment; this presentation update does not regrade previous results.
