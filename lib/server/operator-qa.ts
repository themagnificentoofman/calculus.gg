import { createGameApi } from './game-api.ts';
import { selectBankQuestions, assertBankSetPlayable } from './compact-bank-selection.ts';
import { consumeBankReadQuota, consumeMutationQuota } from './quota.ts';
import type { Store, Data } from './firestore-admin.ts';

export const QA_UIDS = ['cn_m1qa_ed08a3de_0', 'cn_m1qa_ed08a3de_1', 'cn_m1qa_ed08a3de_2'];
const PREFIX = 'cn_m1qa_ed08a3de_';
const COLLECTIONS = ['users', 'users_public', 'questionSets', 'gameSecrets', 'games', 'bankRecent'];
// Every path is isolated at its top-level collection, including transaction
// reads/writes and history queries. This cannot touch ordinary player records.
export function isolatedQaStore(base: Store): Store {
  const path = (value: string) => {
    if (!COLLECTIONS.includes(value.split('/')[0])) throw Error('Unsupported QA collection');
    return PREFIX + value;
  };
  return { get: value => base.get(path(value)),
    find: (collection, filters, limit) => base.find(path(collection), filters, limit),
    transaction: fn => base.transaction(tx => fn({get: value => tx.get(path(value)), set: (value, data) => tx.set(path(value), data), delete: value => tx.delete(path(value))})) };
}
export async function operatorQa(input: Data, db: D1Database, base: Store) {
  const store = isolatedQaStore(base);
  if (input.action === 'cleanup') {
    const paths: string[] = [];
    for (const collection of COLLECTIONS) {
      const rows = await store.find(collection, [], 1000);
      if (rows.length >= 1000) throw Error('QA cleanup bound exceeded');
      for (const row of rows) {
        paths.push(`${collection}/${row.id}`);
        if (collection === 'games') for (const uid of QA_UIDS) paths.push(`games/${row.id}/reviews/${uid}`);
      }
    }
    if (paths.length > 200) throw Error('QA cleanup bound exceeded');
    await store.transaction(async tx => { for (const path of paths) tx.delete(path); });
    await db.batch(QA_UIDS.flatMap(uid => ['mutation:', 'bank-read:'].map(prefix => db.prepare('DELETE FROM ai_quota WHERE key=?').bind(prefix + uid + ':minute'))));
    return {cleanedDocuments: paths.length};
  }
  if (!Number.isInteger(input.actor) || !QA_UIDS[input.actor]) throw Error('Invalid QA actor');
  const uid = QA_UIDS[input.actor];
  if (input.action === 'history') return {history: await store.find('games', [['players', 'ARRAY_CONTAINS', uid], ['status', 'EQUAL', 'finished']], 100)};
  if (input.action === 'snapshot') {
    if (!/^[a-f0-9]{24}$/.test(input.gameId || '')) throw Error('Invalid QA game');
    const game = await store.get('gameSecrets/' + input.gameId);
    if (!game?.players?.includes(uid)) throw Error('QA game membership required');
    return {roundSnapshot: game.roundSnapshot, receipts: game.receipts, status: game.status};
  }
  if (input.action !== 'call' || !['profile', 'questions', 'games'].includes(input.resource)) throw Error('Invalid QA action');
  const api = createGameApi({store, verify: async token => {if (token !== uid) throw Error('Invalid QA identity'); return {sub: uid, name: 'Milestone 1 isolated verification'};},
    select: (request, recent) => selectBankQuestions(db, request, recent), checkPlayable: questions => assertBankSetPlayable(db, questions),
    quota: actor => consumeBankReadQuota(db, actor), mutationQuota: actor => consumeMutationQuota(db, actor)});
  const response = await api(input.resource, new Request('https://calculus.ninja/api/' + input.resource, {method: 'POST', headers: {'Content-Type': 'application/json', Authorization: 'Bearer ' + uid}, body: JSON.stringify(input.body)}));
  return {status: response.status, body: await response.json()};
}
