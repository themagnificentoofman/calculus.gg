# calculus.ninja

Competitive calculus practice and multiplayer games, hosted independently of Google AI Studio. The existing React App Router interface runs with Vinext on Cloudflare Workers through Sites. Firebase continues to hold the existing accounts, profiles, games and chat; this migration does not copy or erase that data.

## Local development

Use Node 24 and the committed lockfile:

```sh
npm ci
cp .env.example .dev.vars
npm run dev
```

Normal gameplay uses the indexed problem bank and makes zero OpenAI selection or grading calls. Configure `FIREBASE_SERVICE_ACCOUNT_JSON` with the existing dedicated database-scoped identity. Apply the D1 migration and import/activate a verified bank release before starting games. An empty filter returns an explicit insufficient-content response.

See [the problem-bank guide](docs/bank/README.md) for reproducible 1,008 / 10,080 / 100,800-instance stages, mathematical validation, immutable revisions, offline Batch authoring, reports, benchmarks and rollout. Private generated payloads stay outside Git and browser assets. `OPENAI_API_KEY` is only needed by the optional offline administrative authoring CLI.

```sh
python3 -m venv .bank-venv
.bank-venv/bin/python -m pip install -r scripts/bank/requirements.txt
npm run typecheck
npm test
npm run build
```

The CI workflow performs these checks without an API key or access to production data. Signed-in production Firebase requests and hosted bank imports require runtime configuration and separate deployment verification.

See [DEPLOYMENT.md](DEPLOYMENT.md) for hosting, Firebase domain setup, scaling limits and the rollback process.

## Contact form

`/contact` sends bug reports, balance feedback, and questions to the owner's fixed inbox through Resend. Set the encrypted server secret `RESEND_API_KEY` and `CONTACT_FROM_EMAIL` to a sending address authorized by that Resend account. No browser credential or public email relay is used. See the [Resend email API](https://resend.com/docs/api-reference/emails/send-email) for sender setup.

The authenticated `/api/contact` endpoint verifies Firebase tokens and takes the reply-to address from the account claims. Existing D1 quota storage enforces a rolling 60-second account cooldown, 10 submissions per account per UTC day, and 100 total per UTC day, including failed delivery attempts. Conditional SQL updates enforce limits across concurrent requests and Worker instances. GET returns the remaining server cooldown after reload. Provider idempotency keys protect an unchanged message retried after an ambiguous delivery failure. The form retains failed messages and never reports delivery success on provider errors.

Local tests use an in-memory SQLite database and fake email delivery; they do not send email. Live delivery requires the two production environment settings above.

Primary domain: https://calculus.ninja

Problem authors must follow the [notation and worked-solution standards](docs/bank/NOTATION-AND-SOLUTIONS.md). The publication path rejects unreviewed solutions; [Help → Mathematical notation](https://calculus.ninja/help#notation) documents the player-facing conventions.
