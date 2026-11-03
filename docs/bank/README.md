# Indexed problem bank

Normal gameplay selects approved, persisted D1 revisions. It never imports the OpenAI authoring module or calls a model for selection or grading. Firebase remains authoritative for identity, profiles, private question sets, game snapshots, clocks, XP, ratings, reviews and receipts. The original four modes and round termination rules are unchanged.

## Baseline and ownership

The current serving layout is `compact-gzip-shared-v1`; see [the measured storage comparison](storage/README.md) and [controlled rollout](operations.md). The existing 100,800 records are preserved; do not regenerate them for this rollout. The following generation commands document authoring reproducibility, not a deployment prerequisite. Milestone 1 completed on 2026-11-03: **100,800 imported, fully verified and active problems**, **260,400 verified memberships**, and **1,850 reconciled batch receipts** for `cn-2026-11-02-full-v2`. The explicitly authorized [operator-budget mode](operator-budget.md) ran within fixed cumulative operating limits; provider remaining quota telemetry stayed unknown. Hosted canonical/hash/publication/membership verification and all 24 selection cells passed before guarded activation. Test, Rapid, PvP and Multiplayer passed isolated hosted engine/Firestore checks, including shared snapshots, scoring, history and errors. Temporary import access is disabled. A personal Cloudflare account was not needed.

Inspected GitHub `main` at `1397e5c` on November 2, 2026. The Sites source commit `ba3eb419` had an identical tree but divergent history; the feature branch reconciles both histories. The existing public Site is `appgprj_6ad91db3d4788191b3e73074e27447f5` at https://calculus.ninja. GitHub pushes do not automatically deploy it.

There was **no actual curated/preset corpus** in the repository. `tests/math-fixtures.mjs`, mocked AI output and emulator fixtures are tests, not reusable approved content. Live D1 inspection found only `ai_quota`. Existing Firestore AI question snapshots were not promoted, reclassified, rewritten or assigned fabricated bank IDs. Initial retained/imported problem count: **0**. The new corpus is an explicit original seed.

D1 stores immutable mathematical revisions and release membership; mutable publication state, reports and future measured statistics use separate tables. The existing named Firebase database and service identity are unchanged. No new service is required.

## Reproduce the corpus

Use the locked Node dependencies and pinned mathematical verifier:

```sh
npm ci
python3 -m venv .bank-venv
.bank-venv/bin/python -m pip install -r scripts/bank/requirements.txt
npm run bank:verify

.bank-venv/bin/python scripts/bank/pipeline.py --stage pilot
node scripts/bank/admin.mjs import .bank-data/bank.sqlite .bank-data/cn-2026-11-02-pilot-v2.manifest.json
node scripts/bank/admin.mjs activate .bank-data/bank.sqlite cn-2026-11-02-pilot-v2

.bank-venv/bin/python scripts/bank/pipeline.py --stage expanded
node scripts/bank/admin.mjs import .bank-data/bank.sqlite .bank-data/cn-2026-11-02-expanded-v2.manifest.json
node scripts/bank/admin.mjs activate .bank-data/bank.sqlite cn-2026-11-02-expanded-v2

.bank-venv/bin/python scripts/bank/pipeline.py --stage full
node scripts/bank/admin.mjs import .bank-data/bank.sqlite .bank-data/cn-2026-11-02-full-v2.manifest.json
node scripts/bank/admin.mjs activate .bank-data/bank.sqlite cn-2026-11-02-full-v2
npm run bank:benchmark
node --experimental-strip-types scripts/bank/audit.mjs
```

Targets are 14, 140 and 1,400 retained instances per family: **1,008 / 10,080 / 100,800**. Each stage runs the same mathematical, render, identity and coverage gates. A SQLite checkpoint records deterministic parameter seeds and rejected items. Restarting continues the job; imports reconcile identical existing rows and slots. Conflicting revisions/manifests abort. Run timings and per-run counters are operational reports, excluded from immutable release identity. A partial import stays staging and cannot be selected. Preserve failed checkpoints for investigation; change the recipe version when changing mathematical definitions.

The importer reconstructs every item from its supported mathematical recipe using the independent verifier before mutating release content. A JSON `passed` flag alone cannot authorize an import. Unknown families, unsupported external text, invalid parameters, altered formulas, explanations or answer keys fail closed. New authoring proposals require an implemented and verified recipe before import.

Generated JSONL, SQLite, SQL exports, review samples and job checkpoints are private operator artifacts in ignored `.bank-data/`; they contain answer keys. Never put them in `public/`, browser bundles, a public download endpoint or Git. Commit recipes, small fixtures, manifests and reports. Back up the release artifact and checksum in private persistent storage before production import.

## Mathematical gates and coverage

See [validation and diversity](validation.md), [source register](sources.md), [snapshot contract](snapshot-contract.md), [operations](operations.md), and [costs](costs.md). `docs/bank/releases/` contains measured release/benchmark reports; a manifest's approved count is not evidence of production deployment.

Original templates were authored with interactive AI assistance and checked automatically. **Human-reviewed count is zero.** Difficulty and solve time are estimates, separate from measured telemetry. Gameplay makes no claims of infinite variety or an unverified public problem count.
