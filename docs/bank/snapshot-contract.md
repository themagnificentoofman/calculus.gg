# Immutable problems and replay-ready snapshots

`problemId` identifies a problem permanently; `problemRevision` is a positive, consecutive revision. New seed IDs use a truncated SHA-256 semantic identity (`cn_` plus 20 hexadecimal characters), with full hashes checked for collisions. A correction explicitly retains the original ID and increments the revision. `contentHash` covers the entire immutable record, including mathematical content, choices, key, derivation, assumptions, provenance, estimates and validation evidence. Publication is a separate mutable state. A release membership links an immutable revision to its bank version.

The private record has four opaque stable choice IDs and `answerChoiceId`. Choice IDs are mathematical-content hashes, not answer labels. `bank_problems` rejects UPDATE and DELETE; `bank_slots` rejects membership mutation. Old revisions remain resolvable through operator tools and historical snapshots. Retirement records a reason and excludes a revision from subsequent selections. `bank_statistics` is reserved for measured attempts/correct/solve-time aggregates; estimated difficulty/solve time stays explicitly labelled in content.

A question set is an authenticated, owner-bound, mode-bound, expiring, single-use issuance reference. It is **not** a permanent problem ID. The existing set-to-game transition and server transactions remain authoritative.

Each new bank round stores `roundSnapshot` in `gameSecrets`:

```ts
{
  schemaVersion: 1,
  selectionPolicy: 'family-uniform-v1',
  relaxation: 'none' | 'recent-families' | 'recent-problems' | 'family-cap',
  questions: [{
    ordinal: 0,
    problemId: 'cn_…',
    problemRevision: 1,
    contentHash: 'full SHA-256',
    bankRelease: 'release ID',
    familyId: 'method family',
    choiceOrder: ['opaque choice ID', '…', '…', '…']
  }]
}
```

The ordered array is the actual round order, and `choiceOrder` is the actual one-time server permutation. The private `questions` array also retains the full displayed content, correct index and explanations, so replay does not depend on a later active release or corrected template. All competitors use that same snapshot. Answer indexes refer to the recorded permutation. A future replay implementation must verify content hashes and preserve the original order; it must not regenerate choices or replace old content with the latest revision.

Public game projection is an explicit question-field allowlist: statement, four options, topic, difficulty, ID and revision. Waiting competitive lobbies reveal no questions. Answer keys, choice mappings, validation payloads, provenance details and unrevealed explanations remain server-side. Accepted-answer reviews expose only that player's existing staged feedback. There is no arbitrary-ID public answer endpoint. The report endpoint accepts a reference and reason and returns no content.

Legacy snapshots retain their original representation without invented IDs or retrospective bank-release claims. Existing accounts, XP, ratings and result receipts are neither migrated nor rewritten.
