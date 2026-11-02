export type GameMode = 'test' | 'rapid' | 'pvp' | 'multiplayer';
export interface SolvedProblem { topic: string; difficulty: string }
export const PROBLEM_XP = { easy: 10, medium: 20, hard: 30, olympiad: 50 } as const;
export const RATING_K = 32;
export const TOPICS = ['integration', 'differentiation', 'limits', 'series', 'differential equations', 'multivariable'] as const;
export const finite = (value: unknown, fallback = 0): number => typeof value === 'number' && Number.isFinite(value) ? value : fallback;
const nonnegative = (value: number) => Math.min(Number.MAX_SAFE_INTEGER, Math.max(0, finite(value)));
export const getLevelFromXp = (xp: number) => Math.floor(Math.sqrt(nonnegative(xp) / 100));
export const getXpForLevel = (level: number) => 100 * Math.floor(nonnegative(level)) ** 2;
export function getXpProgress(xp: number) {
  const level = getLevelFromXp(xp);
  const current = nonnegative(xp) - getXpForLevel(level);
  const max = getXpForLevel(level + 1) - getXpForLevel(level);
  return { current, max, percentage: Math.min(100, current / max * 100) };
}
// XP measures practice; the same problem earns the same credit in every mode.
export function calculateProblemXp(_mode: GameMode, difficulty: string): number {
  const key = typeof difficulty === 'string' ? difficulty.toLowerCase() : '';
  return Object.hasOwn(PROBLEM_XP, key) ? PROBLEM_XP[key as keyof typeof PROBLEM_XP] : 0;
}
export function hasRating(profile?: { rating?: number; ratedGames?: number; wins?: number; losses?: number; draws?: number } | null) {
  return !!profile && (finite(profile.rating) !== 0 || (profile.ratedGames !== undefined ? finite(profile.ratedGames) > 0 : finite(profile.wins) + finite(profile.losses) + finite(profile.draws) > 0));
}
export interface RatingPlayer {
  uid: string;
  rating: number;
  score: number;
  attempted: number;
  correct: number;
  topicRatings?: Record<string, number>;
  answers: Record<string, { correct: boolean }>;
}
export interface Standing { uid: string; rank: number; outcome: 'win' | 'draw' | 'loss' | 'unplayed' }
export function getStandings(players: Pick<RatingPlayer, 'uid' | 'score' | 'attempted'>[]): Standing[] {
  // An inactive player cannot beat someone who participated and took a penalty.
  const compare = (a: typeof players[number], b: typeof players[number]) =>
    Number(b.attempted > 0) - Number(a.attempted > 0) || finite(b.score) - finite(a.score);
  const sorted = [...players].sort((a, b) => compare(a, b) || a.uid.localeCompare(b.uid));
  return sorted.map(p => {
    const rank = 1 + sorted.filter(other => compare(other, p) < 0).length;
    const tied = sorted.filter(other => compare(other, p) === 0).length > 1;
    return { uid: p.uid, rank, outcome: sorted.every(x => x.attempted === 0) ? 'unplayed' : rank > 1 ? 'loss' : tied ? 'draw' : 'win' };
  });
}
interface Pair { a: string; b: string; actual: number; ra: number; rb: number }
function pairChanges(players: RatingPlayer[], pairs: Pair[]) {
  const changes = Object.fromEntries(players.map(p => [p.uid, 0]));
  const degrees: Record<string, number> = {};
  for (const { a, b } of pairs) { degrees[a] = (degrees[a] || 0) + 1; degrees[b] = (degrees[b] || 0) + 1; }
  for (const { a, b, actual, ra, rb } of pairs) {
    const expected = 1 / (1 + 10 ** (Math.max(-4000, Math.min(4000, finite(rb) - finite(ra))) / 400));
    // Symmetric weights preserve the rating pool and bound every player's change by K.
    const delta = RATING_K * (actual - expected) / Math.max(degrees[a], degrees[b]);
    changes[a] += delta;
    changes[b] -= delta;
  }
  return changes;
}
export function calculateRatings(players: RatingPlayer[], questions: { topic: string }[]) {
  const standings = getStandings(players);
  const rank = Object.fromEntries(standings.map(p => [p.uid, p.rank]));
  const pairs: Pair[] = [];
  const topics: Record<string, Pair[]> = {};
  for (let i = 0; i < players.length; i++) for (let j = i + 1; j < players.length; j++) {
    const a = players[i], b = players[j];
    // No evidence of a successful solve: no rating transfer for an idle/all-wrong draw.
    if (a.correct + b.correct > 0) pairs.push({ a: a.uid, b: b.uid, actual: rank[a.uid] < rank[b.uid] ? 1 : rank[a.uid] === rank[b.uid] ? 0.5 : 0, ra: a.rating, rb: b.rating });
    const shared: Record<string, [number, number]> = {};
    questions.forEach((q, index) => {
      const aa = a.answers[index], bb = b.answers[index];
      const topic = q.topic.toLowerCase();
      if (!aa || !bb || !TOPICS.includes(topic as typeof TOPICS[number])) return;
      const scores = shared[topic] ||= [0, 0];
      scores[0] += Number(aa.correct); scores[1] += Number(bb.correct);
    });
    for (const [topic, [sa, sb]] of Object.entries(shared)) {
      if (sa + sb === 0) continue;
      (topics[topic] ||= []).push({ a: a.uid, b: b.uid, actual: sa > sb ? 1 : sa === sb ? 0.5 : 0, ra: finite(a.topicRatings?.[topic]), rb: finite(b.topicRatings?.[topic]) });
    }
  }
  const overall = pairChanges(players, pairs);
  const topicChanges = Object.fromEntries(Object.entries(topics).map(([topic, ps]) => [topic, pairChanges(players, ps)]));
  return Object.fromEntries(players.map(p => [p.uid, {
    ratingChange: overall[p.uid],
    rated: pairs.some(pair => pair.a === p.uid || pair.b === p.uid),
    topicChanges: Object.fromEntries(Object.entries(topicChanges).filter(([topic]) => topics[topic].some(pair => pair.a === p.uid || pair.b === p.uid)).map(([topic, changes]) => [topic, changes[p.uid]])),
    ...standings.find(s => s.uid === p.uid)!,
  }]));
}
