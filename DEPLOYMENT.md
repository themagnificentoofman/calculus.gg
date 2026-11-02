# Standalone deployment

## Hosting and configuration

The source is prepared for Sites-managed Cloudflare Workers with a D1 `DB` binding. `.openai/hosting.json` retains the registered Site identity. Publishing applies the committed D1 schema before switching the Worker version. Keep the runtime secret in the hosting service's environment-variable controls, never in Git, a browser bundle, or the hosting manifest.

| Runtime value | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required server-only OpenAI credential |
| `OPENAI_MODEL` | Optional model override; defaults to the `gpt-5-mini` |
| `DB` | Sites-provisioned D1 binding for shared AI usage counters |

The Site retains its existing access settings. Primary domain: `calculus.ninja`. Custom-domain registration alone does not confirm DNS validation, certificate issuance, or successful routing.

`GET /api/health` reports `status: "ok"` and an `aiConfigured` boolean; it never returns secret values. A healthy response does not verify Firebase console settings, OpenAI quota, or model access.

## Firebase: preserve existing users and data

`firebase-applet-config.json` is the existing browser Firebase configuration and named Firestore database. It is intentionally retained so accounts and game history are not silently moved to an empty database.

Before testing Google sign-in, add `calculus.ninja` to the existing project's **Authentication → Settings → Authorized domains** in the Firebase console. After verifying sign-in on the primary domain, remove obsolete application hostnames from Authorized domains. Keep the Firebase service domains required for authentication. Confirm Google and email/password providers remain enabled. If the Firebase browser API key has HTTP-referrer restrictions, authorize the new origin. No production Firebase settings or records were changed by the code migration.

AI endpoints independently verify Firebase ID tokens with Google's public signing keys, the existing project audience/issuer, expiration, subject, issued-at and authentication-time claims. Tokens are not checked for revocation or account disablement on every request; they can remain valid until expiry. Firebase continues to enforce database access rules.

## Scaling and cost boundaries

* Requests run on stateless Workers; secrets and AI prompts remain server-side.
* D1 counters are shared by all Worker instances. Conditional atomic upserts enforce 5 generation requests per user per minute, 60 per user per UTC day, and 200 across the Site per UTC day. Rejected requests can conservatively consume another counter's slot. Review these intentional initial limits in `lib/server/quota.ts` before widening access.
* The endpoint accepts only known topics/difficulties and 1–20 questions; request bodies are capped at 4 KB. OpenAI Responses requests have a 70-second timeout and a maximum of 24,000 output tokens (including reasoning). Responses are not stored (`store: false`); a strict JSON schema constrains every question and server validation checks the returned set again. OpenAI and hosting quotas can independently limit throughput.
* Model output must match the requested question count, topic/difficulty and UI data structure. Every problem, option, and explanation step must also render with the same KaTeX configuration used in the browser. This validates structure and notation, not mathematical correctness.
* Existing Firebase listeners remain in place. Firebase billing, indexes and listener volume remain part of capacity planning.
* Existing prototype Firestore rules allow broad authenticated game updates and self-edited rating/XP. This hosting migration does not make competition scores tamper-proof. Server-authoritative scoring and tighter membership rules are necessary before treating public ratings as trustworthy.

## Validation and release

CI runs a clean install, type checking, server-boundary tests and production build. Tests cover malformed/oversized requests, invalid AI output, JWT issuer/audience/expiry checks, and shared quota SQL, plus Responses API schema construction, refusals, incomplete output and sanitized provider errors. CI does not contact production Firebase or spend OpenAI quota.

For local D1 after `npm run build`:

```sh
npx wrangler d1 migrations apply DB --local --config dist/server/wrangler.json --persist-to .wrangler/state
```

Then run `npm run start`. Local data is separate from hosted data. Keep generated migrations and metadata committed; append future migrations instead of editing an applied migration.

Use the Sites source helper to push the exact source commit, package the matching build and publish a saved version. Roll back by deploying a prior saved version. D1 schema changes are not automatically reversed by a code rollback; this initial migration adds only the independent quota table. GitHub remains the reviewable source; a GitHub push by itself is not configured to publish the Site automatically.

After secrets/domain setup, verify Google and email sign-in, question generation in each mode, joining a game, chat, leaderboard and existing history. These checks must be performed before calling the migration fully operational.

## Custom domain

Attach `calculus.ninja` to the existing Site. At the registrar, set both apex A records returned by Sites and the TXT ownership-verification records. Retain unrelated DNS records. Refresh the custom-domain status until domain validation and TLS are active, then verify the homepage and sign-in at https://calculus.ninja. DNS and Firebase console changes are separate from source publication.

## Browser navigation

Page links use standard HTML anchors, and sign-in and game invitation redirects use browser navigation. This avoids the deployed Vinext client router failing with `TypeError: ... is not a function` when loading its navigation module. Full page loads retain Firebase sign-in state. Settings waits for Firebase authentication initialization before redirecting signed-out visitors.

## OpenAI activation

Set `OPENAI_API_KEY` as a secret and optionally `OPENAI_MODEL` in Sites runtime environment settings, then deploy a saved version to apply the new environment revision. The default is `gpt-5-mini` with low reasoning effort. No OpenAI credential is used at build time or sent to browsers. All four game modes call the same authenticated `/api/questions` endpoint.

The API organization must have usable credit and model access. `credit_balance_exhausted` / `insufficient_quota` requires adding API credit; it is not fixed by retrying or replacing the key. A ChatGPT subscription does not supply API billing. `aiConfigured: true` checks the runtime secret and database binding only; it does not prove billing or generation works. Verify a signed-in game after activation.
