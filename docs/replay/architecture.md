# Milestone 2: private round replay and full history

Base: deployed Sites version 32, source efaf1f0e27037f86c1979048fbf6535700c50dc6. The compact D1 bank, permanent IDs, release, mappings and receipts are unchanged. Replay storage uses the existing Firestore Enterprise database and server identity. The bank importer stays disabled.

## Capture and authority

New games have replayVersion 1 independently of progressionVersion 3. Existing and already-active games without that capability remain Legacy; sparse historical timelines are never converted into fabricated replays. The server freezes the exact statements, choice IDs/order, explanation, answer key, problem IDs/revisions/hashes, release and available context in replayContent. Replay never reselects from the current bank.

Each authoritative transition writes a bounded replayServer chunk and replayManifests record in the same transaction as game state, answers, XP and rating receipts. Event IDs derive from an operation UUID allocated outside transaction retries, with the client request ID retained separately for correlation. Duplicate accepted answers return the original event and cannot re-award points. Valid participant answer rejections are recorded without awarding anything. Invalid authentication and malformed requests fail before recording. Chat and profile secrets are excluded.

Client events are observations, not authority. IndexedDB saves events incrementally. An immutable pending envelope remains until an acknowledgement; a lost response retries the exact same chunk/hash. Segment leases serialize upload attempts across tabs. New page loads create new monotonic clock segments. A server handshake supplies an anchor and RTT uncertainty; orphan segments without a recoverable anchor stay unaligned. Background synchronization runs outside replay routes and resumes queued work for the signed-in owner. Local storage failure produces a capture gap when storage recovers.

A snapshot, row count, or closed session alone cannot establish Available. Every accepted answer needs exposure, submission and response observations, plus displayed feedback in modes that display solutions. Missing events, missing chunks, unclosed sessions, uncertain clocks and context gaps produce Partial. Untimed Test can remain active after page leave: replay does not invent a timeout or forfeit.

## Storage and access

Server-only collections: replayContent, replayManifests, replayServer, replayCapture, replayClient. Existing default-deny Firestore rules prohibit direct client access. All replay HTTP endpoints verify a Firebase token and participant membership. Content and every chunk-read endpoint enforce the whole-match terminal gate, even for early finishers. Detailed opponent answer events and client traces are excluded. Own snapshots and public match aggregates are available after completion/cancellation. No public share route exists.

The manifest contains mode/settings/participants, app and rules versions, clock anchors/deadlines, logical end, later settlement time and saved result receipts. Original countdown/elapsed/remaining time is independent of playback speed. A deterministic reducer plus checkpoints supports arbitrary seek; PlaybackClock uses monotonic elapsed time rather than frame count. Analysis reveals solutions separately from captured feedback.

## History and retention

No history or synchronized-replay eviction/TTL is introduced. Page size 25 limits display and transfer, never stored record count. Filters execute before limits. Stable per-encoding keyset cursors merge Timestamp, ISO, numeric and older timestamp-object records; unknown dates remain reachable under All dates. The unique __name__ document ID breaks timestamp ties. Legacy ffa is displayed and filtered as Multiplayer. A missing result receipt is labeled unknown, never reconstructed as an authoritative reward result. Legacy text: “Legacy — replay was not recorded for this round.”

Explicit client-capture bounds per player/round: 4096 events, 32 segments, 128 chunks per segment; 32 events and 24 KB per chunk. Limit/failure does not remove rounds or change gameplay results. Unsynchronized local events are retained until acknowledged; clearing browser data can lose them. Metadata is retained. Small default capture bounds can produce Partial during unusually long/high-interaction sessions.

## Cost, tests and rollback

An authoritative transition adds two Firestore document writes (chunk + manifest); creation adds one immutable content snapshot. Each client chunk adds two writes (chunk + capture summary), and each newly opened segment adds one summary write. These are document operations, not a claim about provider billing units or remaining quota. Replay reads are paginated by 16 chunks; the UI requests history status for at most 25 rounds. No D1 content writes or generation calls are introduced.

Tests cover all four modes/both Multiplayer win conditions, transactions/retries/duplicates, match-level secrecy, cross-user reads, immutable snapshots, missing/out-of-order/conflicting chunks, offline response loss, multi-tab queue leases, clock segments, penalties, feedback dwell, delayed settlement, seek equivalence, playback speeds/background time and >50-record history with mixed encodings/date ranges. See the validation report for measured sizes and latency.

Rollback: redeploy saved Sites version 32 with its existing environment and bindings. It ignores new replay collections/fields and continues existing gameplay; do not delete replay collections, accounts, game histories, bank rows or receipts. Newly started rounds after rollback will be Legacy. Keep this version's source/archive to restore replay access later. No schema migration or security-rule relaxation is required.
