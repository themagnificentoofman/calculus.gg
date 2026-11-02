import { calculateProblemXp, calculateRatings, finite, TOPICS, type GameMode } from '../progression.ts';
import { gamePlayers, nextUnanswered, type GameQuestion, type GameSession, type MatchSettings } from '../game-progress.ts';
import type { Store, Transaction, Data } from './firestore-admin.ts';

export class GameError extends Error { status: number; constructor(message: string, status = 400) { super(message); this.status = status; } }
export const identifier = (value: unknown) => { if (typeof value !== 'string' || (!/^[a-zA-Z0-9_-]{5,128}$/.test(value) || ['__proto__', 'constructor', 'prototype'].includes(value))) throw new GameError('Invalid identifier.'); return value; };
const requireMember = (game: GameSession, uid: string) => { if (!game.players.includes(uid)) throw new GameError('You are not a player in this game.', 403); };
const snapshot = (p: Data) => ({ rating: finite(p.rating), topicRatings: Object.fromEntries(TOPICS.map(t => [t, finite(p.topicRatings?.[t])])) });
const competitive = (g: GameSession) => ['pvp', 'multiplayer'].includes(g.mode);
export function publicProfile(profile: Data) {
  const keys = ['uid', 'displayName', 'handle', 'photoURL', 'color', 'lastActive', 'createdAt', 'rating', 'classification', 'gamesPlayed', 'wins', 'losses', 'draws', 'ratedGames', 'xp', 'topicXp', 'topicRatings', 'topicRatedGames'];
  return Object.fromEntries(keys.filter(k => profile[k] !== undefined).map(k => [k, profile[k]]));
}
export function publicGame(game: GameSession) {
  const { questions = [], answers = {}, ratingSnapshot: _snapshots, ...rest } = game;
  return { ...rest, questionCount: questions.length,
    questions: game.status === 'waiting' ? [] : questions.map(({ correctIndex: _key, explanation: _explanation, ...q }) => q),
    answers: Object.fromEntries(Object.entries(answers).map(([uid, values]) => [uid, Object.fromEntries(Object.entries(values).map(([i, { selectedOption: _selection, ...a }]) => [i, a]))])),
  };
}
function ownProgress(game: GameSession, uid: string) {
  const answers = game.answers?.[uid] || {};
  return { answers, reviews: Object.fromEntries(Object.keys(answers).map(index => {
    const q = game.questions![Number(index)]; return [index, { correctIndex: q.correctIndex, explanation: q.explanation }];
  })) };
}
export const playerView = (game: GameSession, uid: string) => ({ game: publicGame(game), progress: ownProgress(game, uid) });
function saveGame(tx: Transaction, id: string, game: GameSession) {
  tx.set(`gameSecrets/${id}`, game); tx.set(`games/${id}`, publicGame(game));
  for (const uid of game.players) tx.set(`games/${id}/reviews/${uid}`, ownProgress(game, uid));
}
function saveProfile(tx: Transaction, uid: string, profile: Data) {
  tx.set(`users/${uid}`, profile); tx.set(`users_public/${uid}`, publicProfile(profile));
}
function patchProfile(profile: Data, patch: Data) {
  const allowed = ['displayName', 'handle', 'photoURL', 'color', 'settings'];
  if (!patch || typeof patch !== 'object' || Array.isArray(patch) || Object.keys(patch).some(k => !allowed.includes(k))) throw new GameError('Only profile preferences can be changed.');
  for (const [k, v] of Object.entries(patch)) {
    if (k === 'settings') {
      if (!v || Array.isArray(v) || typeof v !== 'object' || Object.keys(v).some(key => !['theme', 'notifications', 'soundEnabled'].includes(key)) ||
        ('theme' in v && !['dark', 'light', 'system'].includes(v.theme)) || ['notifications', 'soundEnabled'].some(key => key in v && typeof v[key] !== 'boolean')) throw new GameError('Invalid settings.');
      profile.settings = { ...profile.settings, ...v }; continue;
    }
    if (typeof v !== 'string' || v.length > (k === 'photoURL' ? 300000 : k === 'displayName' ? 99 : 32)) throw new GameError('Invalid profile field.');
    if (k === 'handle' && !/^[a-zA-Z0-9_]{3,32}$/.test(v)) throw new GameError('Handles must use 3–32 letters, numbers or underscores.');
    if (k === 'color' && !/^#[0-9a-fA-F]{6}$/.test(v)) throw new GameError('Invalid player color.');
    if (k === 'photoURL' && v && !/^https:\/\//.test(v) && !/^data:image\/(png|jpeg|webp);base64,[a-zA-Z0-9+/=]+$/.test(v)) throw new GameError('Invalid profile image.');
    profile[k] = v;
  }
}
function settingsFor(mode: GameMode, input: Data): { timeLimit?: number; settings?: MatchSettings } {
  const integer = (n: unknown, min: number, max: number) => typeof n === 'number' && Number.isInteger(n) && n >= min && n <= max;
  if (mode === 'rapid') { if (!integer(input.timeLimit, 30, 300)) throw new GameError('Choose a 30–300 second time limit.'); return { timeLimit: input.timeLimit }; }
  if (mode === 'multiplayer') {
    const s = input.settings;
    if (!s || typeof s !== 'object' || Array.isArray(s) || Object.keys(s).some(k => !['winCondition', 'targetScore', 'timeLimit', 'penalties'].includes(k)) || !['first_to_n', 'time_limit'].includes(s.winCondition) || !integer(s.targetScore, 1, 20) || !integer(s.timeLimit, 30, 300) || typeof s.penalties !== 'boolean') throw new GameError('Invalid multiplayer settings.');
    return { settings: { winCondition: s.winCondition, targetScore: s.targetScore, timeLimit: s.timeLimit, penalties: s.penalties } };
  }
  return {};
}
export function createServerGames(store: Store, now: () => number = Date.now) {
  async function profile(uid: string, claims: Data, patch: Data = {}) {
    return store.transaction(async tx => {
      const existing = await tx.get(`users/${uid}`);
      const p = existing || { uid, displayName: typeof claims.name === 'string' ? claims.name.slice(0, 99) : 'Anonymous Calc Bro', handle: `user${uid.slice(0, 6)}`, photoURL: typeof claims.picture === 'string' ? claims.picture : '', email: typeof claims.email === 'string' ? claims.email : '',
        rating: 0, classification: 'Novice', gamesPlayed: 0, wins: 0, losses: 0, draws: 0, ratedGames: 0, answeredQuestions: 0, correctAnswers: 0, xp: 0, topicXp: {}, topicRatings: {}, topicRatedGames: {}, friends: [], settings: { theme: 'dark', notifications: true, soundEnabled: true }, createdAt: new Date(now()) };
      p.uid = uid; patchProfile(p, patch); p.lastActive = now(); saveProfile(tx, uid, p); return p;
    });
  }
  async function storeQuestions(uid: string, mode: GameMode, category: string, difficulty: string, questions: GameQuestion[]) {
    const id = crypto.randomUUID().replaceAll('-', '').slice(0, 24);
    await store.transaction(async tx => { await tx.get(`questionSets/${id}`); tx.set(`questionSets/${id}`, { uid, mode, category, difficulty, questions, expiresAt: new Date(now() + 30 * 60_000) }); });
    return { questionSetId: id, questionCount: questions.length };
  }
  async function createGame(uid: string, id: string, mode: GameMode, input: Data) {
    identifier(id); await sync(uid);
    return store.transaction(async tx => {
      const [set, existing, p] = await Promise.all([tx.get(`questionSets/${id}`), tx.get(`gameSecrets/${id}`), tx.get(`users/${uid}`)]);
      if (!set || set.uid !== uid || set.mode !== mode) throw new GameError('This question set does not belong to this game.', 403);
      if (existing) { requireMember(existing as GameSession, uid); return { id, ...playerView(existing as GameSession, uid) }; }
      if (!p || set.used || new Date(set.expiresAt).getTime() <= now()) throw new GameError('This question set has expired. Please start again.');
      const configuration = settingsFor(mode, input), solo = mode === 'test' || mode === 'rapid', startTime = now() + (mode === 'rapid' ? 3000 : 0);
      const game: GameSession = { mode, status: solo ? 'active' : 'waiting', progressionVersion: 3, players: [uid], scores: { [uid]: 0 }, questions: set.questions, category: set.category, difficulty: set.difficulty,
        answers: {}, completedPlayers: [], pendingClaims: [], receipts: {}, ratingSnapshot: { [uid]: snapshot(p) }, createdAt: new Date(now()),
        ...(configuration.settings ? { settings: configuration.settings } : {}), ...(solo ? { startTime } : {}), ...(mode === 'rapid' ? { deadline: startTime + configuration.timeLimit! * 1000 } : {}) };
      const { questions: _questions, ...metadata } = set;
      tx.set(`questionSets/${id}`, { ...metadata, used: true }); saveGame(tx, id, game);
      return { id, ...playerView(game, uid) };
    });
  }
  // Every transition reads authoritative state, identities and clocks on the server.
  // Score, XP and all result receipts commit together with the accepted answer.
  async function act(uid: string, id: string, action: string, input: Data = {}) {
    identifier(id);
    return store.transaction(async tx => {
      const raw = await tx.get(`gameSecrets/${id}`);
      if (!raw || raw.progressionVersion !== 3) throw new GameError('This game uses an older version. Please create a new game.', 409);
      const game = raw as GameSession;
      const joining = action === 'join' && !game.players.includes(uid);
      if (!joining) requireMember(game, uid);
      const ids = [...new Set([...game.players, ...(joining ? [uid] : [])])];
      const docs = await Promise.all(ids.map(p => tx.get(`users/${p}`)));
      if (docs.some(p => !p)) throw new GameError('A player profile is unavailable.', 409);
      const profiles = Object.fromEntries(ids.map((p, i) => [p, docs[i]!]));
      const changed = new Set<string>();
      const time = now();
      let modified = false, duplicate = false, answer: any = null;
      if (action === 'join') {
        if (input.mode !== game.mode || !competitive(game)) throw new GameError('This game belongs to a different mode.');
        if (joining) {
          if (game.status !== 'waiting' || game.players.length >= (game.mode === 'pvp' ? 2 : 10)) throw new GameError('Game is full or already started.', 409);
          game.players.push(uid); game.scores[uid] = 0; modified = true;
          if (game.mode === 'pvp') { game.status = 'active'; game.startTime = time + 3000; game.deadline = game.startTime + 30 * 60_000; }
          game.ratingSnapshot = Object.fromEntries(game.players.map(p => [p, snapshot(profiles[p])]));
        }
      } else if (action === 'start') {
        if (game.players[0] !== uid || game.mode !== 'multiplayer') throw new GameError('Only the host can start this game.', 403);
        if (game.status === 'waiting') {
          if (game.players.length < 2) throw new GameError('At least two players are required.');
          game.status = 'active'; game.startTime = time; game.deadline = time + (game.settings?.winCondition === 'time_limit' ? game.settings.timeLimit * 1000 : 30 * 60_000);
          game.ratingSnapshot = Object.fromEntries(game.players.map(p => [p, snapshot(profiles[p])])); modified = true;
        }
      } else if (action === 'answer') {
        const { index, selectedOption } = input;
        if (!Number.isInteger(index) || index < 0 || !Number.isInteger(selectedOption) || selectedOption < 0 || selectedOption > 3) throw new GameError('Select a valid answer.');
        answer = game.answers?.[uid]?.[index];
        if (answer) { duplicate = true; }
        else if (game.status !== 'active') throw new GameError('This game has ended.', 409);
        else if (time < game.startTime!) throw new GameError('The game has not started yet.', 409);
        else if (!game.deadline || time < game.deadline) {
          if (index !== nextUnanswered(game, uid)) throw new GameError('Please answer the current question.', 409);
          const q = game.questions?.[index]; if (!q) throw new GameError('Question not found.');
          const correct = selectedOption === q.correctIndex, xp = correct ? calculateProblemXp(game.mode, q.difficulty) : 0;
          answer = { selectedOption, correct, xp, timeMs: time - game.startTime! };
          (game.answers![uid] ||= {})[index] = answer;
          game.scores[uid] = finite(game.scores[uid]) + (correct ? 1 : game.mode === 'multiplayer' && game.settings?.penalties ? -1 : 0);
          if (nextUnanswered(game, uid) === game.questions!.length) game.completedPlayers = [...new Set([...game.completedPlayers!, uid])];
          if (game.mode === 'rapid' && !correct) game.deadline! -= 5000;
          const p = profiles[uid], topicXp = { ...p.topicXp };
          topicXp[q.topic] = finite(topicXp[q.topic]) + xp;
          Object.assign(p, { xp: finite(p.xp) + xp, topicXp, answeredQuestions: finite(p.answeredQuestions) + 1, correctAnswers: finite(p.correctAnswers) + Number(correct) });
          changed.add(uid); modified = true;
          if (correct) { game.timeline ||= {}; (game.timeline[uid] ||= []).push({ questionIndex: index, timeMs: answer.timeMs }); }
        }
      } else if (action === 'chat') {
        if (typeof input.text !== 'string') throw new GameError('Send a text message.');
        const text = input.text.trim();
        if (typeof text !== 'string' || !text || text.length > 100) throw new GameError('Messages must contain 1–100 characters.');
        const last = [...(game.messages || [])].reverse().find(m => m.senderId === uid);
        if (last && time - last.timestamp < 750) throw new GameError('Please wait before sending another message.', 429);
        game.messages = [...(game.messages || []).slice(-99), { senderId: uid, senderName: profiles[uid].displayName || 'Player', text, timestamp: time }]; modified = true;
      } else if (!['view', 'complete', 'claim'].includes(action)) throw new GameError('Unsupported game action.');
      const target = game.mode === 'multiplayer' && game.settings?.winCondition === 'first_to_n' && Object.values(game.scores).some(s => s >= game.settings!.targetScore);
      if (game.status === 'active' && (target || game.players.every(p => nextUnanswered(game, p) === game.questions!.length) || (game.deadline && time >= game.deadline))) {
        game.status = 'finished'; game.finishedAt = time; game.pendingClaims = []; modified = true;
        const players = gamePlayers(game), counted = players.some(p => p.attempted > 0), ranked = competitive(game) && players.length > 1;
        const ratings = ranked ? calculateRatings(players, game.questions!) : {};
        for (const p of game.players) {
          const result = ratings[p] || { ratingChange: 0, topicChanges: {}, rated: false, rank: 1, outcome: 'completed' };
          const profile = profiles[p], newRating = finite(profile.rating) + result.ratingChange;
          game.receipts![p] = { ...result, newRating, counted };
          if (!counted) continue;
          const topicRatings = { ...profile.topicRatings }, topicRatedGames = { ...profile.topicRatedGames };
          for (const [topic, delta] of Object.entries(result.topicChanges)) { topicRatings[topic] = finite(topicRatings[topic]) + delta; topicRatedGames[topic] = finite(topicRatedGames[topic]) + 1; }
          Object.assign(profile, { gamesPlayed: finite(profile.gamesPlayed) + 1, rating: newRating, topicRatings, topicRatedGames,
            wins: finite(profile.wins) + Number(ranked && result.outcome === 'win'), losses: finite(profile.losses) + Number(ranked && result.outcome === 'loss'), draws: finite(profile.draws) + Number(ranked && result.outcome === 'draw'),
            ratedGames: finite(profile.ratedGames, finite(profile.wins) + finite(profile.losses) + finite(profile.draws)) + Number(result.rated) });
          changed.add(p);
        }
      }
      if (action === 'claim' && game.status !== 'finished') throw new GameError('This game is still in progress.', 409);
      for (const p of changed) saveProfile(tx, p, profiles[p]);
      if (modified) saveGame(tx, id, game);
      return { ...playerView(game, uid), answer: answer || null, duplicate, receipt: game.receipts?.[uid] || null, serverNow: time };
    });
  }
  async function sync(uid: string) {
    const active = await store.find('gameSecrets', [['players', 'ARRAY_CONTAINS', uid], ['status', 'EQUAL', 'active'], ['deadline', 'LESS_THAN_OR_EQUAL', now()]], 25);
    for (const g of active) if (g.data.deadline && g.data.deadline <= now()) await act(uid, g.id, 'complete');
  }
  return { profile, storeQuestions, createGame, act, sync };
}
