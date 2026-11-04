import { createServerGames, GameError, identifier } from './game-engine.ts';
import { BankUnavailableError, type RecentProblems } from './bank-selection.ts';
import type { RoundSnapshot, SelectionDiagnostics } from '../bank/contracts.ts';
import { socialAction } from './social.ts';
import { readBoundedJson, validateQuestionRequest, validQuestionResponse } from './questions-policy.mjs';
import type { Store, Data } from './firestore-admin.ts';
import type { GameQuestion } from '../game-progress.ts';
import type { GameMode } from '../progression.ts';
const response = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
const only = (body: Data, keys: string[]) => { if (!body || typeof body !== 'object' || Array.isArray(body) || Object.keys(body).some(k => !keys.includes(k))) throw new GameError('Unexpected request fields.'); };
const modes = ['test', 'rapid', 'pvp', 'multiplayer'];
export function createGameApi(deps: { store: Store; verify: (token: string) => Promise<Data>; select: (input: { category: string; difficulty: string; count: number; tag?: string }, recent: RecentProblems) => Promise<{ questions: GameQuestion[]; relaxation: RoundSnapshot['relaxation']; diagnostics?: SelectionDiagnostics }>; checkPlayable?: (questions: GameQuestion[]) => Promise<void>; quota: (uid: string) => Promise<boolean>; mutationQuota?: (uid: string) => Promise<boolean>; now?: () => number }) {
  const games = createServerGames(deps.store, deps.now);
  return async (resource: 'games' | 'profile' | 'questions' | 'social', request: Request) => {
    if (request.method !== 'POST') return response({ error: 'Use POST.' }, 405);
    const origin = request.headers.get('origin');
    if (origin && origin !== new URL(request.url).origin || request.headers.get('sec-fetch-site') === 'cross-site') return response({ error: 'Request origin is not allowed.' }, 403);
    const bearer = /^Bearer ([^\s]+)$/.exec(request.headers.get('authorization') || '');
    if (!bearer || bearer[1].length > 8192) return response({ error: 'Please sign in.' }, 401);
    let claims: Data;
    try { claims = await deps.verify(bearer[1]); identifier(claims.sub); } catch { return response({ error: 'Your sign-in has expired. Please sign in again.' }, 401); }
    const uid = claims.sub;
    try {
      let body: Data;
      try { body = await readBoundedJson(request, resource === 'profile' ? 320000 : 8192); } catch { throw new GameError('Send a valid JSON request.'); }
      if (!body || typeof body !== 'object' || Array.isArray(body)) throw new GameError('Send a JSON object.');
      if (deps.mutationQuota && !await deps.mutationQuota(uid)) throw new GameError('Too many requests. Please wait a moment and retry.', 429);
      if (resource === 'profile') { only(body, ['patch']); return response({ profile: await games.profile(uid, claims, body.patch ?? {}) }); }
      if (resource === 'questions') {
        only(body, ['mode', 'category', 'difficulty', 'count', 'tag']);
        const input = validateQuestionRequest(body);
        if (!input || !modes.includes(body.mode) || (body.tag !== undefined && (typeof body.tag !== 'string' || !/^[a-z][a-z0-9-]{1,63}$/.test(body.tag)))) throw new GameError('Choose a supported mode, category, difficulty and question count.');
        if (!await deps.quota(uid)) throw new GameError('Question selection limit reached. Please try again later.', 429);
        // Competitive sets use the common bank policy without adapting to the
        // host's personal practice history. The immutable order is shared.
        const recent = ['test','rapid'].includes(body.mode) ? await deps.store.get(`bankRecent/${uid}`) || {} : {};
        const { questions, relaxation, diagnostics } = await deps.select({ ...input, ...(body.tag ? { tag: body.tag } : {}) }, recent);
        if (!validQuestionResponse(questions, input)) throw new GameError('The problem bank returned an invalid set. Please retry.', 502);
        return response(await games.storeQuestions(uid, body.mode, input.category, input.difficulty, questions, relaxation, diagnostics));
      }
      if (resource === 'social') {
        const fields: Record<string, string[]> = { request: ['to'], remove: ['friendId'], invite: ['to', 'gameId'], accept: ['id'], reject: ['id'], cancel: ['id'], invite_accept: ['id'], invite_reject: ['id'] };
        if (typeof body.action !== 'string' || !Object.hasOwn(fields, body.action)) throw new GameError('Unsupported social action.');
        only(body, ['action', ...fields[body.action]]);
        for (const key of fields[body.action]) identifier(body[key]);
        if (body.action === 'invite_accept') return response(await games.acceptInvite(uid, body.id));
        return response(await socialAction(deps.store, uid, body.action, body, deps.now?.()));
      }
      const fields: Record<string, string[]> = { create: ['questionSetId', 'mode', 'options'], join: ['gameId', 'mode'], answer: ['gameId', 'index', 'selectedOption','requestId'], start: ['gameId'], leave: ['gameId'], view: ['gameId'], complete: ['gameId'], claim: ['gameId'], chat: ['gameId', 'text'], sync: [] };
      if (typeof body.action !== 'string' || !Object.hasOwn(fields, body.action)) throw new GameError('Unsupported game action.');
      only(body, ['action', ...fields[body.action]]);
      if (body.action === 'sync') { await games.sync(uid); return response({ ok: true }); }
      if (body.action === 'create') {
        if (!modes.includes(body.mode)) throw new GameError('Invalid game mode.');
        only(body.options || {}, ['category', 'difficulty', 'timeLimit', 'settings']);
        if (deps.checkPlayable && !await deps.store.get(`gameSecrets/${identifier(body.questionSetId)}`)) {
          const pending = await deps.store.get(`questionSets/${body.questionSetId}`);
          if (pending && pending.uid === uid) await deps.checkPlayable(pending.questions || []);
        }
        return response(await games.createGame(uid, identifier(body.questionSetId), body.mode as GameMode, body.options || {}));
      }
      return response(await games.act(uid, identifier(body.gameId), body.action, body));
    } catch (error) {
      if (error instanceof GameError) return response({ error: error.message }, error.status);
      if (error instanceof BankUnavailableError) return response({ error: error.message, code: 'INSUFFICIENT_CONTENT' }, 409);
      // Never send credentials, upstream bodies, private question data or stack traces.
      return response({ error: 'The server could not save this operation. Please retry.' }, 503);
    }
  };
}
