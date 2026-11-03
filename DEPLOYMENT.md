# Standalone deployment

## Hosting and configuration

The source is prepared for Sites-managed Cloudflare Workers with a D1 `DB` binding. `.openai/hosting.json` retains the registered Site identity. Publishing applies the committed D1 schema before switching the Worker version. Keep runtime secrets in the hosting service's environment-variable controls, never in Git, a browser bundle, or the hosting manifest.

| Runtime value | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional offline operator authoring credential; not required by gameplay |
| `OPENAI_MODEL` | Legacy generation setting; not used by bank gameplay |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Dedicated server identity with `roles/datastore.user`, conditioned to the existing named database |
| `DB` | Sites-provisioned D1 binding for the indexed problem bank, reports and shared request counters |

The Site retains its existing access settings. Primary domain: `calculus.ninja`. Custom-domain registration alone does not confirm DNS validation, certificate issuance, or successful routing.

`GET /api/health` reports `status: "ok"` and `bankConfigured` / `secureGameplayConfigured` booleans and `questionSource: "bank"`; it never returns secret values. A healthy response does not verify Firebase console settings, the active bank release or its content.

## Firebase: preserve existing users and data

`firebase-applet-config.json` is the existing browser Firebase configuration and named Firestore database. It is intentionally retained so accounts and game history are not silently moved to an empty database.

Before testing Google sign-in, add `calculus.ninja` to the existing project's **Authentication → Settings → Authorized domains** in the Firebase console. After verifying sign-in on the primary domain, remove obsolete application hostnames from Authorized domains. Keep the Firebase service domains required for authentication. Confirm Google and email/password providers remain enabled. If the Firebase browser API key has HTTP-referrer restrictions, authorize the new origin. The secure-gameplay rollout also requires the coordinated rules and public-profile migration below; deploying only the Worker is insufficient.

All game, question, profile and social endpoints independently verify Firebase ID tokens with Google's public signing keys, the existing project audience/issuer, expiration, subject, issued-at and authentication-time claims. Tokens are not checked for revocation or account disablement on every request; they can remain valid until expiry. Firestore rules deny all browser writes and restrict private reads; the server identity uses IAM and must remain limited to this database.

## Scaling and cost boundaries

Gameplay has no model generation/grading calls and no empty-bank fallback. Account-scoped bank selection limits (12 per minute) are separate from paid offline authoring budgets and the existing 120-operation mutation limit. See [bank costs](docs/bank/costs.md) and [operator rollout](docs/bank/operations.md) for exact sampling bounds, database costs, staged imports and rollback.

Answer validation, clocks, XP, rating snapshots and receipts remain in the existing Firebase server transactions. Historical accounts, results and question snapshots are preserved. The new D1 migration is additive. Import and activate the verified corpus before deploying the bank-only Worker; never deploy an empty-bank cutover as complete.

## Validation and release

CI runs a clean install, type checking, pinned symbolic math checks, unit tests, Enterprise Auth/Firestore emulator attack tests and a production build. Bank tests cover independent import verification, immutable identities, filtering, repetition, retirement, answer secrecy and zero-model gameplay. Legacy generation regression tests remain isolated from gameplay. Integration tests cover all four modes, concurrent answers/joins, owner-bound question sets, private answer keys and account data, unauthorized writes, server deadlines, offline opponents, exact-once settlement, chat and friend operations. CI does not contact production Firebase or spend OpenAI quota.

For local D1 after `npm run build`:

```sh
npx wrangler d1 migrations apply DB --local --config dist/server/wrangler.json --persist-to .wrangler/state
```

Then run `npm run start`. Local data is separate from hosted data. Keep generated migrations and metadata committed; append future migrations instead of editing an applied migration.

Use the Sites source helper to push the exact source commit, package the matching build and publish a saved version after verifying the hosted bank import. Roll back to a compatible server-authoritative version. Do not restore the old client-writable rules or deploy a legacy client-scoring version over the new rules. D1 schema changes are not automatically reversed by a code rollback; the quota and bank migrations are additive. GitHub remains the reviewable source; a GitHub push by itself is not configured to publish the Site automatically.

After secrets/domain setup, verify Google and email sign-in, bank selection in each mode, joining a game, chat, leaderboard and existing history. These checks must be performed before calling the migration fully operational.

## Custom domain

Attach `calculus.ninja` to the existing Site. At the registrar, set both apex A records returned by Sites and the TXT ownership-verification records. Retain unrelated DNS records. Refresh the custom-domain status until domain validation and TLS are active, then verify the homepage and sign-in at https://calculus.ninja. DNS and Firebase console changes are separate from source publication.

## Browser navigation

Page links use standard HTML anchors, and sign-in and game invitation redirects use browser navigation. This avoids the deployed Vinext client router failing with `TypeError: ... is not a function` when loading its navigation module. Full page loads retain Firebase sign-in state. Settings waits for Firebase authentication initialization before redirecting signed-out visitors.

## Offline authoring and bank activation

Use the protected offline Batch CLI in [the bank guide](docs/bank/README.md). Production gameplay does not require `OPENAI_API_KEY`. The original generation module remains only for legacy regression tests and is absent from the gameplay import graph. Batch proposals cannot directly publish bank content.

The new deployment requires the committed bank schema plus the separately stored verified corpus. See [operations](docs/bank/operations.md). A GitHub PR is reviewable source; Sites publishing and remote D1 bulk import are separate actions. Preserve the existing public audience and Firebase ownership.

## Coordinated secure-gameplay rollout

Target: Enterprise Native database `ai-studio-2e3c04a9-27fc-4403-91e0-7e7c677e3ee6` in project `gen-lang-client-0109864131` (us-east5). Keep the existing accounts and private `users` records.

1. Create a dedicated `calculus-game-server` service account. Grant only `roles/datastore.user` with condition `resource.name == "projects/gen-lang-client-0109864131/databases/ai-studio-2e3c04a9-27fc-4403-91e0-7e7c677e3ee6"`. This is data access, not project administration, rules publishing, Auth management or access to other databases. Store its JSON credential as the encrypted Sites runtime secret `FIREBASE_SERVICE_ACCOUNT_JSON`. Never commit the credential or use owner OAuth credentials in the Worker. See [Firebase’s database access guidance](https://firebase.google.com/docs/firestore/enterprise/create-databases#configure-per-database-access-permissions).
2. With that server identity, run `scripts/backfill-public-profiles.mjs` first in dry-run mode, then with `--apply`. It reads each current private profile in a transaction and writes only the explicit public projection to `users_public`; email, settings, friends and private history are excluded. It does not reset or award statistics. Pass the service-account JSON through stdin, not command-line arguments or tracked files.
3. Verify type checking, unit/integration tests and the matching production build. Deploy `firestore.rules` to the named database with `firebase deploy --only firestore:rules --project gen-lang-client-0109864131`. Immediately publish the matching Worker version with the configured secret. During this short cutover, old clients fail closed and must reload. Do not publish either half as a permanent partial deployment.
4. Confirm both health flags, signed-in bank selection, accepted-answer feedback, saved results, public leaderboard/history, Chat and Friends. Recheck that browsers cannot write scores/profiles/games or read private question keys. Keep the previous release as a code reference, not a security rollback.

Enterprise pipelines perform matchmaking, profile search, history, leaderboard and expired-game lookup on the database. Standard listeners remain specifically for real-time game state, the user’s own profile, friend presence, requests and invitations. Public game documents contain no answer keys, explanations or selected option indexes; owner-only review documents are written in the same transaction as accepted answers. Timed matches settle at the next server interaction or signed-in reconciliation, including after all participants disconnect.

`GET /api/health` only checks configuration presence. It does not prove the service identity’s IAM permissions, quota, or actual database connectivity. Protect and rotate the server credential through the hosting and Google Cloud controls.

Waiting competitive lobbies expire after 30 minutes. Host cancellation closes the lobby; other players can leave before start. Invitation acceptance verifies current friendship and joins the game in the same transaction. Closing a tab does not cancel an active game; its server deadline still applies.
