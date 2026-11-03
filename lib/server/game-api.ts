import { createServerGames, GameError, identifier } from './game-engine.ts';
import { QuestionGenerationError } from './generate-questions.ts';
import { socialAction } from './social.ts';
import { readBoundedJson, validateQuestionRequest, validQuestionResponse } from './questions-policy.mjs';
import type { Store, Data } from './firestore-admin.ts';
import type { GameQuestion } from '../game-progress.ts';
import type { GameMode } from '../progression.ts';
const response = (body: unknown, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
const only = (body: Data, keys: string[]) => { if (!body || typeof body !== 'object' || Array.isArray(body) || Object.keys(body).some(k => !keys.includes(k))) throw new GameError('Unexpected request fields.'); };
const modes = ['test', 'rapid', 'pvp', 'multiplayer'];
export function createGameApi(deps: { store: Store; verify: (token: string) => Promise<Data>; generate: (category: string, difficulty: string, count: number) => Promise<GameQuestion[]>; quota: (uid: string) => Promise<boolean>; mutationQuota?: (uid: string) => Promise<boolean>; now?: () => number }) {
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
        only(body, ['mode', 'category', 'difficulty', 'count']);
        const input = validateQuestionRequest(body);
        if (!input || !modes.includes(body.mode)) throw new GameError('Choose a supported mode, category, difficulty and question count.');
        if (!await deps.quota(uid)) throw new GameError('Question generation limit reached. Please try again later.', 429);
        const questions = await deps.generate(input.category, input.difficulty, input.count);
        if (!validQuestionResponse(questions, input)) throw new GameError('Question generation returned an invalid set. Please retry.', 502);
        return response(await games.storeQuestions(uid, body.mode, input.category, input.difficulty, questions));
      }
      if (resource === 'social') {
        const fields: Record<string, string[]> = { request: ['to'], remove: ['friendId'], invite: ['to', 'gameId'], accept: ['id'], reject: ['id'], cancel: ['id'], invite_accept: ['id'], invite_reject: ['id'] };
        if (typeof body.action !== 'string' || !Object.hasOwn(fields, body.action)) throw new GameError('Unsupported social action.');
        only(body, ['action', ...fields[body.action]]);
        for (const key of fields[body.action]) identifier(body[key]);
        if (body.action === 'invite_accept') return response(await games.acceptInvite(uid, body.id));
        return response(await socialAction(deps.store, uid, body.action, body, deps.now?.()));
      }
      const fields: Record<string, string[]> = { create: ['questionSetId', 'mode', 'options'], join: ['gameId', 'mode'], answer: ['gameId', 'index', 'selectedOption'], start: ['gameId'], leave: ['gameId'], view: ['gameId'], complete: ['gameId'], claim: ['gameId'], chat: ['gameId', 'text'], sync: [] };
      if (typeof body.action !== 'string' || !Object.hasOwn(fields, body.action)) throw new GameError('Unsupported game action.');
      only(body, ['action', ...fields[body.action]]);
      if (body.action === 'sync') { await games.sync(uid); return response({ ok: true }); }
      if (body.action === 'create') {
        if (!modes.includes(body.mode)) throw new GameError('Invalid game mode.');
        only(body.options || {}, ['category', 'difficulty', 'timeLimit', 'settings']);
        return response(await games.createGame(uid, identifier(body.questionSetId), body.mode as GameMode, body.options || {}));
      }
      return response(await games.act(uid, identifier(body.gameId), body.action, body));
    } catch (error) {
      if (error instanceof GameError) return response({ error: error.message }, error.status);
      if (error instanceof QuestionGenerationError) return response({ error: error.kind === 'timeout' ? 'Question generation timed out. Please retry.' : error.kind === 'invalid-output' ? 'The generated questions could not be validated. Please retry.' : 'Question generation is temporarily unavailable. Please retry.' }, error.kind === 'timeout' ? 504 : error.kind === 'invalid-output' ? 502 : 503);
      // Never send credentials, upstream bodies, private question data or stack traces.
      return response({ error: 'The server could not save this operation. Please retry.' }, 503);
    }
  };
}
