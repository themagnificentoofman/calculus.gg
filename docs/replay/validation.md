# Milestone 2 validation

The checkout starts from deployed Sites version 32. All accounts, existing game history, and the verified compact problem bank are retained. No production data migration is required.

- Full unit suite passed: 87 passing tests, with 3 environment-gated skips. Focused replay coverage includes 19 passing tests.
- Isolated Firebase Enterprise emulator suite: 19 passing tests, including real server replay chunks, direct-client access denial, early-finisher and cross-user gates, unchanged rewards on read, and full-history pagination over 85 Timestamp/string/numeric/object/unknown-date records.
- Bank mathematical checks: 8 passing tests. Local workerd/Miniflare smoke verified 72 fixture records and selected 3 unique validated problems. No generation call was made.
- Browser QA used disposable local fixtures; no production accounts or rounds were changed. The actual IndexedDB queue and capture hook recorded a two-question round (one correct, one incorrect), synchronized to Available, and reconstructed 16 client events plus 10 authoritative events. Observed question exposure, answer acceptance, feedback and Next timings remained distinct.
- Browser player checks: question/event seek, solution hidden until captured feedback, separate analysis, UTC timestamps, speed selection and automatic stop at the replay end. At 8×, a 15-second fixture stopped at exactly 15 seconds. Mobile-width layout was inspected.
- Browser history checks: page 3 displays records beyond 50; applying January 1–5 returns exactly 5 older fixture rounds and resets to page 1. Date editing uses an explicit Apply range action.
- A 20-question local round produced 124 client events, 46 server events, 28 replay documents, 48,739 JSON bytes and 52 additional replay document writes. Loading required 4 replay HTTP requests. In-memory load took about 3.2 ms; this excludes real network/provider latency. A 4,096-event seek fixture compiled in about 2.4 ms and 100 seeks took about 1.5 ms. See measurements.json.

Temporary browser QA routes were removed before packaging. No private keys, full bank corpus, import bundle, or authentication bypass is part of the replay implementation. The production bank-import route remains disabled. Final source, saved version, deployment status and production smoke results are recorded after publication.

Stored history details retain available answer XP and rating receipts. Replay analysis summarizes authoritative accuracy and topics, explicitly excludes unanswered questions and missing timing intervals, and shows cumulative score/progress at each accepted answer.
