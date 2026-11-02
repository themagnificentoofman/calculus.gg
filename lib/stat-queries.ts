import { execute, field, and, or } from 'firebase/firestore/pipelines';
import type { Firestore } from 'firebase/firestore';
// Enterprise pipelines filter and order before applying limits, so unrated accounts
// cannot push rated players out of the leaderboard and history is actually recent.
export async function loadLeaderboard(db: Firestore) {
  const legacyGames = field('wins').ifAbsent(0).add(field('losses').ifAbsent(0)).add(field('draws').ifAbsent(0));
  const snapshot = await execute(db.pipeline().collection('users_public')
    .where(or(field('rating').ifAbsent(0).notEqual(0), field('ratedGames').ifAbsent(legacyGames).greaterThan(0)))
    .sort(field('rating').descending()).limit(100));
  return snapshot.results.map(row => ({ ...row.data(), id: row.id! }));
}
export async function loadRecentGames(db: Firestore, uid: string) {
  const base = db.pipeline().collection('games')
    .where(and(field('players').arrayContains(uid), field('status').equal('finished')));
  // Legacy games may store ISO strings. Bound each date type on the server, then
  // merge their recent windows chronologically without rewriting historical data.
  const snapshots = await Promise.all(['timestamp', 'string'].map(type => execute(base
    .where(field('createdAt').type().equal(type)).sort(field('createdAt').descending()).limit(50))));
  const rows = snapshots.flatMap(snapshot => snapshot.results.map(row => ({ ...row.data(), id: row.id! }))) as Array<Record<string, any> & { id: string }>;
  const millis = (row: typeof rows[number]) => row.createdAt?.toMillis?.() ?? new Date(row.createdAt).getTime();
  return rows.sort((a, b) => (millis(b) || 0) - (millis(a) || 0)).slice(0, 50);
}

export async function searchPublicProfiles(db: Firestore, uid: string, search: string) {
  const term = search.trim().toLowerCase().slice(0, 99);
  if (!term) return [];
  const snapshot = await execute(db.pipeline().collection('users_public').where(and(
    field('uid').notEqual(uid), or(field('displayName').ifAbsent('').toLower().stringContains(term), field('handle').ifAbsent('').toLower().stringContains(term))
  )).limit(20));
  return snapshot.results.map(row => ({ ...row.data(), uid: row.id! })) as Array<Record<string, any> & { uid: string }>;
}
export async function loadWaitingGames(db: Firestore, uid: string, mode: 'pvp' | 'multiplayer', category?: string, difficulty?: string) {
  let pipeline = db.pipeline().collection('games').where(and(field('mode').equal(mode), field('status').equal('waiting'), field('progressionVersion').equal(3), field('players').arrayContains(uid).not(), field('players').arrayLength().lessThan(mode === 'pvp' ? 2 : 10)));
  if (category) pipeline = pipeline.where(field('category').equal(category));
  if (difficulty) pipeline = pipeline.where(field('difficulty').equal(difficulty));
  const snapshot = await execute(pipeline.limit(10));
  return snapshot.results.map(row => ({ ...row.data(), id: row.id! })) as Array<Record<string, any> & { id: string }>;
}
