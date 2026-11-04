# Original published ODE and multivariable baseline

This map covers all 768 ODE and multivariable records from the original published milestone-3 artifact, whose SHA-256 is `1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677`. It does not substitute later revision previews for the baseline.

Each topic originally had 384 records, with 96 published at each difficulty. `descriptor-map.json` preserves `publishedDifficulty`, the original content hash, full-record hash, actual choice-menu hash, and answer identity separately from `reviewedDifficulty`, `reviewedRoute`, and `qualifiedOlympiad`.

| Topic | Original peer-qualified records | Effective qualified records | Qualified normalized items | Qualified idea groups |
|---|---:|---:|---:|---:|
| Differential equations | 24 | 21 | 17 | 3 |
| Multivariable | 64 | 64 | 57 | 8 |

All 72 original multivariable peer records and all 72 original ODE route-review records match the published content hashes exactly. The 144 original normalization records also match. The multivariable peer’s aggregate input-file hash differs because it reviewed a subset; its per-record source bindings are exact. The ODE route review is a family-level editorial review applied across the finite coefficient domain, not a new independent solution of every instance.

Three original ground-state menus have a subsequently confirmed unique-length giveaway. Their old mathematical Olympiad decision remains visible in `reviewedDifficulty`, but `qualifiedOlympiad` is false for the original menu. The later repaired-menu qualification is never transferred backward. Other original-menu peer decisions remain explicit, even when a later candidate menu differs.

The 168 difficulty-only revision records bind the original content hash and preserve every literal choice, choice description, and answer ID. They support conservative lower-level editorial dispositions; they are not described as independent blind difficulty reviews. The independent density-centroid review additionally binds eight original canonical records and their unchanged menus, supporting Easy through the qualitative centroid bound.

Every original record has one final lineage match. For 736 records, the semantic task is unchanged, so the final construction descriptors and conservative normalized task key can be reused without new idea credit. The remaining 32 lower-level records changed semantic identity; they retain original descriptors and separate original task keys. Final classification is not transferred to those records.

All 192 originally published Olympiad records have an explicit original-menu classification or source-bound lower-level disposition. Lower-level records without a newly bound classification use `reviewedDifficulty: null`; their published labels remain intact. This reconciliation does not claim a fresh mathematical solve of all 768 problems or describe the size of the complete four-topic candidate pool.

Run `python3 verify.py` to check the portable evidence and source joins. `reconcile.py` records the original repository-bound reconciliation process; rerunning it requires the original published artifact in the adjacent milestone-3 checkout.
