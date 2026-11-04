# Problem-bank authoring

Before changing or adding content, read `../../docs/bank/PROBLEM-AUTHORING-STANDARDS.md` and `../../docs/bank/NOTATION-AND-SOLUTIONS.md`. Follow their mathematical-decision, finite-domain, options-visible difficulty, independent-verification, notation, source-binding, lineage, provenance, and admission requirements. These apply equally to bulk families, standalone questions, and adaptations. Complete the authoring checklist and add evidence-backed practices that worked to the standing guide and release handoff; distinguish local checks from imported or deployed results.

Preserve frozen constructors used to reconstruct existing immutable releases. Do not update a certificate hash merely to make a changed constructor pass. A new instance or family needs a source-bound reviewed solution, strict rendering, and independently checked mathematics before it can be admitted. Run the publication gate through `admin.mjs` / the delta workflow. Unknown or unreviewed families must fail closed; never bypass the gate by setting a validation flag.

Preserve historical integrity while requiring active legacy content to earn its place through demonstrated quality and usefulness. Retention, repair, reclassification and withdrawal need evidence tied to the actual content; age or raw item count alone does not justify a decision. Useful older fluency remains eligible when it meets the same review standards as new work.

Read `../../docs/bank/problem-quality/LEGACY-POLICY.md` before admitting legacy content. Experimental opt-in defaults off; it is not an exception to quality admission. Exact source/review evidence, original construction lineage and the Legacy marker are required. Default practice horizons must pass without optional legacy; competitive modes use the common nonlegacy pool.

Never rewrite published hashes, answer keys, saved games, ratings, or replay snapshots to fix explanation formatting. Use reviewed presentation corrections for non-semantic clarifications, and new immutable revisions for mathematical changes.
