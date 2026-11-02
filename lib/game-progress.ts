import { collection, doc, getDocs, onSnapshot, query, runTransaction, serverTimestamp, where, type Firestore } from 'firebase/firestore';
import { calculateProblemXp, calculateRatings, finite, getStandings, TOPICS, type GameMode } from './progression.ts';

export interface GameQuestion { latexProblem: string; options: string[]; correctIndex: number; explanation: string | string[]; topic: string; difficulty: string }
export interface SavedAnswer { selectedOption: number; correct: boolean; xp: number; timeMs: number }
export interface MatchSettings { category?: string; difficulty?: string; winCondition: 'first_to_n' | 'time_limit'; targetScore: number; timeLimit: number; penalties: boolean }
export interface ResultReceipt { ratingChange: number; newRating: number; topicChanges: Record<string, number>; outcome: string; rank: number; rated: boolean; counted: boolean; legacy?: boolean }
export interface GameSession {
  mode: GameMode; status: 'waiting' | 'active' | 'finished'; players: string[]; scores: Record<string, number>;
  questions?: GameQuestion[]; category?: string; difficulty?: string; settings?: MatchSettings;
  startTime?: number; deadline?: number; finishedAt?: number; createdAt?: unknown;
  progressionVersion?: number; answers?: Record<string, Record<string, SavedAnswer>>;
  ratingSnapshot?: Record<string, { rating: number; topicRatings: Record<string, number> }>;
  completedPlayers?: string[]; pendingClaims?: string[]; receipts?: Record<string, ResultReceipt>;
  timeline?: Record<string, { questionIndex: number; timeMs: number }[]>;
  messages?: { senderId: string; senderName: string; text: string; timestamp: number }[]; winner?: string;
}
export function gamePlayers(game: GameSession) {
  return game.players.map(uid => {
    const answers = game.answers?.[uid] || {};
    return { uid, score: finite(game.scores[uid]), attempted: game.progressionVersion === 2 ? Object.keys(answers).length : 1,
      correct: Object.values(answers).filter(a => a.correct).length, answers,
      rating: finite(game.ratingSnapshot?.[uid]?.rating), topicRatings: game.ratingSnapshot?.[uid]?.topicRatings || {} };
  });
}
export const gameStandings = (game: GameSession) => getStandings(gamePlayers(game));
export const isCompetitive = (game: GameSession) => game.mode === 'pvp' || game.mode === 'multiplayer';
export const nextUnanswered = (game: GameSession, uid: string) => {
  const index = (game.questions || []).findIndex((_, i) => !game.answers?.[uid]?.[i]);
  return index === -1 ? (game.questions || []).length : index;
};
const ended = (game: GameSession, now: number) => ({ status: 'finished' as const, finishedAt: now, pendingClaims: game.players });
const profileSnapshot = (data: Record<string, any>) => ({ rating: finite(data.rating), topicRatings: Object.fromEntries(TOPICS.map(topic => [topic, finite(data.topicRatings?.[topic])])) });
const requireMember = (game: GameSession, uid: string) => {
  if (!game.players.includes(uid)) throw new Error('You are not a player in this game.');
};
const requireCurrent = (game: GameSession) => {
  if (game.progressionVersion !== 2) throw new Error('This lobby uses an older scoring version. Please create a new game.');
};

// Core operations and real-time listeners are required for live game/profile synchronization.
// All transaction callbacks are retry-safe: no sounds, React updates, or other side effects.
export function createGameProgress(db: Firestore, now: () => number = Date.now) {
  const gameRef = (id: string) => doc(db, 'games', id);
  const userRef = (uid: string) => doc(db, 'users', uid);
  async function claimResult(id: string, uid: string): Promise<ResultReceipt> {
    return runTransaction(db, async tx => {
      const [gs, ps] = await Promise.all([tx.get(gameRef(id)), tx.get(userRef(uid))]);
      if (!gs.exists() || !ps.exists()) throw new Error('Could not find the game or your profile.');
      const game = gs.data() as GameSession;
      requireMember(game, uid);
      if (game.status !== 'finished') throw new Error('This game is still in progress.');
      if (game.receipts?.[uid]) return game.receipts[uid];
      if (game.progressionVersion !== 2) return { ratingChange: 0, newRating: finite(ps.data().rating), topicChanges: {}, outcome: 'historical', rank: 0, rated: false, counted: false, legacy: true };
      const players = gamePlayers(game);
      const counted = players.some(p => p.attempted > 0);
      const competitive = isCompetitive(game) && players.length > 1;
      const result = competitive ? calculateRatings(players, game.questions || [])[uid] : { ratingChange: 0, topicChanges: {}, rated: false, rank: 1, outcome: 'completed' };
      const profile = ps.data();
      const receipt: ResultReceipt = { ...result, newRating: finite(profile.rating) + result.ratingChange, counted };
      if (counted) {
        const topicRatings = { ...profile.topicRatings };
        const topicRatedGames = { ...profile.topicRatedGames };
        for (const [topic, change] of Object.entries(result.topicChanges)) {
          topicRatings[topic] = finite(topicRatings[topic]) + change;
          topicRatedGames[topic] = finite(topicRatedGames[topic]) + 1;
        }
        tx.update(userRef(uid), {
          gamesPlayed: finite(profile.gamesPlayed) + 1,
          wins: finite(profile.wins) + Number(competitive && result.outcome === 'win'),
          losses: finite(profile.losses) + Number(competitive && result.outcome === 'loss'),
          draws: finite(profile.draws) + Number(competitive && result.outcome === 'draw'),
          ratedGames: finite(profile.ratedGames, finite(profile.wins) + finite(profile.losses) + finite(profile.draws)) + Number(result.rated),
          rating: receipt.newRating, topicRatings, topicRatedGames,
        });
      }
      tx.update(gameRef(id), { [`receipts.${uid}`]: receipt, pendingClaims: (game.pendingClaims || []).filter(p => p !== uid) });
      return receipt;
    });
  }
  const pendingQuery = (uid: string) => query(collection(db, 'games'), where('pendingClaims', 'array-contains', uid));
  const activeQuery = (uid: string) => query(collection(db, 'games'), where('players', 'array-contains', uid), where('status', '==', 'active'));
  async function syncPendingResults(uid: string) {
    const active = await getDocs(activeQuery(uid));
    for (const game of active.docs) {
      const data = game.data();
      if (data.progressionVersion === 2 && data.deadline && data.deadline <= now()) await completeGame(game.id, uid);
    }
    const pending = await getDocs(pendingQuery(uid));
    for (const game of pending.docs) await claimResult(game.id, uid);
  }
  function watchPendingResults(uid: string, onError: (error: unknown) => void) {
    let stopped = false;
    let pending = new Set<string>();
    const claiming = new Set<string>();
    const retries = new Map<string, ReturnType<typeof setTimeout>>();
    const claim = (id: string) => {
      if (stopped || !pending.has(id) || claiming.has(id)) return;
      claiming.add(id);
      claimResult(id, uid).catch(error => {
        onError(error);
        if (!stopped && pending.has(id)) retries.set(id, setTimeout(() => { retries.delete(id); claim(id); }, 5000));
      }).finally(() => claiming.delete(id));
    };
    const stopClaims = onSnapshot(pendingQuery(uid), snapshot => {
      pending = new Set(snapshot.docs.map(game => game.id));
      for (const [id, timer] of retries) if (!pending.has(id)) { clearTimeout(timer); retries.delete(id); }
      for (const id of pending) if (!retries.has(id)) claim(id);
    }, onError);
    // Deadlines remain active on the dashboard and are reconciled after reconnecting.
    const timers = new Map<string, { deadline: number; timer: ReturnType<typeof setTimeout> }>();
    const finish = (id: string) => {
      if (stopped || !timers.has(id)) return;
      completeGame(id, uid).catch(error => {
        onError(error);
        const entry = timers.get(id);
        if (!stopped && entry) entry.timer = setTimeout(() => finish(id), 5000);
      });
    };
    const stopActive = onSnapshot(activeQuery(uid), snapshot => {
      const present = new Set(snapshot.docs.map(game => game.id));
      for (const [id, entry] of timers) if (!present.has(id)) { clearTimeout(entry.timer); timers.delete(id); }
      for (const game of snapshot.docs) {
        const data = game.data();
        if (data.progressionVersion !== 2 || !data.deadline || timers.get(game.id)?.deadline === data.deadline) continue;
        const old = timers.get(game.id); if (old) clearTimeout(old.timer);
        timers.set(game.id, { deadline: data.deadline, timer: setTimeout(() => finish(game.id), Math.max(0, data.deadline - now()) + 20) });
      }
    }, onError);
    return () => {
      stopped = true; stopClaims(); stopActive();
      for (const timer of retries.values()) clearTimeout(timer);
      for (const entry of timers.values()) clearTimeout(entry.timer);
    };
  }
  async function createGame(uid: string, mode: GameMode, questions: GameQuestion[], options: { category: string; difficulty: string; settings?: MatchSettings; timeLimit?: number }) {
    if (!questions.length) throw new Error('No questions were generated.');
    await syncPendingResults(uid);
    const ref = doc(collection(db, 'games'));
    await runTransaction(db, async tx => {
      const ps = await tx.get(userRef(uid));
      if (!ps.exists()) throw new Error('Your profile is still loading. Please try again.');
      const solo = mode === 'test' || mode === 'rapid';
      const startTime = now() + (mode === 'rapid' ? 3000 : 0);
      tx.set(ref, {
        mode, status: solo ? 'active' : 'waiting', progressionVersion: 2, players: [uid], scores: { [uid]: 0 },
        questions, category: options.category, difficulty: options.difficulty, ...(options.settings ? { settings: options.settings } : {}),
        answers: {}, completedPlayers: [], receipts: {}, pendingClaims: [], ratingSnapshot: { [uid]: profileSnapshot(ps.data()) },
        ...(solo ? { startTime } : {}), ...(mode === 'rapid' ? { deadline: startTime + (options.timeLimit || 60) * 1000 } : {}),
        createdAt: serverTimestamp(),
      });
    });
    return ref.id;
  }
  async function joinGame(id: string, uid: string, mode: 'pvp' | 'multiplayer') {
    await syncPendingResults(uid);
    await runTransaction(db, async tx => {
      const gs = await tx.get(gameRef(id));
      if (!gs.exists()) throw new Error('Game not found.');
      const game = gs.data() as GameSession;
      if (game.mode !== mode) throw new Error('This game belongs to a different mode.');
      if (game.players.includes(uid) && game.status === 'finished') return;
      requireCurrent(game);
      if (game.players.includes(uid)) return;
      if (game.status !== 'waiting' || game.players.length >= (mode === 'pvp' ? 2 : 10)) throw new Error('Game is full or already started.');
      const players = [...game.players, uid];
      const profiles = await Promise.all(players.map(p => tx.get(userRef(p))));
      if (profiles.some(p => !p.exists())) throw new Error('A player profile is unavailable. Please retry.');
      const ratingSnapshot = Object.fromEntries(players.map((p, i) => [p, profileSnapshot(profiles[i].data()!)]));
      const startTime = now() + 3000;
      tx.update(gameRef(id), { players, [`scores.${uid}`]: 0, ratingSnapshot,
        ...(mode === 'pvp' ? { status: 'active', startTime, deadline: startTime + 30 * 60_000 } : {}) });
    });
  }
  async function startGame(id: string, uid: string) {
    await syncPendingResults(uid);
    await runTransaction(db, async tx => {
      const gs = await tx.get(gameRef(id));
      if (!gs.exists()) throw new Error('Game not found.');
      const game = gs.data() as GameSession;
      requireCurrent(game); requireMember(game, uid);
      if (game.status !== 'waiting') return;
      if (game.players[0] !== uid || game.players.length < 2) throw new Error('The host can start once at least two players join.');
      const profiles = await Promise.all(game.players.map(p => tx.get(userRef(p))));
      if (profiles.some(p => !p.exists())) throw new Error('A player profile is unavailable.');
      const ratingSnapshot = Object.fromEntries(game.players.map((p, i) => [p, profileSnapshot(profiles[i].data()!)]));
      const startTime = now();
      tx.update(gameRef(id), { status: 'active', startTime, ratingSnapshot,
        deadline: startTime + (game.settings?.winCondition === 'time_limit' ? game.settings.timeLimit * 1000 : 30 * 60_000) });
    });
  }
  async function submitAnswer(id: string, uid: string, index: number, selectedOption: number) {
    return runTransaction(db, async tx => {
      const [gs, ps] = await Promise.all([tx.get(gameRef(id)), tx.get(userRef(uid))]);
      if (!gs.exists() || !ps.exists()) throw new Error('Could not find the game or your profile.');
      const game = gs.data() as GameSession;
      requireCurrent(game); requireMember(game, uid);
      const existing = game.answers?.[uid]?.[index];
      if (existing) return { answer: existing, game, duplicate: true };
      const time = now();
      if (game.status !== 'active') throw new Error('This game has ended.');
      if (time < (game.startTime || 0)) throw new Error('The game has not started yet.');
      if (game.deadline && time >= game.deadline) {
        tx.update(gameRef(id), ended(game, time));
        return { answer: null, game: { ...game, ...ended(game, time) }, duplicate: false };
      }
      const questions = game.questions || [], q = questions[index];
      if (!q || !Number.isInteger(index) || index !== nextUnanswered(game, uid) || !Number.isInteger(selectedOption) || selectedOption < 0 || selectedOption >= q.options.length) throw new Error('Please answer the current question.');
      const correct = selectedOption === q.correctIndex;
      const xp = correct ? calculateProblemXp(game.mode, q.difficulty) : 0;
      const answer: SavedAnswer = { selectedOption, correct, xp, timeMs: time - (game.startTime || time) };
      const ownAnswers = { ...game.answers?.[uid], [index]: answer };
      const scores = { ...game.scores, [uid]: finite(game.scores[uid]) + (correct ? 1 : game.mode === 'multiplayer' && game.settings?.penalties ? -1 : 0) };
      const completedPlayers = [...new Set([...(game.completedPlayers || []), ...(Object.keys(ownAnswers).length === questions.length ? [uid] : [])])];
      const deadline = game.deadline ? game.deadline - (game.mode === 'rapid' && !correct ? 5000 : 0) : undefined;
      let next: GameSession = { ...game, answers: { ...game.answers, [uid]: ownAnswers }, scores, completedPlayers, ...(deadline ? { deadline } : {}) };
      const reachedTarget = game.mode === 'multiplayer' && game.settings?.winCondition === 'first_to_n' && scores[uid] >= game.settings.targetScore;
      if (reachedTarget || game.players.every(p => completedPlayers.includes(p)) || (deadline && deadline <= time)) next = { ...next, ...ended(game, time) };
      const profile = ps.data();
      const topicXp = { ...profile.topicXp };
      const topic = q.topic.toLowerCase();
      if (TOPICS.includes(topic as typeof TOPICS[number])) topicXp[topic] = finite(topicXp[topic]) + xp;
      tx.update(userRef(uid), { xp: finite(profile.xp) + xp, topicXp,
        answeredQuestions: finite(profile.answeredQuestions) + 1, correctAnswers: finite(profile.correctAnswers) + Number(correct) });
      const timeline = { ...game.timeline };
      if (correct) timeline[uid] = [...(timeline[uid] || []), { questionIndex: index, timeMs: answer.timeMs }];
      tx.update(gameRef(id), { answers: next.answers, scores, completedPlayers, timeline,
        ...(deadline ? { deadline } : {}), ...(next.status === 'finished' ? ended(game, time) : {}) });
      return { answer, game: next, duplicate: false };
    });
  }
  async function completeGame(id: string, uid: string) {
    await runTransaction(db, async tx => {
      const gs = await tx.get(gameRef(id));
      if (!gs.exists()) throw new Error('Game not found.');
      const game = gs.data() as GameSession;
      requireCurrent(game); requireMember(game, uid);
      if (game.status === 'finished') return;
      if (game.status !== 'active') throw new Error('This game has not started.');
      if (game.deadline && now() >= game.deadline || game.players.every(p => nextUnanswered(game, p) === game.questions?.length)) tx.update(gameRef(id), ended(game, now()));
    });
  }
  return { createGame, joinGame, startGame, submitAnswer, completeGame, claimResult, syncPendingResults, watchPendingResults };
}
