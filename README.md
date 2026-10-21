# calculus.gg

Competitive calculus practice and multiplayer games, hosted independently of Google AI Studio. The existing React App Router interface runs with Vinext on Cloudflare Workers through Sites. Firebase continues to hold the existing accounts, profiles, games and chat; this migration does not copy or erase that data.

## Local development

Use Node 24 and the committed lockfile:

```sh
npm ci
cp .env.example .dev.vars
npm run dev
```

Set `GEMINI_API_KEY` in the untracked `.dev.vars` file. Never prefix it with `NEXT_PUBLIC_`: AI requests now pass through `/api/questions` on the server. `GEMINI_MODEL` optionally overrides the existing `gemini-3.1-pro-preview` model.

Apply D1 migrations locally before testing AI requests, using the generated local Worker configuration as described in [DEPLOYMENT.md](DEPLOYMENT.md).

```sh
npm run typecheck
npm test
npm run build
```

The CI workflow performs these checks without an API key or access to production data. Signed-in Firebase requests and live Gemini results require runtime configuration and separate integration verification.

See [DEPLOYMENT.md](DEPLOYMENT.md) for hosting, Firebase domain setup, scaling limits and the rollback process.

Original AI Studio project: https://ai.studio/apps/2e3c04a9-27fc-4403-91e0-7e7c677e3ee6
