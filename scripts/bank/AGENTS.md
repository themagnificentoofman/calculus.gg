# Problem-bank authoring

Before changing or adding content, read `../../docs/bank/NOTATION-AND-SOLUTIONS.md` and follow its notation, derivation, independent-verification, source-binding, and admission requirements. These apply equally to bulk families and standalone questions.

Preserve frozen constructors used to reconstruct existing immutable releases. Do not update a certificate hash merely to make a changed constructor pass. A new instance or family needs a source-bound reviewed solution, strict rendering, and independently checked mathematics before it can be admitted. Run the publication gate through `admin.mjs` / the delta workflow. Unknown or unreviewed families must fail closed; never bypass the gate by setting a validation flag.

Never rewrite published hashes, answer keys, saved games, ratings, or replay snapshots to fix explanation formatting. Use reviewed presentation corrections for non-semantic clarifications, and new immutable revisions for mathematical changes.
