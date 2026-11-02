# calculus.ninja

Competitive calculus practice and multiplayer games, hosted independently of Google AI Studio. The existing React App Router interface runs with Vinext on Cloudflare Workers through Sites. Firebase continues to hold the existing accounts, profiles, games and chat; this migration does not copy or erase that data.

## Local development

Use Node 24 and the committed lockfile:

```sh
npm ci
cp .env.example .dev.vars
npm run dev
```

Set `OPENAI_API_KEY` in the untracked `.dev.vars` file. Never prefix it with `NEXT_PUBLIC_`: AI requests pass through `/api/questions`; it returns an opaque question-set ID. Answer validation, XP and ratings run on authenticated server endpoints. Configure `FIREBASE_SERVICE_ACCOUNT_JSON` with a dedicated database-scoped identity for real Firebase use. `OPENAI_MODEL` optionally overrides the existing `gpt-5-mini` model.

Apply D1 migrations locally before testing AI requests, using the generated local Worker configuration as described in [DEPLOYMENT.md](DEPLOYMENT.md).

```sh
npm run typecheck
npm test
npm run build
```

The CI workflow performs these checks without an API key or access to production data. Signed-in Firebase requests and live OpenAI results require runtime configuration and separate integration verification.

See [DEPLOYMENT.md](DEPLOYMENT.md) for hosting, Firebase domain setup, scaling limits and the rollback process.

## Contact form

`/contact` sends bug reports, balance feedback, and questions to the owner's fixed inbox through Resend. Set the encrypted server secret `RESEND_API_KEY` and `CONTACT_FROM_EMAIL` to a sending address authorized by that Resend account. No browser credential or public email relay is used. See the [Resend email API](https://resend.com/docs/api-reference/emails/send-email) for sender setup.

The authenticated `/api/contact` endpoint verifies Firebase tokens and takes the reply-to address from the account claims. Existing D1 quota storage enforces a rolling 60-second account cooldown, 10 submissions per account per UTC day, and 100 total per UTC day, including failed delivery attempts. Conditional SQL updates enforce limits across concurrent requests and Worker instances. GET returns the remaining server cooldown after reload. Provider idempotency keys protect an unchanged message retried after an ambiguous delivery failure. The form retains failed messages and never reports delivery success on provider errors.

Local tests use an in-memory SQLite database and fake email delivery; they do not send email. Live delivery requires the two production environment settings above.

Primary domain: https://calculus.ninja
