These corrections cover all 157 admitted families supplied by the frozen coverage builder for integration, differentiation, limits, and series: 1,256 existing records, eight instances per family. Multivariable and the separately authored extension modules are outside this bounded audit.

Runtime integration requires only `solutions.py` and `correction-data.json`. Call `supports(original_record)`, then `corrected_solution(original_record)`. Call `corrected_statement(original_record)` on the same original record for the eight same-semantic rising-factorial notation clarifications; it returns `None` otherwise. Do not mutate the input between these calls. Both correction APIs check the complete original record digest in addition to its problem ID, family, instance, and content hash. All answer choices, answer identifiers, and original content remain unchanged.

The authoring code uses SymPy and the immutable content builder as a source of the actual expressions and instance parameters. To reproduce from a repository copy:

```sh
BANK_AUDIT_ARTIFACT=/absolute/path/to/cn-2026-11-03-ideas-v3.jsonl .bank-venv/bin/python scripts/bank/solution-review/coverage/generate.py
node scripts/bank/solution-review/coverage/render-check.cjs
```

The generator infers `scripts/bank/content` from repository ancestors. Set `BANK_AUDIT_CONTENT_DIR` to override it. The renderer infers the repository's KaTeX package; set `BANK_AUDIT_KATEX` to override it. The source digest manifest records the precise artifact and frozen input modules used.

The family audit lists every reviewed family and all eight original IDs. Each correction carries its original content hash and complete record digest, a family review evidence ID, the specific issues addressed, the revised derivation, and executed mathematical checks. Checks of newly displayed derivatives, substitutions, partial fractions, finite recurrences, rescalings, or coefficient identities are distinct from the unchanged-answer guard. Standard analytic theorem applications include their hypotheses and are explicitly distinguished from symbolic equalities. Neither an AI editorial review nor a successful CAS identity check is labeled a human review or a formal proof.

The corrected explanations remove unused builder parameters, bind any auxiliary functions or sequences, show concrete endpoints and decisive identities, distinguish bounds from equality and approximations from exact values, and give branch, domain, and convergence reasons when a step requires them. Natural logarithms use `\ln`, inverse trigonometric functions use conventional arc names, and differentials are upright. Mathematical formulas remain math; prose is not split into fixed-width gathered fragments.

For future content, run the mathematical checks and strict render check on the entire admitted finite instance domain. A new instance, changed statement, or changed solution requires fresh evidence and a new source guard. Reusing a family label is not evidence that an unseen instance is covered. Never publish a correction whose necessary symbolic or analytic step remains unresolved.
