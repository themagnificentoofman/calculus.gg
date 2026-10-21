# Standalone deployment

## Hosting and configuration

The source is prepared for Sites-managed Cloudflare Workers with a D1 `DB` binding. `.openai/hosting.json` retains the registered Site identity. Publishing applies the committed D1 schema before switching the Worker version. Keep the runtime secret in the hosting service's environment-variable controls, never in Git, a browser bundle, or the hosting manifest.

| Runtime value | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Required server-only Gemini credential |
| `GEMINI_MODEL` | Optional model override; defaults to the original `gemini-3.1-pro-preview` |
| `DB` | Sites-provisioned D1 binding for shared AI usage counters |

The initial Site is private. Expected host: `calculus-gg.honeybox19.chatgpt.site`. Registration alone does not confirm a successful deployment.

`GET /api/health` reports `status: "ok"` and an `aiConfigured` boolean; it never returns secret values. A healthy response does not verify Firebase console settings, Gemini quota, or model access.

## Firebase: preserve existing users and data

`firebase-applet-config.json` is the existing browser Firebase configuration and named Firestore database. It is intentionally retained so accounts and game history are not silently moved to an empty database.

Before testing Google sign-in, add `calculus-gg.honeybox19.chatgpt.site` to the existing project's **Authentication → Settings → Authorized domains** in the Firebase console. Add any later custom domain there as well. Confirm Google and email/password providers remain enabled. If the Firebase browser API key has HTTP-referrer restrictions, authorize the new origin. No production Firebase settings or records were changed by the code migration.

AI endpoints independently verify Firebase ID tokens with Google's public signing keys, the existing project audience/issuer, expiration, subject, issued-at and authentication-time claims. Tokens are not checked for revocation or account disablement on every request; they can remain valid until expiry. Firebase continues to enforce database access rules.

## Scaling and cost boundaries

* Requests run on stateless Workers; secrets and AI prompts remain server-side.
* D1 counters are shared by all Worker instances. Conditional atomic upserts enforce 5 generation requests per user per minute, 60 per user per UTC day, and 200 across the Site per UTC day. Rejected requests can conservatively consume another counter's slot. Review these intentional initial limits in `lib/server/quota.ts` before widening access.
* The endpoint accepts only known topics/difficulties and 1–20 questions; request bodies are capped at 4 KB. Gemini requests have a 70-second timeout and a maximum of 24,000 output tokens. Gemini and hosting quotas can independently limit throughput.
* Model output must match the requested question count, topic/difficulty and UI data structure. This validates structure, not mathematical correctness.
* Existing Firebase listeners remain in place. Firebase billing, indexes and listener volume remain part of capacity planning.
* Existing prototype Firestore rules allow broad authenticated game updates and self-edited rating/XP. This hosting migration does not make competition scores tamper-proof. Server-authoritative scoring and tighter membership rules are necessary before treating public ratings as trustworthy.

## Validation and release

CI runs a clean install, type checking, server-boundary tests and production build. Tests cover malformed/oversized requests, invalid AI output, JWT issuer/audience/expiry checks, and shared quota SQL. CI does not contact production Firebase or spend Gemini quota.

For local D1 after `npm run build`:

```sh
npx wrangler d1 migrations apply DB --local --config dist/server/wrangler.json --persist-to .wrangler/state
```

Then run `npm run start`. Local data is separate from hosted data. Keep generated migrations and metadata committed; append future migrations instead of editing an applied migration.

Use the Sites source helper to push the exact source commit, package the matching build and publish a saved version. Roll back by deploying a prior saved version. D1 schema changes are not automatically reversed by a code rollback; this initial migration adds only the independent quota table. GitHub remains the reviewable source; a GitHub push by itself is not configured to publish the Site automatically.

After secrets/domain setup, verify Google and email sign-in, question generation in each mode, joining a game, chat, leaderboard and existing history. These checks must be performed before calling the migration fully operational.
